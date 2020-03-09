import bpy
import os, time, math, subprocess, json, tempfile, re
from fpdf import FPDF
from os import path
from . import variables as V
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
				bpy.ops.scene.lm_importassets()
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


class LM_OP_ImportAssets(bpy.types.Operator):
	bl_idname = "scene.lm_importassets"
	bl_label = "Lineup Maker: Import all assets from source folder"
	bl_options = {'REGISTER', 'UNDO'}

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
	stoped = None
	importing_asset = None
	updating_viewlayers = None
	cancelling = False
	percent = 0
	total_assets = 0
	updated_assets_number = 0
	skipped_asset_number = 0

	@classmethod
	def poll(cls, context):
		return context.scene.lm_render_collection and path.isdir(context.scene.lm_asset_path)

	def execute(self, context):
		self.log = L.LoggerProgress(context='IMPORT_ASSETS')

		# Init the scene and store the right variables
		self.folder_src = bpy.path.abspath(context.scene.lm_asset_path)

		if not path.isdir(self.folder_src):
			self.log.error('The asset path is not valid : \n{} '.format(self.folder_src))
			self.report({'ERROR	'}, 'Lineup Maker : The asset path is not valid')
			return {'FINISHED'}

		H.set_active_collection(context, V.LM_MASTER_COLLECTION)
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
		if len(self.asset_name):
			self.import_list = [path.join(self.folder_src, f,) for f in os.listdir(self.folder_src) if path.isdir(os.path.join(self.folder_src, f)) and f == self.asset_name]
			if len(self.import_list):
				H.remove_asset(context, self.asset_name)
			else:
				self.log.warning('Asset {} doesn\'t exist in the asset folder {}'.format(self.asset_name, self.folder_src))
				self.report({'INFO'}, 'Lineup Maker : Import cancelled, Asset {} doesn\'t exist in the asset folder {}'.format(self.asset_name, self.folder_src))

				return {'FINISHED'}

		# If asset_name has NOT been defined - scan all subfolders and import only the new necessary one
		else:
			self.import_list = [path.join(self.folder_src, f,) for f in os.listdir(self.folder_src) if path.isdir(os.path.join(self.folder_src, f))]
		
		self.total_assets = len(self.import_list)

		self._timer = bpy.context.window_manager.event_timer_add(0.1, window=bpy.context.window)
		bpy.context.window_manager.modal_handler_add(self)

		return {"RUNNING_MODAL"}

	def modal(self, context, event):
		if event.type == 'ESC':
			self.cancelling = True

		if event.type == 'TIMER':
			if self.stoped:
				bpy.context.window_manager.event_timer_remove(self._timer)
				return {'FINISHED'}
			elif self.importing_asset is not None or self.updating_viewlayers is not None:
				return{'PASS_THROUGH'}
			elif self.updating_viewlayers:
				return{'PASS_THROUGH'}
			elif not self.cancelling and self.importing_asset is None and len(self.import_list):
				self.importing_asset = self.import_list.pop()
				self.importing(context, self.importing_asset)
			elif (self.importing_asset is None or self.cancelling) and len(self.view_layer_list) == 0:
				if self.updated_assets_number:
					self.view_layer_list = list(self.asset_view_layers.keys())
					self.percent = 0
					self.total_assets = len(self.asset_view_layers)
					self.updated_assets_number = 0
				else:
					self.post(context, self.cancelling)
			elif self.updating_viewlayers is None and len(self.view_layer_list):
				self.updating_viewlayers = self.view_layer_list.pop()
				self.update_viewlayers(context, self.updating_viewlayers)

		return{'PASS_THROUGH'}

	def importing(self, context, asset):
		updated = self.import_asset(context, asset)

		self.percent = round(100 - (len(self.import_list) * 100 / self.total_assets), 2)
		context.scene.lm_import_progress = '{} %  -  {}/{}  -  {} asset(s) updated  -  {} assets(s) skipped'.format(self.percent, self.total_assets - len(self.import_list), self.total_assets, self.updated_assets_number, self.skipped_asset_number)

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

			# Hide asset in Global View Layer
			curr_asset_view_layer.hide_viewport = True

			# Refresh UI
			bpy.ops.wm.redraw_timer(type='DRAW', iterations=1)

			return asset_name
		
		return None

	def update_viewlayers(self, context, view_layer):
		if view_layer not in context.scene.view_layers:
			bpy.ops.scene.view_layer_add()
			context.window.view_layer.name = view_layer
			context.view_layer.use_pass_combined = False
			context.view_layer.use_pass_z = False
		else:
			context.window.view_layer = context.scene.view_layers[view_layer]

		if view_layer in self.updated_assets:
			for n in self.asset_view_layers.keys():
				if view_layer != n and view_layer != context.scene.lm_render_collection.name:
					curr_asset_view_layer = H.get_layer_collection(context.view_layer.layer_collection, n)
					if curr_asset_view_layer:
						curr_asset_view_layer.exclude = True
		else:
			for n in self.updated_assets:
				if view_layer != n and view_layer != context.scene.lm_render_collection.name:
					curr_asset_view_layer = H.get_layer_collection(context.view_layer.layer_collection, n)
					if curr_asset_view_layer:
						curr_asset_view_layer.exclude = True
		
		self.updated_assets_number += 1
		self.percent = round((self.updated_assets_number * 100 / self.total_assets), 2)
		context.scene.lm_import_message = 'Updating ViewLayers : {}'.format(view_layer)
		context.scene.lm_import_progress = '{} %  -  {}/{}'.format(self.percent, self.updated_assets_number, self.total_assets)
		self.updating_viewlayers = None
		
		if len(self.view_layer_list) == 0:
			self.post(context, self.cancelling)


	def post(self, context, cancelled=False):
		# Set the global View_layer active
		if len(self.asset_name):
			context.window.view_layer = context.scene.view_layers[self.asset_name]
		else:	
			context.window.view_layer = context.scene.view_layers[context.scene.lm_initial_view_layer]

		H.renumber_assets(context)

		self.log.complete_progress_asset()

		bpy.ops.scene.lm_refresh_asset_status()

		if cancelled:
			self.end()
			context.scene.lm_import_message = 'Import/Update Cancelled'
			self.report({'ERROR'}, 'Lineup Maker : Import/Update Cancelled')
			return {'CANCELLED'}
		else:
			self.end()
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
		self.stoped = True
		self.updating_viewlayers = False
		self.cancelling = False
		

	
