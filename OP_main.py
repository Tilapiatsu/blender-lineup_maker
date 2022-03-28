import bpy
import os, time, math, subprocess, json, tempfile, re
from datetime import date
from fpdf import FPDF
from os import path
from . import variables as V
from . import properties as P
from . import helper as H
from . import asset_format as A
from . import naming_convention as N
from . import compositing as C
from . import stats as S
from . import logger as L


class LM_OP_UpdateLineup(bpy.types.Operator):
	bl_idname = "scene.lm_update_lineup"
	bl_label = "Lineup Maker: Import/Update asset, then render, then composite, then export PDF"
	bl_options = {'REGISTER', 'UNDO'}

	imported = False
	rendered = False
	composited = False
	exported = False
	done = False

	def register_render_handler(self):
		self._timer = bpy.context.window_manager.event_timer_add(0.5, window=bpy.context.window)

	def unregister_render_handler(self):
		bpy.context.window_manager.event_timer_remove(self._timer)
	

	def execute(self, context):
		self.imported = False
		self.rendered = False
		self.composited = False
		self.exported = False
		self.done = False

		self.register_render_handler()
		bpy.context.window_manager.modal_handler_add(self)
		
		return {"RUNNING_MODAL"}
	
	def modal(self, context, event):
		if event.type == 'TIMER':
			if not self.imported:
				bpy.ops.scene.lm_create_blend_catalog_file()
				self.imported = True
			
			elif not self.rendered:
				bpy.ops.scene.lm_renderassets()
				self.rendered = True
			
			elif not self.composited:
				bpy.ops.scene.lm_compositerenders()
				self.composited = True

			elif not self.exported:
				bpy.ops.scene.lm_export_pdf()
				self.exported = True
			
			else:
				self.report({'INFO'}, 'Lineup Maker : Lineup Updated correctly')
				return {"FINISHED"}

		return {"PASS_THROUGH"}

class LM_OP_CreateBlendCatalogFile(bpy.types.Operator):
	bl_idname = "scene.lm_create_blend_catalog_file"
	bl_label = "Lineup Maker: Create Blend Catalog File"
	bl_options = {'REGISTER'}

	
	mode : bpy.props.EnumProperty(items=[("ASSET", "Asset", ""), ("QUEUE", "Queue", ""), ("ALL", "All", ""), ("IMPORT", "Import", ""), ("IMPORT_NEW", "Import New", "")])
	asset_name : bpy.props.StringProperty(name="Asset Name", default='', description='Name of the asset to export')

	folder_src = ''
	asset_collection = ''
	asset_view_layers = {}
	import_list = []
	view_layer_list = []
	updated_assets = []
	updated_view_layers = []
	log = None
	_timer = None
	stopped = None
	importing_asset = None
	updating_viewlayers = None
	cancelling = False
	percent = 0
	total_assets = 0
	updated_assets_number = 0
	skipped_asset_number = 0
	autosave_step = 1

	@classmethod
	def poll(cls, context):
		return context.scene.lm_render_collection and path.isdir(context.scene.lm_asset_path)

	def execute(self, context):
		self.log = L.LoggerProgress(context='IMPORT_ASSETS')
		self.tmpdir = tempfile.mkdtemp()
		self.preset_path = os.path.join(self.tmpdir, "temp_preset.json")
		bpy.ops.save_preset('INVOKE_DEFAULT', filepath=self.preset_path)

		# Init the scene and store the right variables
		self.folder_src = bpy.path.abspath(context.scene.lm_asset_path)

		if not path.isdir(self.folder_src):
			self.log.error('The asset path is not valid : \n{} '.format(self.folder_src))
			self.report({'ERROR	'}, 'Lineup Maker : The asset path is not valid')
			return {'FINISHED'}

		H.set_active_collection(context, bpy.context.scene.collection.name)
		if context.scene.lm_asset_collection is None:
			self.asset_collection, _ = H.create_asset_collection(context, V.LM_ASSET_COLLECTION)
		else:
			self.asset_collection = context.scene.lm_asset_collection
		H.set_active_collection(context, self.asset_collection.name)
		
		
		# Store the Global View_Layer
		if context.scene.lm_initial_view_layer  == '':
			context.scene.lm_initial_view_layer = context.window.view_layer.name
		else:
			context.window.view_layer = context.scene.view_layers[context.scene.lm_initial_view_layer]

		# Disable the Global View Layer
		context.scene.view_layers[context.scene.lm_initial_view_layer].use = False

		# feed asset view layer with existing one
		for a in context.scene.lm_asset_list:
			self.asset_view_layers[a.view_layer] = H.get_layer_collection(context.view_layer.layer_collection, a.name)

		# if asset_name has been defined - Import one specific asset
		if self.mode == "ASSET":
			if len(self.asset_name):
				asset_path = path.join(self.folder_src, self.asset_name)

				if not path.isdir(asset_path):
					self.log.warning('Asset {} doesn\'t exist in the asset folder {}'.format(self.asset_name, self.folder_src))
					self.report({'INFO'}, 'Lineup Maker : Import cancelled, Asset {} doesn\'t exist in the asset folder {}'.format(self.asset_name, self.folder_src))

					return {'FINISHED'}

				self.import_list = [asset_path]

				H.remove_asset(context, self.asset_name)

		# If asset_name has NOT been defined - scan all subfolders and import only the new necessary one
		elif self.mode == "ALL":
			self.import_list = [path.join(self.folder_src, f,) for f in os.listdir(self.folder_src) if path.isdir(os.path.join(self.folder_src, f))]
		
		elif self.mode == "QUEUE":
			queue_asset_name = [a.name for a in context.scene.lm_render_queue if a.checked]
			self.import_list = [path.join(self.folder_src, f,) for f in os.listdir(self.folder_src) if path.isdir(os.path.join(self.folder_src, f)) and path.basename(os.path.join(self.folder_src, f)) in queue_asset_name]
		
		elif self.mode == "IMPORT":
			import_asset_name = [a.name for a in context.scene.lm_import_list if a.checked]
			self.import_list = [path.join(self.folder_src, f,) for f in os.listdir(self.folder_src) if path.isdir(os.path.join(self.folder_src, f)) and path.basename(os.path.join(self.folder_src, f)) in import_asset_name]
		
		elif self.mode == "IMPORT_NEW":
			import_asset_name = [a.name for a in context.scene.lm_import_list if a.checked and not a.is_imported]
			self.import_list = [path.join(self.folder_src, f,) for f in os.listdir(self.folder_src) if path.isdir(os.path.join(self.folder_src, f)) and path.basename(os.path.join(self.folder_src, f)) in import_asset_name]

		self.total_assets = len(self.import_list)

		H.switch_shadingtype(context, 'SOLID')

		self._timer = bpy.context.window_manager.event_timer_add(0.01, window=bpy.context.window)
		bpy.context.window_manager.modal_handler_add(self)

		return {"RUNNING_MODAL"}

	def modal(self, context, event):
		if event.type == 'ESC':
			self.cancelling = True

		if event.type == 'TIMER':
			# stopped
			if self.stopped:
				bpy.context.window_manager.event_timer_remove(self._timer)
				return {'FINISHED'}

			# importing in progress
			elif self.importing_asset is not None or self.updating_viewlayers is not None:
				return{'PASS_THROUGH'}
			
			# importing current file done -> switch to next file
			elif not self.cancelling and self.importing_asset is None and len(self.import_list):
				self.importing_asset = self.import_list.pop()
				self.importing(context, self.importing_asset)
			
			# import not started -> init import
			elif (self.importing_asset is None or self.cancelling) and len(self.import_list) == 0:
				if self.updated_assets_number:
					self.view_layer_list = list(self.asset_view_layers.keys())
					self.percent = 0
					self.total_assets = len(self.asset_view_layers)
					self.updated_assets_number = 0
				else:
					self.post(context, self.cancelling)
			# elif self.updating_viewlayers is None and len(self.view_layer_list):
			# 	self.updating_viewlayers = self.view_layer_list.pop()
			# 	self.update_viewlayers(context, self.updating_viewlayers)

		return{'PASS_THROUGH'}

	def importing(self, context, asset):
		self.asset_name = path.basename(asset)
		self.asset_path = asset
		updated = self.create_asset_blendfile()
		# updated = self.import_asset(context, asset)

		self.percent = round(100 - (len(self.import_list) * 100 / self.total_assets), 2)
		context.scene.lm_import_progress = '{} %  -  {} / {}  -  {} asset(s) updated  -  {} assets(s) skipped'.format(self.percent, self.total_assets - len(self.import_list), self.total_assets, self.updated_assets_number, self.skipped_asset_number)

		if updated:
			self.updated_assets.append(updated)
		
		self.importing_asset = None

	def import_asset(self, context, asset_path):
		curr_asset = A.LMAsset(context, asset_path)
		asset_name = curr_asset.asset_name

		self.log.init_progress_asset(asset_name)

		if not curr_asset.is_valid:
			context.scene.lm_import_message = 'Skipping Asset  :  Asset {} is not valid'.format(asset_name)
			self.log.warning('Asset "{}" is not valid.\n		Skipping file'.format(asset_name))
			self.log.store_failure('Asset "{}" is not valid.\n		Skipping file'.format(asset_name))
			self.skipped_asset_number += 1
			return

		# Import new asset
		if asset_name not in bpy.data.collections and asset_name not in context.scene.lm_asset_list:
			# self.create_asset_blendfile()
			updated, success, failure = curr_asset.import_asset()
			H.set_active_collection(context, self.asset_collection.name)

			self.log.success += success
			self.log.failure += failure
			context.scene.lm_import_message = 'Importing Asset  :  {}'.format(asset_name)
			self.report({'INFO'}, 'Asset {} have been imported'.format(asset_name))
			self.updated_assets_number += 1

		# Update Existing asset
		else:
			updated, success, failure = curr_asset.update_asset()
			H.set_active_collection(context, self.asset_collection.name)

			self.log.success += success
			self.log.failure += failure
			if updated:
				context.scene.lm_import_message = 'Update Asset  :  {}'.format(asset_name)
				self.report({'INFO'}, 'Asset {} have been updated'.format(asset_name))
				self.updated_assets_number += 1
			else:
				context.scene.lm_import_message = 'Skipping Asset  :  Asset {} is already Up to date'.format(asset_name)
				self.report({'INFO'}, 'Asset {} have been skipped / is already up to date'.format(asset_name))
				self.skipped_asset_number += 1
			

		curr_asset_view_layer = H.get_layer_collection(context.view_layer.layer_collection, curr_asset.asset_name)
		
		if updated:
			# Store asset collection view layer
			self.asset_view_layers[curr_asset_view_layer.name] = curr_asset_view_layer
			context.scene.lm_asset_list[curr_asset_view_layer.name].view_layer = curr_asset_view_layer.name

			# H.switch_current_viewlayer(context, curr_asset_view_layer.name)

			# Refresh UI
			bpy.ops.wm.redraw_timer(type='DRAW', iterations=1)
			# Hide asset in Global View Layer
			curr_asset_view_layer.hide_viewport = True

			self.autosave(context)

			return asset_name
		
		return None
	
	# Not Needed anymore ?
	def update_viewlayers(self, context, view_layer):
		H.update_view_layer(context, view_layer, self.updated_assets, self.asset_view_layers)

		self.updated_assets_number += 1
		self.percent = round((self.updated_assets_number * 100 / self.total_assets), 2)
		context.scene.lm_import_message = 'Updating ViewLayers : {}'.format(view_layer)
		context.scene.lm_viewlayer_progress = '{} %  -  {}/{} layer(s) updated'.format(self.percent, self.updated_assets_number, self.total_assets)
		self.log.info(context.scene.lm_import_message)
		self.updating_viewlayers = None
		
		if len(self.view_layer_list) == 0:
			self.post(context, self.cancelling)

	def autosave(self, context):
		if context.scene.lm_import_autosave_step == 0:
			return
		
		if self.autosave_step > context.scene.lm_import_autosave_step:
			self.autosave_step = 1

			if bpy.data.is_saved:
				backup_filepath = path.join(path.dirname(bpy.data.filepath), path.basename(bpy.data.filepath).replace('.blend', '_bak.blend'))
			else:
				backup_filepath = path.join(bpy.app.tempdir, 'LM_autobak.blend')
				
			self.log.info('Autosaving {}'.format(backup_filepath))
			bpy.ops.wm.save_as_mainfile('EXEC_DEFAULT',filepath=backup_filepath, copy=True )
		else:
			self.autosave_step += 1
			self.log.info('Autosave after {} import(s)'.format(context.scene.lm_import_autosave_step - self.autosave_step + 1))

	def post(self, context, cancelled=False):
		# for a in self.view_layer_list:
		# 	self.update_viewlayers(context, a)
			
		# # Set the global View_layer active
		# if self.asset_name in context.scene.view_layers:
		# 	context.window.view_layer = context.scene.view_layers[self.asset_name]
		# else:	
		# 	context.window.view_layer = context.scene.view_layers[context.scene.lm_initial_view_layer]

		H.renumber_assets(context)

		self.log.complete_progress_asset()

		for a in self.updated_assets:
			bpy.ops.scene.lm_refresh_asset_status(mode= 'ASSET', asset_name = a)
			bpy.ops.scene.lm_remove_asset_from_import_list(asset_name = a)

		self.end()

		if cancelled:
			context.scene.lm_import_message = 'Import/Update Cancelled'
			self.report({'ERROR'}, 'Lineup Maker : Import/Update Cancelled')
			return {'CANCELLED'}
		else:
			context.scene.lm_import_message = 'Import/Update Completed'
			self.report({'INFO'}, 'Lineup Maker : Import/Update Completed')
			return {'FINISHED'}

	def end(self):
		bpy.context.window_manager.event_timer_remove(self._timer)
		self.import_list = []
		self.view_layer_list = []
		self.updated_assets = []
		self.updated_view_layers = []
		self.importing_asset = None
		self.stopped = True
		self.updating_viewlayers = False
		self.cancelling = False

	def create_asset_blendfile(self):
		# current_dir = path.dirname(path.realpath(__file__))
		# startup_catalog = path.join(current_dir, 'StartupCatalog', "StartupCatalog.blend")

		# command = '''import bpy

