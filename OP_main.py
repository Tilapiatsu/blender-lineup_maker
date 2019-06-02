import bpy
import os, time, math
from fpdf import FPDF
from os import path
from . import variables as V
from . import helper as H
from . import asset_format as A
from . import naming_convention as N
from . import compositing as C


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
				self.report({'INFO'}, 'Lineup Maker : Lineup Updated correctly ')
				return {"FINISHED"}

		return {"PASS_THROUGH"}

class LM_OP_ImportAssets(bpy.types.Operator):
	bl_idname = "scene.lm_importassets"
	bl_label = "Lineup Maker: Import all assets from source folder"
	bl_options = {'REGISTER', 'UNDO'}

	def execute(self, context):
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
				for m in mesh_names:
					try:
						texture_files[m] = [path.join(subfolder, m, t) for t in os.listdir(path.join(subfolder, m)) if path.isfile(os.path.join(subfolder, m, t)) and path.splitext(t)[1].lower() in V.LM_COMPATIBLE_TEXTURE_FORMAT.keys()]
						for mesh, textures in texture_files.items():
							print('Lineup Maker : {} texture files found for mesh {}'.format(len(textures), mesh))
							for t in textures:
								print('Lineup Maker : 		{} '.format(t))
					except FileNotFoundError as e:
						texture_files[m] = []
						print('Lineup Maker : folder dosn\'t exist in "{}"'.format(subfolder))
				asset_name = path.basename(subfolder)
				curr_asset = A.BpyAsset(context, mesh_files, texture_files, json_files)
				
				if asset_name not in bpy.data.collections and asset_name not in context.scene.lm_asset_list:
					curr_asset.import_asset()
					H.set_active_collection(context, asset_collection.name)
				else:
					curr_asset.update_asset()
					H.set_active_collection(context, asset_collection.name)

				assigned = False
				for mesh_name in curr_asset.asset.keys():
					for mat in context.scene.lm_asset_list[curr_asset.asset_name].mesh_list[mesh_name].material_list:
						if len(curr_asset.asset[mesh_name][1].keys()) == 0:
							curr_asset.feed_material(mat.material)
							continue
						for t in curr_asset.asset[mesh_name][1].keys():
							tnc = N.NamingConvention(context, t, context.scene.lm_texture_naming_convention)
							mnc = N.NamingConvention(context, mat.name.lower(), context.scene.lm_texture_naming_convention)

							if tnc == mnc:
								curr_asset.feed_material(mat.material, curr_asset.asset[mesh_name][1][t])
								assigned = True
								break
						else:
							if not assigned:
								print('Lineup Maker : No Texture found for material "{}"'.format(mat.name))

				del assigned

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

		return {'FINISHED'}

	def renumber_assets(self, context):
		asset_name_list = [a.name for a in context.scene.lm_asset_list]
		asset_name_list.sort()

		for number,name in enumerate(asset_name_list):
			context.scene.lm_asset_list[name].asset_number = number + 1

