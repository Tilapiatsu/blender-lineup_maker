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

	def execute(self, context):
		context.scene.render.film_transparent = True

		for asset in context.scene.lm_asset_list:
			render_path, render_filename = self.get_render_path(context, asset.name)

			# Set  need_render status for each assets
			need_render = True
			if not context.scene.lm_force_render:
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
		
		need_render_asset = [a for a in context.scene.lm_asset_list if a.need_render]
		
		self.clear_composite_tree(context)

		composite_nodes = {}

		context.window_manager.progress_begin(0,len(need_render_asset))

		for i, asset in enumerate(need_render_asset):
			render_path, render_filename = self.get_render_path(context, asset.name)

			asset.need_render = True
			asset.render_path = render_path

			# switch to the proper view_layer
			context.window.view_layer = context.scene.view_layers[asset.name]

			output_node = self.build_output_nodegraph(context, i, asset)
			
			for frame in range(context.scene.frame_start, context.scene.frame_end + 1):
				print('Lineup Maker : Rendering asset "{}" | Frame {}' .format(asset.view_layer, str(frame).zfill(4)))
				self.report({'INFO'}, 'Lineup Maker : Rendering asset "{}" | Frame {}' .format(asset.view_layer, str(frame).zfill(4)))
				context.scene.frame_set(frame)
				
				bpy.context.scene.render.filepath = render_filename + str(frame).zfill(4)
				bpy.ops.render.render(write_still=False, layer=asset.view_layer)
				# bpy.ops.wm.redraw_timer(type='DRAW_WIN_SWAP', iterations=1)

				asset.need_render = False
				asset.rendered = True
			
			output_node.mute = True

			composite_nodes[asset.name] = self.build_composite_nodegraph(context, i, asset)
			context.window_manager.progress_update(i)

		for node in composite_nodes.values():
			node.mute = False
		
		bpy.context.scene.render.filepath = render_filename
		bpy.ops.render.render(write_still=False)


		self.revert_need_render(context)

		# Set the global View_layer active
		context.window.view_layer = context.scene.view_layers[context.scene.lm_initial_view_layer]
		context.window_manager.progress_end()
		return {'FINISHED'}

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

		location = (0, -1000 * index)
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
		out.mute = True

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