# {}({})
# bpy.ops.object.move_to_collection(collection_index=0, is_new=True, new_collection_name="{}")
# bpy.ops.wm.save_as_mainfile(filepath = "{}")
# bpy.ops.wm.quit_blender()
# '''.format(m.import_command[2], m.import_command[3], self.asset_name, path.join(self.param['lm_blend_catalog_path'], self.asset_name + '.blend'))

		command = '''import bpy

bpy.ops.scene.lm_import_assets("INVOKE_DEFAULT", mode = "ASSET", asset_name = "{}", asset_path = "{}")
bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.move_to_collection(collection_index=0, is_new=True, new_collection_name="{}")
bpy.context.scene.lm_is_catalog_scene = True
bpy.ops.wm.save_as_mainfile(filepath = "{}")
bpy.ops.wm.quit_blender()
'''.format(self.asset_name, self.asset_path, self.asset_name, path.join(bpy.context.scene.lm_blend_catalog_path, self.asset_name + '.blend'))
		print(command)

		subprocess.check_call([bpy.app.binary_path, V.LM_CATALOG_PATH, '--python-expr', command])

		return True

class LM_OP_ImportAssets(bpy.types.Operator):
	bl_idname = "scene.lm_import_assets"
	bl_label = "Lineup Maker: Import all assets from source folder"
	bl_options = {'REGISTER'}

	mode : bpy.props.EnumProperty(items=[("ASSET", "Asset", ""), ("QUEUE", "Queue", ""), ("ALL", "All", ""), ("IMPORT", "Import", ""), ("IMPORT_NEW", "Import New", "")])
	asset_name : bpy.props.StringProperty(name="Asset Name", default='', description='Name of the asset to export')
	asset_path : bpy.props.StringProperty(name="Asset Path", default='', description='Asset path.')
	
	folder_src = ''
	asset_collection = ''
	asset_view_layers = {}
	import_list = []
	view_layer_list = []
	updated_assets = []
	updated_view_layers = []
	log = None
	_timer = None
	stopped = None
	importing_asset = None
	updating_viewlayers = None
	cancelling = False
	percent = 0
	total_assets = 0
	updated_assets_number = 0
	skipped_asset_number = 0
	autosave_step = 1

	# @classmethod
	# def poll(cls, context):
	# 	return context.scene.lm_render_collection and path.isdir(context.scene.lm_asset_path)

	def execute(self, context):
		self.log = L.LoggerProgress(context='IMPORT_ASSETS')
		# context.scene.lm_render_collection = self.render_collection
		context.scene.lm_asset_path = self.asset_path

		# Init the scene and store the right variables
		self.folder_src = bpy.path.abspath(context.scene.lm_asset_path)

		if not path.isdir(self.folder_src):
			self.log.error('The asset path is not valid : \n{} '.format(self.folder_src))
			self.report({'ERROR	'}, 'Lineup Maker : The asset path is not valid')
			return {'FINISHED'}

		H.set_active_collection(context, bpy.context.scene.collection.name)
		if context.scene.lm_asset_collection is None:
			self.asset_collection, _ = H.create_asset_collection(context, V.LM_ASSET_COLLECTION)
		else:
			self.asset_collection = context.scene.lm_asset_collection
		H.set_active_collection(context, self.asset_collection.name)
		
		
		# Store the Global View_Layer
		if context.scene.lm_initial_view_layer  == '':
			context.scene.lm_initial_view_layer = context.window.view_layer.name
		else:
			context.window.view_layer = context.scene.view_layers[context.scene.lm_initial_view_layer]

		# Disable the Global View Layer
		context.scene.view_layers[context.scene.lm_initial_view_layer].use = False

		# feed asset view layer with existing one
		for a in context.scene.lm_asset_list:
			self.asset_view_layers[a.view_layer] = H.get_layer_collection(context.view_layer.layer_collection, a.name)

		# if asset_name has been defined - Import one specific asset
		if self.mode == "ASSET":
			if len(self.asset_name):
				asset_path = path.join(self.folder_src, self.asset_name)

				if not path.isdir(asset_path):
					self.log.warning('Asset {} doesn\'t exist in the asset folder {}'.format(self.asset_name, self.folder_src))
					self.report({'INFO'}, 'Lineup Maker : Import cancelled, Asset {} doesn\'t exist in the asset folder {}'.format(self.asset_name, self.folder_src))

					return {'FINISHED'}

				self.import_list = [asset_path]

				H.remove_asset(context, self.asset_name)

		# If asset_name has NOT been defined - scan all subfolders and import only the new necessary one
		elif self.mode == "ALL":
			self.import_list = [path.join(self.folder_src, f,) for f in os.listdir(self.folder_src) if path.isdir(os.path.join(self.folder_src, f))]
		
		elif self.mode == "QUEUE":
			queue_asset_name = [a.name for a in context.scene.lm_render_queue if a.checked]
			self.import_list = [path.join(self.folder_src, f,) for f in os.listdir(self.folder_src) if path.isdir(os.path.join(self.folder_src, f)) and path.basename(os.path.join(self.folder_src, f)) in queue_asset_name]
		
		elif self.mode == "IMPORT":
			import_asset_name = [a.name for a in context.scene.lm_import_list if a.checked]
			self.import_list = [path.join(self.folder_src, f,) for f in os.listdir(self.folder_src) if path.isdir(os.path.join(self.folder_src, f)) and path.basename(os.path.join(self.folder_src, f)) in import_asset_name]
		
		elif self.mode == "IMPORT_NEW":
			import_asset_name = [a.name for a in context.scene.lm_import_list if a.checked and not a.is_imported]
			self.import_list = [path.join(self.folder_src, f,) for f in os.listdir(self.folder_src) if path.isdir(os.path.join(self.folder_src, f)) and path.basename(os.path.join(self.folder_src, f)) in import_asset_name]

		self.total_assets = len(self.import_list)

		H.switch_shadingtype(context, 'SOLID')

		self._timer = bpy.context.window_manager.event_timer_add(0.01, window=bpy.context.window)
		bpy.context.window_manager.modal_handler_add(self)

		return {"RUNNING_MODAL"}

	def modal(self, context, event):
		if event.type == 'ESC':
			self.cancelling = True

		if event.type == 'TIMER':
			# stopped
			if self.stopped:
				bpy.context.window_manager.event_timer_remove(self._timer)
				return {'FINISHED'}

			# importing in progress
			elif self.importing_asset is not None or self.updating_viewlayers is not None:
				return{'PASS_THROUGH'}
			
			# importing current file done -> switch to next file
			elif not self.cancelling and self.importing_asset is None and len(self.import_list):
				self.importing_asset = self.import_list.pop()
				self.importing(context, self.importing_asset)
			
			# import not started -> init import
			elif (self.importing_asset is None or self.cancelling) and len(self.import_list) == 0:
				if self.updated_assets_number:
					self.view_layer_list = list(self.asset_view_layers.keys())
					self.percent = 0
					self.total_assets = len(self.asset_view_layers)
					self.updated_assets_number = 0
				else:
					self.post(context, self.cancelling)
			# elif self.updating_viewlayers is None and len(self.view_layer_list):
			# 	self.updating_viewlayers = self.view_layer_list.pop()
			# 	self.update_viewlayers(context, self.updating_viewlayers)

		return{'PASS_THROUGH'}

	def importing(self, context, asset):
		updated = self.import_asset(context, asset)

		self.percent = round(100 - (len(self.import_list) * 100 / self.total_assets), 2)
		context.scene.lm_import_progress = '{} %  -  {} / {}  -  {} asset(s) updated  -  {} assets(s) skipped'.format(self.percent, self.total_assets - len(self.import_list), self.total_assets, self.updated_assets_number, self.skipped_asset_number)

		if updated:
			self.updated_assets.append(updated)
		
		self.importing_asset = None

	def import_asset(self, context, asset_path):
		curr_asset = A.LMAsset(context, asset_path)
		asset_name = curr_asset.asset_name

		self.log.init_progress_asset(asset_name)

		if not curr_asset.is_valid:
			context.scene.lm_import_message = 'Skipping Asset  :  Asset {} is not valid'.format(asset_name)
			self.log.warning('Asset "{}" is not valid.\n		Skipping file'.format(asset_name))
			self.log.store_failure('Asset "{}" is not valid.\n		Skipping file'.format(asset_name))
			self.skipped_asset_number += 1
			return

		# Import new asset
		if asset_name not in bpy.data.collections and asset_name not in context.scene.lm_asset_list:
			# self.create_asset_blendfile()
			updated, success, failure = curr_asset.import_asset()
			H.set_active_collection(context, self.asset_collection.name)

			self.log.success += success
			self.log.failure += failure
			context.scene.lm_import_message = 'Importing Asset  :  {}'.format(asset_name)
			self.report({'INFO'}, 'Asset {} have been imported'.format(asset_name))
			self.updated_assets_number += 1

		# Update Existing asset
		else:
			updated, success, failure = curr_asset.update_asset()
			H.set_active_collection(context, self.asset_collection.name)

			self.log.success += success
			self.log.failure += failure
			if updated:
				context.scene.lm_import_message = 'Update Asset  :  {}'.format(asset_name)
				self.report({'INFO'}, 'Asset {} have been updated'.format(asset_name))
				self.updated_assets_number += 1
			else:
				context.scene.lm_import_message = 'Skipping Asset  :  Asset {} is already Up to date'.format(asset_name)
				self.report({'INFO'}, 'Asset {} have been skipped / is already up to date'.format(asset_name))
				self.skipped_asset_number += 1
			

		curr_asset_view_layer = H.get_layer_collection(context.view_layer.layer_collection, curr_asset.asset_name)
		
		if updated:
			# Store asset collection view layer
			self.asset_view_layers[curr_asset_view_layer.name] = curr_asset_view_layer
			context.scene.lm_asset_list[curr_asset_view_layer.name].view_layer = curr_asset_view_layer.name

			# H.switch_current_viewlayer(context, curr_asset_view_layer.name)

			# Refresh UI
			bpy.ops.wm.redraw_timer(type='DRAW', iterations=1)
			# Hide asset in Global View Layer
			curr_asset_view_layer.hide_viewport = True

			self.autosave(context)

			return asset_name
		
		return None
	
	def update_viewlayers(self, context, view_layer):
		H.update_view_layer(context, view_layer, self.updated_assets, self.asset_view_layers)

		self.updated_assets_number += 1
		self.percent = round((self.updated_assets_number * 100 / self.total_assets), 2)
		context.scene.lm_import_message = 'Updating ViewLayers : {}'.format(view_layer)
		context.scene.lm_viewlayer_progress = '{} %  -  {}/{} layer(s) updated'.format(self.percent, self.updated_assets_number, self.total_assets)
		self.log.info(context.scene.lm_import_message)
		self.updating_viewlayers = None
		
		if len(self.view_layer_list) == 0:
			self.post(context, self.cancelling)

	def autosave(self, context):
		if context.scene.lm_import_autosave_step == 0:
			return
		
		if self.autosave_step > context.scene.lm_import_autosave_step:
			self.autosave_step = 1

			if bpy.data.is_saved:
				backup_filepath = path.join(path.dirname(bpy.data.filepath), path.basename(bpy.data.filepath).replace('.blend', '_bak.blend'))
			else:
				backup_filepath = path.join(bpy.app.tempdir, 'LM_autobak.blend')
				
			self.log.info('Autosaving {}'.format(backup_filepath))
			bpy.ops.wm.save_as_mainfile('EXEC_DEFAULT',filepath=backup_filepath, copy=True )
		else:
			self.autosave_step += 1
			self.log.info('Autosave after {} import(s)'.format(context.scene.lm_import_autosave_step - self.autosave_step + 1))

	def post(self, context, cancelled=False):
		for a in self.view_layer_list:
			self.update_viewlayers(context, a)
			
		# Set the global View_layer active
		if self.asset_name in context.scene.view_layers:
			context.window.view_layer = context.scene.view_layers[self.asset_name]
		else:	
			context.window.view_layer = context.scene.view_layers[context.scene.lm_initial_view_layer]

		H.renumber_assets(context)

		self.log.complete_progress_asset()

		for a in self.updated_assets:
			bpy.ops.scene.lm_refresh_asset_status(mode= 'ASSET', asset_name = a)
			bpy.ops.scene.lm_remove_asset_from_import_list(asset_name = a)

		self.end()

		if cancelled:
			context.scene.lm_import_message = 'Import/Update Cancelled'
			self.report({'ERROR'}, 'Lineup Maker : Import/Update Cancelled')
			return {'CANCELLED'}
		else:
			context.scene.lm_import_message = 'Import/Update Completed'
			self.report({'INFO'}, 'Lineup Maker : Import/Update Completed')
			return {'FINISHED'}

	def end(self):
		bpy.context.window_manager.event_timer_remove(self._timer)
		self.import_list = []
		self.view_layer_list = []
		self.updated_assets = []
		self.updated_view_layers = []
		self.importing_asset = None
		self.stopped = True
		self.updating_viewlayers = False
		self.cancelling = False


