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

	@classmethod
	def poll(cls, context):
		return context.scene.lm_render_collection and path.isdir(context.scene.lm_asset_path)

	def execute(self, context):
		log = L.Logger(context='IMPORT_ASSETS')
		folder_src = bpy.path.abspath(context.scene.lm_asset_path)

		H.set_active_collection(context, V.LM_MASTER_COLLECTION)
		if context.scene.lm_asset_collection is None:
			asset_collection, _ = H.create_asset_collection(context, V.LM_ASSET_COLLECTION)
		else:
			asset_collection = context.scene.lm_asset_collection
		H.set_active_collection(context, asset_collection.name)
		
		object_list = asset_collection.objects

		# Store the Global View_Layer
		if context.scene.lm_initial_view_layer  == '':
			context.scene.lm_initial_view_layer = context.window.view_layer.name
		else:
			context.window.view_layer = context.scene.view_layers[context.scene.lm_initial_view_layer]

		context.scene.view_layers[context.scene.lm_initial_view_layer].use = False

		asset_view_layers = {}
		if path.isdir(folder_src):
			subfolders = [path.join(folder_src, f,) for f in os.listdir(folder_src) if path.isdir(os.path.join(folder_src, f))]
			
			for subfolder in subfolders:
				bpy.ops.wm.redraw_timer(type='DRAW', iterations=1)
				mesh_files = [path.join(subfolder, f) for f in os.listdir(subfolder) if path.isfile(os.path.join(subfolder, f)) and path.splitext(f)[1].lower() in V.LM_COMPATIBLE_MESH_FORMAT.keys()]
				json_files = [path.join(subfolder, f) for f in os.listdir(subfolder) if path.isfile(os.path.join(subfolder, f)) and path.splitext(f)[1].lower() == '.json']
				texture_files = {}
				mesh_names = [path.basename(path.splitext(t)[0]) for t in mesh_files]

				asset_name = path.basename(subfolder)
				pretty = '---------------------'

				for c in asset_name:
					pretty += '-'

				log.info('----------------------------------------------------------' + pretty)
				log.info('----------------------------- Processing Asset "{}" -----------------------------'.format(path.basename(subfolder)))
				log.info('----------------------------------------------------------' + pretty)

				for m in mesh_names:
					try:
						texture_files[m] = [path.join(subfolder, m, t) for t in os.listdir(path.join(subfolder, m)) if path.isfile(os.path.join(subfolder, m, t)) and path.splitext(t)[1].lower() in V.LM_COMPATIBLE_TEXTURE_FORMAT.keys()]
						for mesh, textures in texture_files.items():
							log.info('{} texture files found for mesh {}'.format(len(textures), mesh))
							for t in textures:
								log.info(' 		{} '.format(t))
					except FileNotFoundError as e:
						texture_files[m] = []
						log.warning('folder dosn\'t exist in "{}"'.format(subfolder))
				asset_name = path.basename(subfolder)

				curr_asset = A.BpyAsset(context, mesh_files, texture_files, json_files)

				# To avoid import asset that doesn't match naming convention
				skip = False
				a_nc = curr_asset.asset_naming_convention
				kw_nc = N.NamingConvention(context, curr_asset.asset_name, context.scene.lm_asset_naming_convention)
				keywords = '\n'
				for keyword in a_nc['keywords']:
					keywords += keyword + '\n'
					if keyword not in a_nc.keys() and keyword not in kw_nc.optionnal_words:
						skip = True
						break
				
				if skip:
					log.warning('Asset "{}" is not valid.\n		Skipping file'.format(asset_name))
					log.warning(keywords)
					log.store_failure('Asset "{}" is not valid.\n		Skipping file'.format(asset_name))
					continue

				# Import new asset
				if asset_name not in bpy.data.collections and asset_name not in context.scene.lm_asset_list:
					curr_asset.import_asset()
					H.set_active_collection(context, asset_collection.name)
					updated = True
					log.store_success('Asset "{}" imported successfully'.format(asset_name))
				# Update Existing asset
				else:
					updated = curr_asset.update_asset()
					H.set_active_collection(context, asset_collection.name)
				# Assign material to meshes if any change on the asset
				if updated:
					first = True
					for mesh_name in curr_asset.asset.keys():
						
						for mat in curr_asset.asset[mesh_name][1]:
							try:
								if len(curr_asset.asset[mesh_name][1].keys()) == 0:
									log.warning('Mesh "{}" have no material applied to it \n	Applying generic material'.format(mesh_name))
									curr_asset.feed_material(curr_asset, context.scene.lm_asset_list[curr_asset.asset_name].material_list[mat].material)
								else:
									log.info('Applying material "{}" to mesh "{}"'.format(mat, mesh_name))
									curr_asset.feed_material(curr_asset, context.scene.lm_asset_list[curr_asset.asset_name].material_list[mat].material, curr_asset.asset[mesh_name][1][mat])
							except KeyError as k:
								log.warning('{}'.format(k))
								if first:
									log.success.pop()
								log.store_failure('Asset "{}" failed assign material "{}" with mesh "{}" :\n{}'.format(asset_name, mat, mesh_name, k))
								first = False

				del updated

				curr_asset_view_layer = H.get_layer_collection(context.view_layer.layer_collection, curr_asset.asset_name)
				# Store asset colection view layer
				asset_view_layers[curr_asset_view_layer.name] = curr_asset_view_layer
				context.scene.lm_asset_list[curr_asset_view_layer.name].view_layer = curr_asset_view_layer.name
				# Hide asset in Global View Layer
				curr_asset_view_layer.hide_viewport = True
			
			# create View Layers for each Assets
			for name in asset_view_layers.keys():
				if name not in context.scene.view_layers:
					bpy.ops.scene.view_layer_add()
					context.window.view_layer.name = name
				else:
					context.window.view_layer = context.scene.view_layers[name]

				for n, _ in asset_view_layers.items():
					if name != n and name != context.scene.lm_render_collection.name:
						curr_asset_view_layer = H.get_layer_collection(context.view_layer.layer_collection, n)
						curr_asset_view_layer.exclude = True

						context.window.view_layer = context.scene.view_layers[name]
						context.view_layer.use_pass_combined = False
						context.view_layer.use_pass_z = False

			
		# Set the global View_layer active
		context.window.view_layer = context.scene.view_layers[context.scene.lm_initial_view_layer]

		self.renumber_assets(context)

		log.info('')
		log.info('----------------------------------------------------------')
		log.info('----------------------------------------------------------')
		log.info('----------------------------------------------------------')
		log.info('')

		log.info('Import/Update Completed with {} success and {} failure'.format(len(log.success),len(log.failure)))
		for s in log.success:
			log.info('{}'.format(s))
		for f in log.failure:
			log.info('{}'.format(f))

		self.report({'INFO'}, 'Lineup Maker : Import/Update Completed')

		return {'FINISHED'}

	def renumber_assets(self, context):
		asset_name_list = [a.name for a in context.scene.lm_asset_list]
		asset_name_list.sort()

		for number,name in enumerate(asset_name_list):
			context.scene.lm_asset_list[name].asset_number = number + 1


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
		
		self.set_rendering_camera(context, asset)

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

	def set_rendering_camera(self, context, asset):
		cam = context.scene.lm_default_camera
		naming_convention = N.NamingConvention(context, asset.name, context.scene.lm_asset_naming_convention)

		for camera_keyword in context.scene.lm_cameras:
			match = True
			for keyword in camera_keyword.keywords:
				if naming_convention.naming_convention[keyword.keyword] != keyword.keyword_value.lower():
					match = False
					break
			
			if match:		
				cam = camera_keyword.camera
				break

		context.scene.camera = bpy.data.objects[cam.name]
		asset.render_camera = cam.name


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

	def set_rendering_camera(self, context, asset):
		cam = context.scene.lm_default_camera
		naming_convention = N.NamingConvention(context, asset.name, context.scene.lm_asset_naming_convention)

		for camera_keyword in context.scene.lm_cameras:
			match = True
			for keyword in camera_keyword.keywords:
				if naming_convention.naming_convention[keyword.keyword] != keyword.keyword_value.lower():
					match = False
					break
			
			if match:		
				cam = camera_keyword.camera
				break

		context.scene.camera = bpy.data.objects[cam.name]

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

	def execute(self, context):
		context.scene.lm_render_path

		need_update_list = [a for a in context.scene.lm_asset_list] + [ a for a in context.scene.lm_render_queue]

		for asset in need_update_list:
			self.report({'INFO'}, 'Lineup Maker : Refresh rendreing status for : "{}"'.format(asset.name))
			rendered_asset = path.join(context.scene.lm_render_path, asset.name)
			asset_path = path.join(context.scene.lm_asset_path, asset.name)
			composite_path = path.join(context.scene.lm_render_path, V.LM_FINAL_COMPOSITE_FOLDER_NAME, '{}{}.jpg'.format(asset.name, V.LM_FINAL_COMPOSITE_SUFFIX))

			if path.isdir(asset_path):
				asset.asset_path = asset_path

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
					
					asset.render_camera = self.get_cameraName_from_render(context, asset, rendered_files[0])
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

		return {'FINISHED'}

	def get_cameraName_from_render(self, context, asset, render_filename):
		word_pattern = re.compile(r'({0}{1})([a-zA-Z_]+){1}([0-9]+)'.format(asset.name, context.scene.lm_separator), re.IGNORECASE)
		groups = word_pattern.finditer(render_filename)
		for g in groups:
			return g.group(2)