class LM_OP_RenderAssets(bpy.types.Operator):
	bl_idname = "scene.lm_render_assets"
	bl_label = "Lineup Maker: Render all assets in the scene"
	bl_options = {'REGISTER', 'UNDO'}
	
	render_list : bpy.props.EnumProperty(items=[("ALL", "All assets", ""), ("QUEUED", "Queded assets", "")])

	_timer = None
	shots = None
	stop = None
	frame_range = None
	remaining_frames = None
	remaining_assets = None
	rendering = None
	need_render_asset = None
	asset_number = 0
	output_node = None
	context = None
	initial_view_layer = None
	rendered_assets = []
	render_filename = ''
	render_path = ''

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
			queued_list = [scene.lm_asset_list[a.name] for a in scene.lm_render_queue]

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
							for f in os.listdir(render_path):
								if asset.render_date < asset.import_date:
									asset.need_render = True
									break
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
		
		self.need_render_asset = [a for a in scene.lm_asset_list if a.need_render]
		self.remaining_assets = len(self.need_render_asset)
		self.asset_number = 0
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

				self.rendered_assets = []
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
				self.render(context)

		return {"PASS_THROUGH"}

	def render(self, context):
		scn = bpy.context.scene 	

		asset = self.need_render_asset[0]

		self.render_path, self.render_filename = self.get_render_path(context, asset.name)

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
			queued_list = [scene.lm_asset_list[a.name] for a in scene.lm_render_queue if scene.lm_asset_list[a.name].rendered]

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

	chapter = ''

	def execute(self, context):
		bpy.ops.scene.lm_refresh_asset_status()

		composite = C.LM_Composite_Image(context)
		res = composite.composite_res
		orientation = 'P' if res[1] < res[0] else 'L'
		pdf = FPDF(orientation, 'pt', (res[0], res[1]))
		
		asset_name_list = [a.name for a in context.scene.lm_asset_list if a.composited]
		# chapter_name_dict = {}
		# for i, asset in enumerate(asset_name_list):
		# 	chapter_nc = N.NamingConvention(context, asset, context.scene.lm_chapter_naming_convention)
		# 	new_name = ''
		# 	for word in chapter_nc.naming_convention['name']:
		# 		new_name += '_' + word
		# 	chapter_name_dict[asset] = [new_name, i]

		# chapter_name_list = chapter_name_dict.values()

		# for i,name in enumerate(chapter_name_list):
		# 	asset_name_list[name[1]] = name[0]

		asset_name_list.sort()

		# create TOC
		composite.create_empty_toc_pages(pdf)

		for name in asset_name_list:
			asset = context.scene.lm_asset_list[name]
			chapter_naming_convention = N.NamingConvention(context, self.chapter, context.scene.lm_chapter_naming_convention)
			asset_naming_convention = N.NamingConvention(context, asset.name, context.scene.lm_asset_naming_convention)

			new_chapter = H.set_chapter(self, chapter_naming_convention, asset_naming_convention)

			if new_chapter:
				pdf.add_page()
				composite.curr_page += 1
				composite.composite_pdf_chapter(pdf, self.chapter)

			pdf.add_page()
			composite.curr_page += 1
			composite.composite_pdf_asset_info(pdf, asset.name)
		
		pdf.page = 1
		composite.composite_pdf_toc(pdf)

		pdf.page = composite.curr_page
		
		pdf_file = path.join(context.scene.lm_render_path, 'lineup.pdf')
		pdf.output(pdf_file)

		self.report({'INFO'}, 'Lineup Maker : PDF File exported correctly : "{}"'.format(pdf_file))

		if context.scene.lm_open_pdf_when_exported:
			os.system("start " + pdf_file)

		return {'FINISHED'}