class LM_OP_UpdateJson(bpy.types.Operator):
	bl_idname = "scene.lm_update_json"
	bl_label = "Lineup Maker: update json data in the current scene"
	bl_options = {'REGISTER', 'UNDO'}

	mode : bpy.props.EnumProperty(items=[("ASSET", "Asset", ""), ("QUEUE", "Queue", ""), ("ALL", "All", "")])
	asset_name : bpy.props.StringProperty(name="Asset Name", default='', description='Name of the asset update Json data')

	@classmethod
	def poll(cls, context):
		return path.isdir(context.scene.lm_asset_path)

	def execute(self, context):
		self.log = L.LoggerProgress(context='UPDATE JSON')

		# Init the scene and store the right variables
		self.folder_src = bpy.path.abspath(context.scene.lm_asset_path)

		if not path.isdir(self.folder_src):
			self.log.error('The asset path is not valid : \n{} '.format(self.folder_src))
			self.report({'ERROR	'}, 'Lineup Maker : The asset path is not valid')
			return {'FINISHED'}

		# if asset_name has been defined - Import one specific asset
		if self.mode == "ASSET":
			if len(self.asset_name):
				self.import_list = [path.join(self.folder_src, f,) for f in os.listdir(self.folder_src) if path.isdir(os.path.join(self.folder_src, f)) and f == self.asset_name]
				if len(self.import_list):
					self.update_json()
				else:
					self.log.warning('Asset {} doesn\'t exist in the asset folder {}'.format(self.asset_name, self.folder_src))
					self.report({'INFO'}, 'Lineup Maker : Update cancelled, Asset {} doesn\'t exist in the asset folder {}'.format(self.asset_name, self.folder_src))

		# If asset_name has NOT been defined - scan all subfolders and import only the new necessary one
		elif self.mode == "ALL":
			self.import_list = [path.join(self.folder_src, f,) for f in os.listdir(self.folder_src) if path.isdir(os.path.join(self.folder_src, f)) and f in context.scene.lm_asset_list]
		
		elif self.mode == "QUEUE":
			queue_asset_name = [a.name for a in context.scene.lm_render_queue if a.checked]
			self.import_list = [path.join(self.folder_src, f,) for f in os.listdir(self.folder_src) if path.isdir(os.path.join(self.folder_src, f)) and path.basename(os.path.join(self.folder_src, f)) in queue_asset_name]

		for a in self.import_list:
			self.update_json(context, a)

		return {'FINISHED'}
	
	def update_json(self, context, asset):
		a = A.LMAsset(context, asset)
		for m in a.meshes:
			a.update_json_values(m, context.scene.lm_asset_list[a.asset_name])