class LM_OP_RenderAssets(bpy.types.Operator):
	bl_idname = "scene.lm_renderassets"
	bl_label = "Lineup Maker: Render all assets in the scene"
	bl_options = {'REGISTER', 'UNDO'}
	
	_timer = None
	shots = None
	stop = None
	frame_range = None
	remaining_frames = None
	remaining_assets = None
	rendering = None
	disablerbbutton = False
	need_render_asset = None
	asset_number = 0
	composite_node = None
	output_node = None
	context = None
	initial_view_layer = None
	rendered_assets = []
	render_filename = ''
	render_path = ''

	composite_filepath = ''
	chapter = ''
	chapters = []

	def pre(self, dummy):
		self.rendering = True
		self.report({'INFO'}, "Lineup Maker : Rendering '{}'".format(os.path.join(self.need_render_asset[0].render_path, self.need_render_asset[0].name)))
		
	def post(self, dummy):
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

	def cancelled(self, dummy):
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
		self.stop = False
		self.rendering = False
		scene = bpy.context.scene
		wm = bpy.context.window_manager

		# self.shots = [ o.name+'' for o in scene.lm_render_collection.all_objects.values() if o.type=='CAMERA' and o.visible_get() == True ]

		if not context.scene.lm_default_camera:
			self.report({"WARNING"}, 'No Default cameras defined')
			return {"FINISHED"}        

		for asset in scene.lm_asset_list:
			render_path, render_filename = self.get_render_path(context, asset.name)

			# Set  need_render status for each assets
			need_render = True
			if not scene.lm_force_render:
				if asset.render_date:
					need_render = False
					rendered_files = os.listdir(render_path)
					if len(rendered_files) < self.get_current_frame_range(context):
						need_render = True
					else:
						for f in os.listdir(render_path):
							if asset.render_date < asset.import_date:
								need_render = True
								break
				else:
					asset.need_render = True
			else:
				asset.need_render = True
		
		self.need_render_asset = [a for a in scene.lm_asset_list if a.need_render]
		self.remaining_assets = len(self.need_render_asset)
		self.asset_number = 0
		self.initial_view_layer = context.window.view_layer

		self.frame_range = self.get_current_frame_range(context)
		self.remaining_frames = self.frame_range
		
		self.clear_composite_tree(context)
		self.context = context

		self.register_render_handler()
		
		bpy.context.window_manager.modal_handler_add(self)

		return {"RUNNING_MODAL"}
	
	def modal(self, context, event):
		if event.type == 'TIMER':

			if True in (not self.need_render_asset, self.stop is True): 
				
				for asset in self.chapters:
					composite = C.LM_Composite_Image(context, asset)
					composite.composite_chapter()

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

			

			elif self.rendering  and self.composite_node is None and self.need_render_asset[0].need_render is False and self.need_render_asset[0].rendered is True:
				asset = self.need_render_asset[0]
				naming_convention = N.NamingConvention(context, asset.name, context.scene.lm_asset_naming_convention).naming_convention
				curr_chapter = naming_convention[context.scene.lm_chapter_name]
				composite = C.LM_Composite_Image(context, asset, self.asset_number)
				self.composite_node = composite.output
				if curr_chapter != self.chapter:
					self.chapters.append(asset)
					self.chapter = curr_chapter

			elif self.rendering and self.remaining_assets and self.composite_node is not None:
				self.unregister_render_handler()
				asset = self.need_render_asset[0]
				print('Lineup Maker : Rendering composited image of "{}"'.format(asset.name))
				
				bpy.ops.render.render(write_still=False)

				self.composite_node.mute = True
				
				self.composite_node = None

				asset.render_date = time.time()
				asset.need_write_info = True

				C.LM_Composite_Image(context, asset, self.asset_number).composite_asset_info()

				self.rendered_assets.append(asset)

				self.need_render_asset.pop(0)
				self.remaining_frames = self.frame_range

				self.remaining_assets -= 1
				self.asset_number += 1

				self.rendering = False
				
				self.register_render_handler()

			elif self.rendering is False and self.composite_node is None: 
				self.render(context)

		return {"PASS_THROUGH"}

	def render(self, context):
		scn = bpy.context.scene 	

		scn.render.film_transparent = True

		asset = self.need_render_asset[0]

		self.render_path, self.render_filename = self.get_render_path(context, asset.name)

		asset.need_render = True
		asset.render_path = self.render_path

		# switch to the proper view_layer
		context.window.view_layer = scn.view_layers[asset.name]
		
		self.set_rendering_camera(context, asset)

		self.output_node = self.build_output_nodegraph(context, self.asset_number, asset)
		bpy.context.scene.render.filepath = self.render_filename + context.scene.camera.name + '_'
		self.output_node.mute = True

		# self.context = context

		bpy.ops.render.render("INVOKE_DEFAULT", animation=True, write_still=False, layer=asset.view_layer)

	def print_render_log(self):
		self.report({'INFO'}, "Lineup Maker : {} assets rendered".format(len(self.rendered_assets)))
		for a in self.rendered_assets:
			self.report({'INFO'}, "Lineup Maker : {} rendered".format(a.name))

	def isolate_collection_visibility(self, context, collections):
		for asset in context.scene.lm_asset_list:
			try:
				view_layer = H.get_layer_collection(context.view_layer.layer_collection, collections[1])
				if asset.view_layer in collections:
					view_layer.exclude = False
				else:
					view_layer.exclude = True
			except KeyError as e:
				print('Lineup Maker : The collection "{}" doesn\'t exist' .format(asset.view_layer))
	
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
		out.file_slots[0].path = asset.name + '_'
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

	def get_curr_render_extension(self, context):
		return V.LM_OUTPUT_EXTENSION[bpy.context.scene.render.image_settings.file_format]

	def revert_need_render(self, context):
		need_render_asset = [a for a in context.scene.lm_asset_list if a.need_render]

		for asset in need_render_asset:
			asset.need_render = False
			asset.render_date = time.time()
			asset.rendered = False
		
	def get_current_frame_range(self, context):
		return context.scene.frame_end + 1 - context.scene.frame_start

	def set_rendering_camera(self, context, asset):
		cam = context.scene.lm_default_camera
		naming_convention = N.NamingConvention(context, asset.name, context.scene.lm_asset_naming_convention)

		for camera_keyword in context.scene.lm_cameras:
			
			if naming_convention.naming_convention[camera_keyword.keyword] == camera_keyword.keyword_value.lower():
				cam = camera_keyword.camera
				break

		context.scene.camera = bpy.data.objects[cam.name]