class LM_OP_RefreshAssetStatus(bpy.types.Operator):
	bl_idname = "scene.lm_refresh_asset_status"
	bl_label = "Lineup Maker: Refresh asset status"
	bl_options = {'REGISTER', 'UNDO'}

	asset_name : bpy.props.StringProperty(name="Asset Name", default='', description='Name of the asset to export')

	def execute(self, context):
		log = L.Logger(context='EXPORT_ASSETS')
		context.scene.lm_render_path

		if self.asset_name == '':
			need_update_list = [a for a in context.scene.lm_asset_list] + [ a for a in context.scene.lm_render_queue]
		else:
			need_update_list = [a for a in context.scene.lm_asset_list if a.name == self.asset_name] + [ a for a in context.scene.lm_render_queue if a.name == self.asset_name]

		for asset in need_update_list:
			self.report({'INFO'}, 'Lineup Maker : Refresh asset status for : "{}"'.format(asset.name))
			log.info('Lineup Maker : Refresh asset status for : "{}"'.format(asset.name))
			rendered_asset = path.join(context.scene.lm_render_path, asset.name)
			asset_path = path.join(context.scene.lm_asset_path, asset.name)
			composite_path = path.join(context.scene.lm_render_path, V.LM_FINAL_COMPOSITE_FOLDER_NAME, '{}{}.jpg'.format(asset.name, V.LM_FINAL_COMPOSITE_SUFFIX))

			if path.isdir(asset_path):
				asset.asset_path = asset_path
				asset.asset_folder_exists = True
			else:
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
					
					rendered_files = [r for r in os.listdir(render_path)]

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
			
			# set rendering camera
			cam = H.set_rendering_camera(context, asset)

		return {'FINISHED'}

	def get_cameraName_from_render(self, context, asset, render_filename):
		word_pattern = re.compile(r'({0}{1})([a-zA-Z_]+){1}([0-9]+)'.format(asset.name, context.scene.lm_separator), re.IGNORECASE)
		groups = word_pattern.finditer(render_filename)
		for g in groups:
			return g.group(2)
		else:
			return ''