class LM_OP_RenderAssets(bpy.types.Operator):
	bl_idname = "scene.lm_render_assets"
	bl_label = "Lineup Maker: Render all assets in the scene"
	bl_options = {'REGISTER', 'UNDO'}
	
	render_list : bpy.props.EnumProperty(items=[("ALL", "All assets", ""), ("QUEUED", "Queded assets", ""), ("LAST_RENDERED", "Last Rendered", "")])

	_timer = None
	shots = None
	stop = None
	frame_range = None
	remaining_frames = None
	remaining_assets = None
	rendering = None
	need_render_asset = None
	output_node = None
	context = None
	initial_view_layer = None
	rendered_assets = []
	render_filename = ''
	render_path = ''
	percent = 0
	total_assets = 0
	asset_number = 1

	composite_filepath = ''

	def pre(self, d1, d2):
		self.rendering = True
		
	def post(self, d1, d2):
		if self.remaining_frames <= 1:
			asset = self.need_render_asset[0]
			asset.need_render = False
			asset.rendered = True
			
			asset.render_list.clear()
			for file in os.listdir(self.render_path):
				render = asset.render_list.add()
				render.render_filepath = os.path.join(self.render_path, file)

		else:
			self.remaining_frames -= 1

	def end(self):
		self.rendered_assets = []
		self.need_render_asset = []


	def cancelled(self, d1, d2):
		self.stop = True

	def register_render_handler(self):
		bpy.app.handlers.render_pre.append(self.pre)
		bpy.app.handlers.render_post.append(self.post)
		bpy.app.handlers.render_cancel.append(self.cancelled)
		self._timer = bpy.context.window_manager.event_timer_add(0.1, window=bpy.context.window)

	def unregister_render_handler(self):
		bpy.app.handlers.render_pre.remove(self.pre)
		bpy.app.handlers.render_post.remove(self.post)
		bpy.app.handlers.render_cancel.remove(self.cancelled)
		bpy.context.window_manager.event_timer_remove(self._timer)

	def execute(self, context):
		# bpy.ops.scene.lm_refresh_asset_status()

		self.stop = False
		self.rendering = False
		scene = bpy.context.scene
		wm = bpy.context.window_manager

		# self.shots = [ o.name+'' for o in scene.lm_render_collection.all_objects.values() if o.type=='CAMERA' and o.visible_get() == True ]

		if not context.scene.lm_default_camera:
			self.report({"WARNING"}, 'No Default cameras defined')
			return {"FINISHED"}       

		if self.render_list == 'ALL':
			queued_list = scene.lm_asset_list
		elif self.render_list == 'QUEUED':
			queued_list = [scene.lm_asset_list[a.name] for a in scene.lm_render_queue if a.checked]
		elif self.render_list == 'LAST_RENDERED':
			queued_list = [scene.lm_asset_list[a.name] for a in scene.lm_last_render_list]

		for asset in queued_list:
			render_path, render_filename = self.get_render_path(context, asset.name)

			# Set  need_render status for each assets
			need_render = True
			if not scene.lm_force_render:
				if not asset.rendered:
					if asset.render_date:
						
						rendered_files = os.listdir(render_path)
						frame_range = H.get_current_frame_range(context)
						if len(rendered_files) < frame_range:
							asset.need_render = True
						else:
							asset.need_render = True
							# if asset.render_date < asset.import_date:
							# 	asset.need_render = True
							# 	break
					else: # Asset has never been rendered
						asset.need_render = True
				else: # Asset already Rendered
					asset.need_render = False
			else: # Force Render is True
				H.delete_folder_if_exist(path.join(context.scene.lm_render_path, asset.name))
				asset.rendered = False
				asset.render_path = ''
				asset.render_list.clear()
				asset.need_render = True
		
		self.rendered_assets = []
		self.need_render_asset = [a for a in scene.lm_asset_list if a.need_render]
		self.remaining_assets = len(self.need_render_asset)
		self.asset_number = 1
		self.total_assets = len(self.need_render_asset)
		self.initial_view_layer = context.window.view_layer

		self.frame_range = H.get_current_frame_range(context)
		self.remaining_frames = self.frame_range
		
		self.clear_composite_tree(context)
		self.context = context

		bpy.context.scene.render.use_overwrite = context.scene.lm_override_frames
		bpy.context.scene.render.filepath = bpy.path.abspath(r"c:\\tmp\\")
		
		# context.scene.render.film_transparent = True

		self.register_render_handler()
		
		bpy.context.window_manager.modal_handler_add(self)

		return {"RUNNING_MODAL"}
	
	def modal(self, context, event):
		if event.type == 'TIMER':

			if True in (not self.need_render_asset, self.stop is True):

				self.unregister_render_handler()
				bpy.context.window_manager.event_timer_remove(self._timer)

				context.window.view_layer = self.initial_view_layer

				if self.stop:
					self.report({'WARNING'}, "Lineup Maker : Render cancelled by user")
					self.print_render_log()
					
				else:
					self.report({'INFO'}, "Lineup Maker : Render completed")
					self.print_render_log()

				context.scene.lm_last_render_list.clear()
				
				for asset in self.rendered_assets:
					a = context.scene.lm_last_render_list.add()
					a.name = asset.name
					a.composited = asset.composited

				# Export lastly selected assets
				if context.scene.lm_pdf_export_last_rendered:
					bpy.ops.scene.lm_export_pdf(mode='LAST_RENDERED')
				
				self.end()
				return {"FINISHED"} 


			elif self.rendering  and self.need_render_asset[0].need_render is False and self.need_render_asset[0].rendered is True:
				asset = self.need_render_asset[0]
				if context.scene.lm_precomposite_frames:
					self.unregister_render_handler()
					
					composite = C.LM_Composite_Image(context)
					composite.composite_asset(asset)
					
					asset.render_date = time.time()
					self.register_render_handler()

				self.rendered_assets.append(asset)

				self.need_render_asset.pop(0)
				self.remaining_frames = self.frame_range

				self.remaining_assets -= 1
				self.asset_number += 1

				self.rendering = False
				

			elif self.rendering is False:
				H.clear_composite_tree(context)
				self.percent = round(self.asset_number * 100 / self.total_assets, 2)
				context.scene.lm_render_message = 'Rendering {}'.format(self.need_render_asset[0].name)
				context.scene.lm_render_progress = '{} %  - Asset n° {} / {}'.format(self.percent, self.asset_number, self.total_assets)
				self.render(context)

		return {"PASS_THROUGH"}

	def render(self, context):
		scn = bpy.context.scene 	

		asset = self.need_render_asset[0]

		self.render_path, self.render_filename = self.get_render_path(context, asset.name)

		self.report({'INFO'}, "Lineup Maker : Rendering '{}'".format(self.render_filename + (str(bpy.context.scene.frame_current).zfill(4)+'.png')))

		# # Try to Skip Existing Files
		# render_files = [f for f in os.listdir(self.render_path) if path.splitext(f)[1] == H.get_curr_render_extension(context) and ]

		# for files in render_files:
		# 	pass

		asset.need_render = True
		asset.render_path = self.render_path

		# switch to the proper view_layer
		context.window.view_layer = scn.view_layers[asset.name]
		
		H.set_rendering_camera(context, asset)

		self.output_node = self.build_output_nodegraph(context, self.asset_number, asset)
		# bpy.context.scene.render.filepath = self.render_filename + context.scene.camera.name + '_'
		# self.output_node.mute = True

		bpy.ops.render.render("INVOKE_DEFAULT", animation=True, write_still=False, layer=asset.view_layer)

	def print_render_log(self):
		self.report({'INFO'}, "Lineup Maker : {} assets rendered".format(len(self.rendered_assets)))
		for a in self.rendered_assets:
			self.report({'INFO'}, "Lineup Maker : {} rendered".format(a.name))

	def clear_composite_tree(self, context):
		tree = context.scene.node_tree
		nodes = tree.nodes
		nodes.clear()

	def build_output_nodegraph(self, context, index, asset):
		tree = context.scene.node_tree
		nodes = tree.nodes

		location = (0, -500 * index)
		incr = 300

		rl = nodes.new('CompositorNodeRLayers')
		rl.location = location
		rl.layer = asset.view_layer
		out = nodes.new('CompositorNodeOutputFile')

		sub_location = (location[0] + incr, location[1])
		
		out.location = sub_location

		out.base_path = asset.render_path
		out.file_slots[0].path = asset.name + '_' + context.scene.camera.name + '_'
		# out.format.compression = 0

		tree.links.new(rl.outputs[0], out.inputs[0])

		location = (location[0], location[1] - incr)
			
		print('Lineup Maker : Output Node graph built')

		return out

	def get_render_path(self, context, asset_name):
		render_path = os.path.abspath(os.path.join(os.path.abspath(context.scene.lm_render_path), asset_name))
		render_filename = render_path + '\\{}_'.format(asset_name)
		H.create_folder_if_neeed(render_path)
		
		return render_path, render_filename

	def revert_need_render(self, context):
		need_render_asset = [a for a in context.scene.lm_asset_list if a.need_render]

		for asset in need_render_asset:
			asset.need_render = False
			asset.render_date = time.time()
			asset.rendered = False