class LM_OP_CompositeRenders(bpy.types.Operator):
	bl_idname = "scene.lm_compositerenders"
	bl_label = "Lineup Maker: composite all rendered assets"
	bl_options = {'REGISTER', 'UNDO'}

	_timer = None
	stop = None
	compositing = None
	context = None
	need_compositing_asset = []
	composited_asset = []
	asset_number = 0
	info_written_asset = []
	chapter = ''
	chapters = []
	done = False

	def pre(self, dummy):
		self.compositing = True
		self.report({'INFO'}, "Lineup Maker : Rendering '{}'".format(os.path.join(self.need_compositing_asset[0].render_path, self.need_compositing_asset[0].name)))
		
	def post(self, dummy):
		self.composited_asset = self.need_compositing_asset
		self.need_compositing_asset = []
		self.compositing = False
		self.asset_number += 1

	def cancelled(self, dummy):
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
		self.stop = False
		self.compositing = False
		self.clear_composite_tree(context)
		self.context = context
		self.composited_asset = []
		self.need_compositing_asset = []

		for asset in context.scene.lm_asset_list:
			render_exist = True
			if len(asset.render_list):
				for render in asset.render_list:
					if not os.path.exists(render.render_filepath):
						render_exist = False
						break
			else:
				self.report({'WARNING'}, 'Lineup Maker : No render found for asset "{}"'.format(asset.name))
				render_exist = False

			if render_exist:
				self.need_compositing_asset.append(asset)

		if len(self.need_compositing_asset):
			for i,asset in enumerate(self.need_compositing_asset):
				C.LM_Composite_Image(context, asset, self.asset_number).output
				asset.need_write_info = False
				asset.info_written = False

			self.register_render_handler()
			
			bpy.context.window_manager.modal_handler_add(self)

			return {"RUNNING_MODAL"}
		else:
			self.report({'WARNING'}, 'Lineup Maker : No render found for any assets')
			return {"FINISHED"}

	def modal(self, context, event):
		if event.type == 'TIMER':

			if True in (not self.need_compositing_asset and self.done, self.stop is True): 

				self.unregister_render_handler()
				bpy.context.window_manager.event_timer_remove(self._timer)

				for asset in self.chapters:
					composite = C.LM_Composite_Image(context, asset, self.asset_number)
					composite.composite_chapter()

				if self.stop:
					self.report({'WARNING'}, "Lineup Maker : Compositing cancelled by user")
					self.print_render_log()
					
				else:
					self.report({'INFO'}, "Lineup Maker : Compositing completed")
					self.print_render_log()

				self.composited_asset = []
				return {"FINISHED"} 
			

			elif self.compositing is False and len(self.composited_asset):
				for asset in context.scene.lm_asset_list:
					naming_convention = N.NamingConvention(context, asset.name, context.scene.lm_asset_naming_convention).naming_convention
					curr_chapter = naming_convention[context.scene.lm_chapter_name]
					composite = C.LM_Composite_Image(context, asset, self.asset_number)
					composite.composite_asset_info()
					if curr_chapter != self.chapter:
						self.chapters.append(asset)
						self.chapter = curr_chapter
					asset.info_written = True
					self.info_written_asset.append(asset)
				
				self.done = True


			elif self.compositing is False and not len(self.composited_asset): 
				bpy.ops.render.render("INVOKE_DEFAULT", write_still=False)

		return {"PASS_THROUGH"}

	def print_render_log(self):
		self.report({'INFO'}, "Lineup Maker : {} assets composited".format(len(self.composited_asset)))
		for a in self.composited_asset:
			self.report({'INFO'}, "Lineup Maker : {} composited".format(a.name))

	def get_current_frame_range(self, context):
		return context.scene.frame_end + 1 - context.scene.frame_start

	def clear_composite_tree(self, context):
		tree = context.scene.node_tree
		nodes = tree.nodes
		nodes.clear()

class LM_OP_ExportPDF(bpy.types.Operator):
	bl_idname = "scene.lm_export_pdf"
	bl_label = "Lineup Maker: Export PDF in the Render Path"
	bl_options = {'REGISTER', 'UNDO'}

	def execute(self, context):
		composite = C.LM_Composite_Image(context, context.scene.lm_asset_list[0].name)
		res = composite.res
		orientation = 'P' if res[1] < res[0] else 'L'
		pdf = FPDF(orientation, 'pt', (res[0], res[1]))
		
		asset_name_list = [a.name for a in context.scene.lm_asset_list]
		asset_name_list.sort()
		for name in asset_name_list:
			asset = context.scene.lm_asset_list[name]
			if asset.raw_composite_filepath != '':
				pdf.add_page()

				composite = C.LM_Composite_Image(context, asset)
				composite.convert_to_jpeg(asset.raw_composite_filepath, asset.final_composite_filepath, 80)

				pdf.image(name=asset.final_composite_filepath, x=0, y=0, w=res[0], h=res[1])
				composite.composite_pdf_asset_info(pdf)
		
		pdf_file = path.join(context.scene.lm_render_path, 'lineup.pdf')
		pdf.output(pdf_file)

		self.report({'INFO'}, 'Lineup Maker : PDF File exported correctly : "{}"'.format(pdf_file))

		return {'FINISHED'}