class LM_OP_ExportAsset(bpy.types.Operator):
	bl_idname = "scene.lm_export_asset"
	bl_label = "Lineup Maker: Export Asset"
	bl_options = {'REGISTER', 'UNDO'}

	export_path = ''
	mode : bpy.props.EnumProperty(items=[("SELECTED", "Selected", ""), ("ASSET", "Asset", "")])
	asset_name : bpy.props.StringProperty(name="Asset Name", default='', description='Name of the asset to export')

	# @classmethod
	# def poll(cls, context):
	# 	if self.mode =='SELECTED':
	# 		object_types = [o.type for o in context.selected_objects]
	# 		return len(object_types) and 'MESH' in object_types and len(context.scene.lm_exported_asset_name)
	# 	elif self.mode == 'ASSET':
	# 		return len(self.asset_name)

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
		elif self.mode == 'ASSET':
			if not len(self.asset_name):
				log.warning('Asset Name is not defined. Export aboard')
				return {'FINISHED'}
			if self.asset_name not in context.scene.lm_asset_list:
				log.warning('Asset Name not in the asset list. Export aboard')
				return {'FINISHED'}

			context.window.view_layer = context.scene.view_layers[self.asset_name]
			self.export_path = path.join(context.scene.lm_asset_path, self.asset_name)

			H.select_asset(context, self.asset_name)

		texture_list = self.get_textures(context)
		tmpdir = tempfile.mkdtemp()

		self.copy_textures(context, texture_list, tmpdir)

		H.delete_folder_if_exist(self.export_path)
		H.create_folder_if_neeed(self.export_path)
		new_tewture_list = {}
		for mesh, _ in texture_list.items():
			new_tewture_list[mesh] = [os.path.join(tmpdir, mesh, t) for t in os.listdir(os.path.join(tmpdir, mesh))]

		self.copy_textures(context, new_tewture_list, self.export_path)

		H.delete_folder_if_exist(tmpdir)

		selection = context.selected_objects

		for o in selection:
			bpy.ops.object.select_all(action='DESELECT')
			bpy.data.objects[o.name].select_set(True)
			context.view_layer.objects.active = o
			export_filename = path.join(self.export_path, o.name + '.fbx')
			bpy.ops.export_scene.fbx(filepath=export_filename, use_selection=True, bake_anim=False, check_existing=False, embed_textures=False)

		self.write_json(context)

		bpy.ops.scene.lm_openfolder(folder_path=self.export_path)

		
		return {'FINISHED'}
	
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
					'materials':[]}
			for slot in material_slots:
				mat = slot.material
				node_tree = mat.node_tree
				nodes = node_tree.nodes

				# for n in nodes:
				# 	print(n)
				# 	for d in dir(n):
				# 		print(d)
				# 		print(getattr(n, d))

				output_nodes = [n for n in nodes if n.type == "OUTPUT_MATERIAL"]

				output_node = output_nodes[0] if len(output_nodes) else None

				if output_node:
					shaders = self.get_children_node(context, node_tree, output_node)
					
					shader = shaders[0] if len(shaders) else None

					# links = node_tree.links
					# for l in links:
					# 	print(l.from_node)
					# 	print(dir(l))
					# 	print(l.to_socket)
					# 	print(dir(l.to_socket))
					# 	print(l.to_socket.name)

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