class LM_OP_CompositeRenders(bpy.types.Operator):
	bl_idname = "scene.lm_compositerenders"
	bl_label = "Lineup Maker: composite all rendered assets"
	bl_options = {'REGISTER', 'UNDO'}

	composite_list : bpy.props.EnumProperty(items=[("ALL", "All assets", ""), ("QUEUED", "Queded assets", "")])

	_timer = None
	shots = None
	stop = None
	remaining_assets = None
	rendering = None
	need_composite_assets = None
	asset_number = 0
	output_node = None
	context = None
	composited_assets = []
	composite_filename = ''
	composite_path = ''

	composite_filepath = ''

	def pre(self, d1, d2):
		self.rendering = True
		self.report({'INFO'}, "Lineup Maker : Rendering '{}'".format(os.path.join(self.need_render_asset[0].render_path, self.need_render_asset[0].name)))
		
	def post(self, d1, d2):
		if self.remaining_frames <= 1:
			asset = self.need_render_asset[0]
			asset.need_render = False
			asset.rendered = True
			
			asset.render_list.clear()
			for file in os.listdir(self.render_path):
				render = asset.render_list.add()
				render.render_filepath = os.path.join(self.render_path, file)

		else:
			self.remaining_frames -= 1

	def cancelled(self, d1, d2):
		self.stop = True

	def register_render_handler(self):
		bpy.app.handlers.render_pre.append(self.pre)
		bpy.app.handlers.render_post.append(self.post)
		bpy.app.handlers.render_cancel.append(self.cancelled)
		self._timer = bpy.context.window_manager.event_timer_add(0.1, window=bpy.context.window)

	def unregister_render_handler(self):
		bpy.app.handlers.render_pre.remove(self.pre)
		bpy.app.handlers.render_post.remove(self.post)
		bpy.app.handlers.render_cancel.remove(self.cancelled)
		bpy.context.window_manager.event_timer_remove(self._timer)

	def execute(self, context):
		bpy.ops.scene.lm_refresh_asset_status()

		self.stop = False
		self.compositing = False
		scene = bpy.context.scene
		wm = bpy.context.window_manager

		# self.shots = [ o.name+'' for o in scene.lm_render_collection.all_objects.values() if o.type=='CAMERA' and o.visible_get() == True ]     

		if self.composite_list == 'ALL':
			queued_list = [a for a in scene.lm_asset_list if a.rendered]
		elif self.composite_list == 'QUEUED':
			queued_list = [scene.lm_asset_list[a.name] for a in scene.lm_render_queue if a.checked and scene.lm_asset_list[a.name].rendered]

		for asset in queued_list:

			# Set  need_render status for each assets
			if not scene.lm_force_composite:
				if not asset.composited:
					composite_file = asset.final_composite_filepath
					if not path.isfile(composite_file):
						asset.need_composite = True
					else:
						asset.need_composite = False
				else: # Asset already composited
					asset.need_composite = False
			else: # Force composite is True
				asset.need_composite = True
		
		self.need_composite_assets = [a for a in scene.lm_asset_list if a.need_composite]
		self.remaining_assets = len(self.need_composite_assets)
		self.asset_number = 0
		
		H.clear_composite_tree(context)
		self.context = context

		bpy.context.scene.render.use_overwrite = context.scene.lm_override_frames
		
		context.scene.render.film_transparent = True

		self.register_render_handler()
		
		bpy.context.window_manager.modal_handler_add(self)

		return {"RUNNING_MODAL"}
	
	def modal(self, context, event):
		if event.type == 'TIMER':

			if True in (not self.need_composite_assets, self.stop is True): 

				self.unregister_render_handler()
				bpy.context.window_manager.event_timer_remove(self._timer)

				if self.stop:
					self.report({'WARNING'}, "Lineup Maker : Render cancelled by user")
					self.print_render_log()
					
				else:
					self.report({'INFO'}, "Lineup Maker : Render completed")
					self.print_render_log()

				self.rendered_assets = []
				return {"FINISHED"} 

			elif self.compositing is False: 
				asset = self.need_composite_assets[0]
				if context.scene.lm_precomposite_frames:
					self.unregister_render_handler()
					
					composite = C.LM_Composite_Image(context)
					composite.composite_asset(asset)
					
					asset.render_date = time.time()
					self.register_render_handler()

				self.composited_assets.append(asset)

				self.need_composite_assets.pop(0)

				self.remaining_assets -= 1
				self.asset_number += 1

				self.compositing = False

		return {"PASS_THROUGH"}

	def print_render_log(self):
		self.report({'INFO'}, "Lineup Maker : {} assets composited".format(len(self.composited_assets)))
		for a in self.composited_assets:
			self.report({'INFO'}, "Lineup Maker : {} composited".format(a.name))

	def build_output_nodegraph(self, context, index, asset):
		tree = context.scene.node_tree
		nodes = tree.nodes

		location = (0, -500 * index)
		incr = 300

		rl = nodes.new('CompositorNodeRLayers')
		rl.location = location
		rl.layer = asset.view_layer
		out = nodes.new('CompositorNodeOutputFile')

		sub_location = (location[0] + incr, location[1])
		
		out.location = sub_location

		out.base_path = asset.render_path
		out.file_slots[0].path = asset.name + '_'
		# out.format.compression = 0

		tree.links.new(rl.outputs[0], out.inputs[0])

		location = (location[0], location[1] - incr)
			
		print('Lineup Maker : Output Node graph built')

		return out

	def revert_need_render(self, context):
		need_render_asset = [a for a in context.scene.lm_asset_list if a.need_render]

		for asset in need_render_asset:
			asset.need_render = False
			asset.render_date = time.time()
			asset.rendered = False


