import bpy
import os,time, math
from os import path
from . import variables as V
from . import helper as H
from . import asset_format as A
from . import naming_convention as N

class LM_OP_ImportAssets(bpy.types.Operator):
	bl_idname = "scene.lm_importassets"
	bl_label = "Lineup Maker: Import all assets from source folder"
	bl_options = {'REGISTER', 'UNDO'}

	def execute(self, context):
		folder_src = bpy.path.abspath(context.scene.lm_asset_path)

		H.set_active_collection(context, V.LM_MASTER_COLLECTION)
		asset_collection, _ = H.create_asset_collection(context, V.LM_ASSET_COLLECTION)
		H.set_active_collection(context, asset_collection.name)
		
		object_list = asset_collection.objects

		# Store the Global View_Layer
		context.scene.lm_initial_view_layer = context.window.view_layer.name
		context.scene.view_layers[context.scene.lm_initial_view_layer].use = False

		asset_view_layers = {}
		if path.isdir(folder_src):
			subfolders = [path.join(folder_src, f,) for f in os.listdir(folder_src) if path.isdir(os.path.join(folder_src, f))]
			for subfolder in subfolders:
				mesh_files = [path.join(subfolder, f) for f in os.listdir(subfolder) if path.isfile(os.path.join(subfolder, f)) and path.splitext(f)[1].lower() in V.LM_COMPATIBLE_MESH_FORMAT.keys()]
				json_files = [path.join(subfolder, f) for f in os.listdir(subfolder) if path.isfile(os.path.join(subfolder, f)) and path.splitext(f)[1].lower() == '.json']
				texture_files = {}
				mesh_names = [path.basename(path.splitext(t)[0]) for t in mesh_files]
				for m in mesh_names:
					try:
						texture_files[m] = [path.join(subfolder, m, t) for t in os.listdir(path.join(subfolder, m)) if path.isfile(os.path.join(subfolder, m, t)) and path.splitext(t)[1].lower() in V.LM_COMPATIBLE_TEXTURE_FORMAT.keys()]
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
				bpy.ops.scene.view_layer_add()
				context.window.view_layer.name = name

				for n, _ in asset_view_layers.items():
					if name != n and name != context.scene.lm_render_collection.name:
						curr_asset_view_layer = H.get_layer_collection(context.view_layer.layer_collection, n)
						curr_asset_view_layer.exclude = True

						context.window.view_layer = context.scene.view_layers[name]
						context.view_layer.use_pass_combined = False
						context.view_layer.use_pass_z = False

			
			# Set the global View_layer active
			context.window.view_layer = context.scene.view_layers[context.scene.lm_initial_view_layer]

		return {'FINISHED'}

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

	def pre(self, dummy):
		self.rendering = True
		self.report({'INFO'}, "Lineup Maker : Rendering '{}'".format(os.path.join(self.need_render_asset[0].render_path, self.need_render_asset[0].name)))
		
	def post(self, dummy):
		if self.remaining_frames <= 1:
			asset = self.need_render_asset[0]

			self.composite_node = self.build_composite_nodegraph(self.context, self.asset_number, asset)

			asset.need_render = False
			asset.rendered = True
		else:
			self.remaining_frames -= 1

	def cancelled(self, dummy):
		self.stop = True

	def register_render_handler(self):
		bpy.app.handlers.render_pre.append(self.pre)
		bpy.app.handlers.render_post.append(self.post)
		bpy.app.handlers.render_cancel.append(self.cancelled)
		self._timer = bpy.context.window_manager.event_timer_add(0.5, window=bpy.context.window)

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

		self.shots = [ o.name+'' for o in scene.lm_render_collection.all_objects.values() if o.type=='CAMERA' and o.visible_get() == True ]

		if len(self.shots) < 0:
			self.report({"WARNING"}, 'No cameras defined')
			return {"FINISHED"}        

		for asset in scene.lm_asset_list:
			render_path, render_filename = self.get_render_path(context, asset.name)

			# Set  need_render status for each assets
			need_render = True
			if not scene.lm_force_render:
				if asset.render_date:
					need_render = False
					rendered_files = os.listdir(render_path)
					if len(rendered_files) < self.get_current_frame_range():
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
				else:
					self.report({'INFO'}, "Lineup Maker : Render completed")

				return {"FINISHED"} 

			elif self.rendering and self.remaining_assets and self.composite_node is not None:
				self.unregister_render_handler()
				print('Lineup Maker : Rendering composited image of "{}"'.format(self.need_render_asset[0].name))
				
				bpy.ops.render.render(write_still=False)
				self.composite_node.mute = True
				
				self.composite_node = None
				self.need_render_asset.pop(0)
				self.remaining_frames = self.frame_range

				self.remaining_assets -= 1
				self.asset_number += 1

				self.rendering = False
				self.register_render_handler()

			elif self.rendering is False: 
				self.render(context)

		return {"PASS_THROUGH"}

	def render(self, context):
		scn = bpy.context.scene
		scn.camera = bpy.data.objects[self.shots[0]] 	

		scn.render.film_transparent = True

		# context.window_manager.progress_begin(0,len(need_render_asset))
		# self.remaining_assets = len(self.need_render_asset)
		asset = self.need_render_asset[0]

		render_path, render_filename = self.get_render_path(context, asset.name)

		asset.need_render = True
		asset.render_path = render_path

		# switch to the proper view_layer
		context.window.view_layer = scn.view_layers[asset.name]

		self.output_node = self.build_output_nodegraph(context, self.asset_number, asset)
		bpy.context.scene.render.filepath = render_filename + self.shots[0] + '_'
		self.output_node.mute = True

		self.context = context

		bpy.ops.render.render("INVOKE_DEFAULT", animation=True, write_still=False, layer=asset.view_layer)

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

		tree.links.new(rl.outputs[0], out.inputs[0])

		location = (location[0], location[1] - incr)
			
		print('Lineup Maker : Output Node graph built')

		return out

	def build_composite_nodegraph(self, context, index, asset):
		print('Lineup Maker : Generating composite nodegraph')
		tree = context.scene.node_tree
		nodes = tree.nodes

		location = (600, - 1000 * index)
		incr = 300

		composite_res = self.get_composite_resolution(context)
		render_res = (bpy.context.scene.render.resolution_x, bpy.context.scene.render.resolution_y)
		framecount = self.get_current_frame_range(context)

		composite_image = bpy.data.images.new(name='{}_composite'.format(asset.name), width=composite_res[0], height=composite_res[1])
		composite_image.generated_color = (0.1, 0.1, 0.1, 1)
		
		composite = nodes.new('CompositorNodeImage')
		composite.location = (location[0], location[1])
		composite.image = composite_image
		location = (location[0], location[1] - incr)

		mix = None

		files = os.listdir(asset.render_path)

		for i,f in enumerate(files):
			image = nodes.new('CompositorNodeImage')
			bpy.ops.image.open(filepath=os.path.join(asset.render_path, f), directory=asset.render_path, show_multiview=False)
			image.image = bpy.data.images[f]
			image.location = location

			location = (location[0] + incr/2, location[1])
			translate = nodes.new('CompositorNodeTranslate')
			translate.location = location
			translate.inputs[1].default_value = -composite_res[0]/2 + render_res[0] / 2 + ((i%(framecount/2)) * render_res[0])
			translate.inputs[2].default_value = composite_res[1]/2 - render_res[1] / 2 - composite_res[2] - (math.floor(i/framecount*2) * render_res[1])

			tree.links.new(image.outputs[0], translate.inputs[0])

			new_mix = nodes.new('CompositorNodeAlphaOver')
			new_mix.location = (location[0] + incr/2, location[1])
			new_mix.use_premultiply = True

			if mix is not None:
				tree.links.new(mix.outputs[0], new_mix.inputs[1])
				tree.links.new(translate.outputs[0], new_mix.inputs[2])
			else:
				tree.links.new(translate.outputs[0], new_mix.inputs[2])
				tree.links.new(composite.outputs[0], new_mix.inputs[1])

			location = (location[0] + incr, location[1] - incr)

			mix = new_mix
		
		out = nodes.new('CompositorNodeOutputFile')
		out.location = (location[0] + incr, location[1])
		out.file_slots[0].path = asset.name + '_composite_'
		out.base_path = path.abspath(path.join(asset.render_path, os.pardir))
		# out.mute = True

		if mix:
			tree.links.new(mix.outputs[0], out.inputs[0])

		location = (location[0], location[1] - 100)
		
		asset.rendered = False
		
		return out

	def get_composite_resolution(self, context):
		fc = context.scene.frame_end-context.scene.frame_start
		res_x = bpy.context.scene.render.resolution_x
		res_y = bpy.context.scene.render.resolution_y
		margin = math.ceil(res_y/3)

		x = math.ceil(fc/2) * res_x
		y = math.floor(fc/2) * res_y + margin

		return (x, y, margin)

	def get_render_path(self, context, asset_name):
		render_path = os.path.abspath(os.path.join(os.path.abspath(context.scene.lm_render_path), asset_name))
		render_filename = render_path + '\\{}_'.format(asset_name)
		if not os.path.exists(render_path):
			os.makedirs(render_path)
		
		return render_path, render_filename
	
	def revert_need_render(self, context):
		need_render_asset = [a for a in context.scene.lm_asset_list if a.need_render]

		for asset in need_render_asset:
			asset.need_render = False
			asset.render_date = time.time()
			asset.rendered = False
		
	def get_current_frame_range(self, context):
		return context.scene.frame_end + 1 - context.scene.frame_start

class LM_OP_CompositeRenders(bpy.types.Operator):
	bl_idname = "scene.lm_compositerenders"
	bl_label = "Lineup Maker: composite all rendered assets"
	bl_options = {'REGISTER', 'UNDO'}

	def execute(self, context):
		
		
		return {'FINISHED'}