class LM_OP_ExportSelectedAsset(bpy.types.Operator):
	bl_idname = "scene.lm_export_selected_asset"
	bl_label = "Lineup Maker: Export selected mesh to asset folder"
	bl_options = {'REGISTER', 'UNDO'}

	export_path = ''

	@classmethod
	def poll(cls, context):
		object_types = [o.type for o in context.selected_objects]
		return len(object_types) and 'MESH' in object_types and len(context.scene.lm_exported_asset_name)

	def execute(self, context):
		self.report({'INFO'}, 'Lineup Maker : Exporting selected objects to asset folder')
		self.json_data = []
		self.export_path = path.join(context.scene.lm_asset_path, context.scene.lm_exported_asset_name)

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
			bpy.ops.export_scene.fbx(filepath=export_filename, use_selection=True, bake_anim=False)

		self.write_json(context)

		bpy.ops.scene.lm_openfolder(folder_path=self.export_path)

		
		return {'FINISHED'}
	
	def copy_textures(self, context, source, destination):
		for mesh, textures in source.items():
			destination_path = path.join(destination, mesh)
			H.create_folder_if_neeed(destination_path)
			for t in textures:
				subprocess.call("xcopy {} {}".format(t, destination_path))

	
	def get_textures(self, context):
		texture_list = {}
		scn = context.scene
		for o in context.selected_objects:
			material_slots = o.material_slots
			name = o.name
			stats = S.Stats(o)
			json = {'name':name,
					'HDStatus':getattr(V.Status, scn.lm_exported_hd_status).value, 
					'LDStatus':getattr(V.Status, scn.lm_exported_ld_status).value,
					'BakingStatus':getattr(V.Status, scn.lm_exported_baking_status).value,
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
							json['materials'][-1]['textures'].append({'file':path.basename(t.image.filepath), 'channel':channel})
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

		