class LM_OP_ExportPDF(bpy.types.Operator):
	bl_idname = "scene.lm_export_pdf"
	bl_label = "Lineup Maker: Export PDF in the Render Path"
	bl_options = {'REGISTER', 'UNDO'}

	mode : bpy.props.EnumProperty(items=[("ALL", "All", ""), ("QUEUE", "Queue", ""), ("LAST_RENDERED", "Last Rendered", "")])

	chapter = ''
	section = ''
	cancelling = False
	stopped = False
	generating_page = None
	empty_toc_page_composited = False
	pages_composited = False
	toc_page_composited = False
	pdf = None
	composite = None
	
	asset_name_list = []
	generated_pages = []
	percent = 0
	total_page_number = 0
	updated_page_number = 0

	def execute(self, context):
		bpy.ops.scene.lm_refresh_asset_status()

		self.composite = C.LM_Composite_Image(context)
		res = self.composite.composite_res
		orientation = 'P' if res[1] < res[0] else 'L'
		self.pdf = FPDF(orientation, 'pt', (res[0], res[1]))
		self.generated_pages = []

		if self.mode == 'ALL':
			self.asset_name_list = [a.name for a in context.scene.lm_asset_list if a.composited]
		elif self.mode == 'QUEUE':
			self.asset_name_list = [a.name for a in context.scene.lm_render_queue if a.checked and a.composited]
		elif self.mode == 'LAST_RENDERED':
			self.asset_name_list = [a.name for a in context.scene.lm_last_render_list]

		self.asset_name_list = H.sort_asset_list(self.asset_name_list)

		self.total_page_number = len(self.asset_name_list)

		self._timer = bpy.context.window_manager.event_timer_add(0.1, window=bpy.context.window)
		bpy.context.window_manager.modal_handler_add(self)

		return {"RUNNING_MODAL"}
	
	def modal(self, context, event):
		if event.type == 'ESC':
			self.cancelling = True

		if event.type == 'TIMER':
			if self.stopped:
				bpy.context.window_manager.event_timer_remove(self._timer)
				return {'FINISHED'}
			elif self.generating_page is not None:
				return{'PASS_THROUGH'}
			elif self.cancelling:
				context.scene.lm_pdf_message = 'PDF Export Cancelled !'
				self.end()
			elif not self.empty_toc_page_composited:
				self.generate_empty_toc(context)
			elif self.generating_page is None and len(self.asset_name_list):
				self.generating_page = self.asset_name_list[0]
				self.generated_pages.append(self.generating_page)
				self.asset_name_list = self.asset_name_list[1:]
				self.generate_page(context, self.generating_page)
			elif self.pages_composited and len(self.asset_name_list) == 0 and not self.toc_page_composited:
				self.generate_toc(context)
			elif self.toc_page_composited:
				self.post(context, cancelled=self.cancelling)

		return{'PASS_THROUGH'}

	def generate_empty_toc(self, context):
		# create empty TOC page
		self.composite.create_empty_toc_pages(self.pdf, self.asset_name_list)
		context.scene.lm_pdf_message = 'Empty Table Of Content Created !'
		self.report({'INFO'}, 'Empty Table Of Content Created !')
		self.empty_toc_page_composited = True
		# Refresh UI
		bpy.ops.wm.redraw_timer(type='DRAW', iterations=1)

	def generate_page(self, context, page):
		asset = context.scene.lm_asset_list[page]
		chapter_naming_convention = N.NamingConvention(context, self.chapter, context.scene.lm_chapter_naming_convention)
		asset_naming_convention = N.NamingConvention(context, asset.name, context.scene.lm_asset_naming_convention)

		self.new_chapter, self.new_section = H.set_chapter(self, asset, chapter_naming_convention, asset_naming_convention)

		if self.new_section:
			self.pdf.add_page()
			self.composite.curr_page += 1
			self.composite.composite_pdf_chapter(self.pdf, self.section, is_section=True)

		if self.new_chapter:
			self.pdf.add_page()
			self.composite.curr_page += 1
			self.composite.composite_pdf_chapter(self.pdf, self.chapter)

		self.pdf.add_page()
		self.composite.curr_page += 1
		self.composite.composite_pdf_asset_info(self.pdf, asset.name)

		self.updated_page_number += 1
		self.percent = round(self.updated_page_number * 100 / self.total_page_number, 2)
		context.scene.lm_pdf_message = 'Generating page  :  {}'.format(asset.name)
		context.scene.lm_pdf_progress = '{} %  -  {} / {}'.format(self.percent, self.updated_page_number, self.total_page_number)
		self.report({'INFO'}, 'Generating page  :  {}  {} / {}'.format(asset.name, self.updated_page_number, self.total_page_number))

		if len(self.asset_name_list) == 0:
			self.pages_composited = True
		
		self.generating_page = None

		# Refresh UI
		bpy.ops.wm.redraw_timer(type='DRAW', iterations=1)

	def generate_toc(self, context):
		context.scene.lm_pdf_message = 'Generating Table Of Content !'
		self.report({'INFO'}, 'Generating Table Of Content !')
		self.pdf.page = 1
		self.composite.composite_pdf_toc(self.pdf, self.generated_pages)
		context.scene.lm_pdf_message = 'Table Of Content Generated !'
		self.report({'INFO'}, 'Table Of Content Generated !')
		self.toc_page_composited = True
		
		# Refresh UI
		bpy.ops.wm.redraw_timer(type='DRAW', iterations=1)

	def post(self, context, cancelled=False):
		self.pdf.page = self.composite.curr_page
		
		if self.mode== 'LAST_RENDERED':
			export_name = '{}_{}_lineup_preview.pdf'.format(date.today(), time.time())
		else:
			export_name = '{}_{}_lineup.pdf'.format(date.today(), time.time())

		pdf_file = path.join(context.scene.lm_render_path, export_name)
		self.pdf.output(pdf_file)

		if context.scene.lm_open_pdf_when_exported or self.mode == 'LAST_RENDERED':
			os.system("start " + pdf_file)

		if cancelled:
			self.end()
			context.scene.lm_pdf_message = 'PDF Export Cancelled'
			self.report({'ERROR'}, 'Lineup Maker : PDF Export Cancelled')
			return {'CANCELLED'}
		else:
			self.end()
			context.scene.lm_pdf_message = 'PDF Export Completed'
			self.report({'INFO'}, 'Lineup Maker : PDF Export Completed')
			return {'FINISHED'}

	def end(self):
		self.asset_name_list = []
		self.generated_pages = []
		self.stopped = True
		self.cancelling = False
		self.generating_page = None
		self.empty_toc_page_composited = False
		self.pages_composited = False
		self.toc_page_composited = False
		self.pdf = None
		self.composite = None
		self.chapter = ''
		self.section = ''
		

class LM_OP_RefreshAssetStatus(bpy.types.Operator):
	bl_idname = "scene.lm_refresh_asset_status"
	bl_label = "Lineup Maker: Refresh asset status"
	bl_options = {'REGISTER', 'UNDO'}

	asset_name : bpy.props.StringProperty(name="Asset Name", default='', description='Name of the asset to export')
	mode : bpy.props.EnumProperty(items=[("ALL", "All", ""), ("QUEUE", "Queue", ""), ("ASSET", "Asset", "")])

	def execute(self, context):
		log = L.Logger(context='EXPORT_ASSETS')
		context.scene.lm_render_path

		if self.mode == 'ALL':
			need_update_list = [a for a in context.scene.lm_asset_list] + [ a for a in context.scene.lm_render_queue]
		elif self.mode == 'QUEUE':
			need_update_list = [a for a in context.scene.lm_render_queue if a.checked]
			need_update_list_name = [a.name for a in need_update_list]
			need_update_list += [a for a in context.scene.lm_asset_list if a.name in need_update_list_name]

		elif self.mode =='ASSET':
			try:
				need_update_list = [context.scene.lm_asset_list[self.asset_name]]
			except KeyError:
				need_update_list = []

			try:
				need_update_list += [context.scene.lm_render_queue[self.asset_name]]
			except KeyError:
				pass
			
		for asset in need_update_list:
			self.report({'INFO'}, 'Lineup Maker : Refresh asset status for : "{}"'.format(asset.name))
			log.info('Lineup Maker : Refresh asset status for : "{}"'.format(asset.name))
			rendered_asset = path.join(context.scene.lm_render_path, asset.name)
			asset_path = path.join(context.scene.lm_asset_path, asset.name)
			composite_path = path.join(context.scene.lm_render_path, V.LM_FINAL_COMPOSITE_FOLDER_NAME, '{}{}.jpg'.format(asset.name, V.LM_FINAL_COMPOSITE_SUFFIX))
			asset_format = A.LMAsset(context, asset_path)
			asset.warnings.clear()

			if path.isdir(asset_path):
				asset.asset_path = asset_path
				asset.asset_folder_exists = True
				asset_format.is_valid
			else:
				log.warning('No asset folder found', asset=asset)
				asset.asset_folder_exists = False

			asset.composited = path.isfile(composite_path)
			if asset.composited:
				asset.final_composite_filepath = composite_path
			
			render_path = rendered_asset
			if asset.render_date == 0:
				if path.isdir(rendered_asset):
					rendered_files = [r for r in os.listdir(render_path)]
					if len(rendered_files) == H.get_current_frame_range(context):
						asset.render_date = path.getmtime(path.join(render_path, rendered_files.pop()))
					else:
						asset.rendered = False
						asset.render_path = ''
			
			if asset.render_date > asset.import_date:
				if path.isdir(rendered_asset):
					
					rendered_files = [r for r in os.listdir(render_path) if path.splitext(r)[1].lower() in V.LM_OUTPUT_EXTENSION.values()]

					if len(rendered_files) == H.get_current_frame_range(context):
						asset.rendered = True
						asset.render_path = render_path
					else:
						asset.rendered = False
						asset.render_path = ''
					
					# if len(rendered_files):
					# 	asset.render_camera = self.get_cameraName_from_render(context, asset, rendered_files[0])
						
					asset.render_list.clear()
					for file in rendered_files:
						render_filepath = asset.render_list.add()
						render_filepath.render_filepath = file
				else:
					asset.rendered = False
					asset.render_path = ''
					asset.render_list.clear()
			else:
				asset.rendered = False
				asset.composited = False
				asset.render_path = ''
				asset.render_list.clear()
			
			if asset_format.need_update:
				asset.need_update = True

			# set rendering camera
			H.set_rendering_camera(context, asset)

		return {'FINISHED'}

	def get_cameraName_from_render(self, context, asset, render_filename):
		word_pattern = re.compile(r'({0}{1})([a-zA-Z_]+){1}([0-9]+)'.format(asset.name, context.scene.lm_separator), re.IGNORECASE)
		groups = word_pattern.finditer(render_filename)
		for g in groups:
			return g.group(2)
		else:
			return ''


class LM_OP_ExportAsset(bpy.types.Operator):
	bl_idname = "scene.lm_export_assets"
	bl_label = "Lineup Maker: Export Asset"
	bl_options = {'REGISTER', 'UNDO'}

	export_path = ''
	mode : bpy.props.EnumProperty(items=[("SELECTED", "Selected", ""), ("ASSET", "Asset", ""), ("QUEUE", "Queue", "")])
	asset_name : bpy.props.StringProperty(name="Asset Name", default='', description='Name of the asset to export')
	cancelling = False
	stopped = False
	exporting_asset = None
	export_list = []
	percent = 0
	total_assets = 0

	def execute(self, context):
		log = L.Logger(context='EXPORT_ASSETS')

		self.report({'INFO'}, 'Lineup Maker : Exporting selected objects to asset folder')
		self.json_data = []
			
		if self.mode =='SELECTED':
			if not len(context.selected_objects):
				self.report({'ERROR'}, 'Lineup Maker : Select at least one Mesh object')
				return {'CANCELLED'}
			else:
				found = False
				for o in context.selected_objects:
					if o.type in V.LM_COMPATIBLE_EXPORT_FORMAT:
						found = True
				if not found:
					self.report({'ERROR'}, 'Lineup Maker : Select at least one Mesh object')
					return {'CANCELLED'}
			self.export_path = path.join(context.scene.lm_asset_path, context.scene.lm_exported_asset_name)
			self.asset_name = context.scene.lm_exported_asset_name
			self.export_asset(context)

		elif self.mode == 'ASSET':
			if not len(self.asset_name):
				log.warning('Asset Name is not defined. Export aboard')
				return {'FINISHED'}
			if self.asset_name not in context.scene.lm_asset_list:
				log.warning('Asset Name not in the asset list. Export aboard')
				return {'FINISHED'}

			self.scene_asset = context.scene.lm_asset_list[self.asset_name]
			context.window.view_layer = context.scene.view_layers[self.asset_name]
			self.export_path = path.join(context.scene.lm_asset_path, self.asset_name)

			H.select_asset(context, self.asset_name)

			self.export_asset(context)

		elif self.mode == "QUEUE":
			if not len(context.scene.lm_render_queue):
				log.warning('Render Queue is empty, add asset to the queue first.')
				return {'FINISHED'}
			
			self.export_list = [a.name for a in context.scene.lm_render_queue if a.checked]
			self.total_assets = len(self.export_list)
			self._timer = bpy.context.window_manager.event_timer_add(0.1, window=bpy.context.window)
			bpy.context.window_manager.modal_handler_add(self)

			return {"RUNNING_MODAL"}
		
		if self.mode not in ["QUEUE"]:
			bpy.ops.scene.lm_openfolder(folder_path=self.export_path)

		return {'FINISHED'}
	
	def modal(self, context, event):
		if event.type == 'ESC':
			self.cancelling = True

		if event.type == 'TIMER':
			if self.stopped:
				bpy.context.window_manager.event_timer_remove(self._timer)
				self.report({'INFO'}, 'Lineup Maker : Export complete')
				return {'FINISHED'}
			elif self.exporting_asset is not None:
				return{'PASS_THROUGH'}
			elif not self.cancelling and self.exporting_asset is None and len(self.export_list):
				self.exporting_asset = self.export_list.pop()
				self.asset_name = self.exporting_asset
				self.scene_asset = context.scene.lm_asset_list[self.asset_name]

				self.percent = round(100 - len(self.export_list) * 100 / self.total_assets, 2)
				context.scene.lm_queue_progress = '{} %  -  {} / {}'.format(self.percent, self.total_assets - len(self.export_list), self.total_assets)
				context.scene.lm_queue_message = 'Exporting {}'.format(self.asset_name)

				context.window.view_layer = context.scene.view_layers[self.asset_name]
				self.export_path = path.join(context.scene.lm_asset_path, self.exporting_asset)
				H.select_asset(context, self.exporting_asset)

				self.export_asset(context)

		return{'PASS_THROUGH'}
	
	def post(self, context):
		self.json_data = []
		self.exporting_asset = None
		bpy.ops.scene.lm_refresh_asset_status(mode='ASSET', asset_name=self.asset_name)
		if not len(self.export_list):
			self.end()

	def end(self):
		self.cancelling = False
		self.stopped = True
		self.exporting_asset = None
		self.export_list = []
		self.json_data = []
		self.total_assets = 0
		self.percent = 0

	def export_asset(self, context):
		self.report({'INFO'}, 'Lineup Maker : Exporting {}'.format(self.asset_name))

		texture_list = self.get_textures(context)
		tmpdir = tempfile.mkdtemp()

		self.copy_textures(context, texture_list, tmpdir)

		H.delete_folder_if_exist(self.export_path)
		H.create_folder_if_neeed(self.export_path)
		new_texture_list = {}
		for mesh, _ in texture_list.items():
			new_texture_list[mesh] = [os.path.join(tmpdir, mesh, t) for t in os.listdir(os.path.join(tmpdir, mesh))]

		self.copy_textures(context, new_texture_list, self.export_path)

		H.delete_folder_if_exist(tmpdir)

		selection = context.selected_objects
		
		# Clear Mesh list
		if self.scene_asset is not None:
			self.scene_asset.mesh_list.clear()
		
		for o in selection:
			bpy.ops.object.select_all(action='DESELECT')
			bpy.data.objects[o.name].select_set(True)
			context.view_layer.objects.active = o
			export_filename = path.join(self.export_path, o.name + '.fbx')
	
			bpy.ops.export_scene.fbx(filepath=export_filename, use_selection=True, bake_anim=False, check_existing=False, embed_textures=False)

			# Register Mesh List
			if self.scene_asset is not None:
				m = self.scene_asset.mesh_list.add()
				m = A.LMMeshFile(export_filename)
		
		if self.scene_asset is not None:
			self.scene_asset.asset_path = self.export_path
			self.scene_asset.asset_folder_exists = True

		self.write_json(context)

		self.post(context)

	def copy_textures(self, context, source, destination):
		for mesh, textures in source.items():
			destination_path = path.join(destination, mesh)
			H.create_folder_if_neeed(destination_path)
			for t in textures:
				subprocess.call("xcopy /r /y {} {}".format(t, destination_path))

	
	def get_textures(self, context):
		texture_list = {}
		scn = context.scene
		for o in context.selected_objects:
			material_slots = o.material_slots
			name = o.name
			stats = S.Stats(o)
			json = {'name':name,
					'HDStatus':getattr(V.Status, scn.lm_exported_hd_status).value if self.mode == 'SELECTED' else scn.lm_asset_list[self.asset_name].hd_status, 
					'LDStatus':getattr(V.Status, scn.lm_exported_ld_status).value if self.mode == 'SELECTED' else scn.lm_asset_list[self.asset_name].ld_status,
					'BakingStatus':getattr(V.Status, scn.lm_exported_baking_status).value if self.mode == 'SELECTED' else scn.lm_asset_list[self.asset_name].baking_status,
					'triangles':stats.triangle_count,
					'vertices':stats.vertex_count,
					'hasUV2':stats.uv_count > 1,
					'section':scn.lm_asset_list[self.asset_name].section,
					'fromFile':scn.lm_asset_list[self.asset_name].from_file,
					'materials':[]}
			for slot in material_slots:
				mat = slot.material
				node_tree = mat.node_tree
				nodes = node_tree.nodes

				output_nodes = [n for n in nodes if n.type == "OUTPUT_MATERIAL"]

				output_node = output_nodes[0] if len(output_nodes) else None

				if output_node:
					shaders = self.get_children_node(context, node_tree, output_node)
					
					shader = shaders[0] if len(shaders) else None

					json['materials'].append({'material':mat.name, 'textures':[]})
					if shader:
						textures = [n for n in nodes if n.type == 'TEX_IMAGE']
						for t in textures:
							channel = self.find_channel(context, node_tree, t, shader)
							json['materials'][-1]['textures'].append({'file':path.basename(bpy.path.abspath(t.image.filepath)), 'channel':channel})
							if not len(texture_list.keys()) or o.name not in texture_list.keys():
								texture_list[o.name] = [bpy.path.abspath(t.image.filepath)]
							else:
								texture_list[o.name].append(bpy.path.abspath(t.image.filepath))
					else:
						self.report({'WARRNING'}, 'Lineup Maker : No shader found in material "{}"'.format(mat.name))
				
				else:
					self.report({'WARRNING'}, 'Lineup Maker : No output node found found in material "{}"'.format(mat.name))

			self.json_data.append(json)

		return texture_list


	def write_json(self, context):
		if len(self.json_data):
			for j in self.json_data:
				json_filepath = path.join(self.export_path, j['name'] + '.json')
				with open(json_filepath, 'w', encoding='utf-8') as outfile:
					json.dump(j, outfile, ensure_ascii=False, indent=4)

	def get_children_node(self, context, node_tree, node):
		links = node_tree.links
		children = []

		for l in links:
			if l.to_node == node:
				children.append(l.from_node)

		if len(children) == 0:
			return None
		else:
			return children

	def get_parents_node(self, context, node_tree, node):
		links = node_tree.links
		parents = []

		for l in links:
			if l.from_node == node:
				parents.append({'node':l.to_node, 'input':l.to_socket})
		
		if len(parents) == 0:
			return None
		else:
			return parents
	

	def find_channel(self, context, node_tree,  node, shader):
		links = node_tree.links

		found = False
		curr_node = [{'node':node, 'input':None}]
		channel = 'null'
		while not found:
			if len(curr_node) == 0:
				return 'null'

			nodes = self.get_parents_node(context, node_tree, curr_node.pop()['node'])

			for n in nodes:
				if n is None:
					continue
				if n['node'] == shader:
					found = True
					channel = n['input'].name
					break
				else:
					curr_node = curr_node + [n]
		
		return channel
