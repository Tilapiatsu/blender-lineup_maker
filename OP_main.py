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
		global_view_layer = context.window.view_layer
		context.scene.view_layers[global_view_layer.name].use = False

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
			
			# # create View Layers for each Assets
			# for name in asset_view_layers.keys():
			# 	bpy.ops.scene.view_layer_add()
			# 	context.window.view_layer.name = name

			# 	for n, _ in asset_view_layers.items():
			# 		if name != n and name != context.scene.lm_render_collection.name:
			# 			curr_asset_view_layer = H.get_layer_collection(context.view_layer.layer_collection, n)
			# 			curr_asset_view_layer.exclude = True

			# 			context.window.view_layer = context.scene.view_layers[name]
			# 			context.view_layer.use_pass_combined = False
			# 			context.view_layer.use_pass_z = False

			
			# Set the global View_layer active
			context.window.view_layer = global_view_layer

		return {'FINISHED'}

class LM_OP_RenderAssets(bpy.types.Operator):
	bl_idname = "scene.lm_renderassets"
	bl_label = "Lineup Maker: Render all assets in the scene"
	bl_options = {'REGISTER', 'UNDO'}

	def execute_old(self, context):
		context.scene.render.film_transparent = True
		

		for asset in context.scene.lm_asset_list:
			render_path, _ = self.get_render_path(context, asset.name)

			need_render = True
			if asset.render_date:
				need_render = False
				rendered_files = os.listdir(render_path)
				if len(rendered_files) < context.scene.frame_end-context.scene.frame_start:
					need_render = True
				else:
					for f in os.listdir(render_path):
						if asset.render_date < asset.import_date:
							need_render = True
							break
						
			if need_render or context.scene.lm_force_render:
				asset.need_render = True
				asset.render_path = render_path

		self.build_output_nodegraph(context)

		bpy.ops.render.render(animation=True)

		self.build_composite_nodegraph(context)
		self.revert_need_render(context)
		return {'FINISHED'}

	def execute(self, context):
		context.scene.render.film_transparent = True
		
		for asset in context.scene.lm_asset_list:
			render_path, render_filename = self.get_render_path(context, asset.name)

			need_render = True
			if asset.render_date:
				need_render = False
				rendered_files = os.listdir(render_path)
				if len(rendered_files) < context.scene.frame_end-context.scene.frame_start:
					need_render = True
				else:
					for f in os.listdir(render_path):
						if asset.render_date < asset.import_date:
							need_render = True
							break
						
			if need_render or context.scene.lm_force_render:
				asset.need_render = True
				asset.render_path = render_path

				for frame in range(context.scene.frame_start, context.scene.frame_end):
					print('Lineup Maker : Rendering asset "{}" | Frame {}' .format(asset.view_layer, frame))
					context.scene.frame_set(frame)

					self.isolate_collection_visibility(context, [V.LM_ASSET_COLLECTION, asset.name])
					bpy.context.scene.render.filepath = render_filename + str(frame).zfill(4)
					bpy.ops.render.render(write_still=True)

				self.build_composite_nodegraph(context)

		self.revert_need_render(context)
		return {'FINISHED'}
	
	def isolate_collection_visibility(self, context, collections):
		for asset in context.scene.lm_asset_list:
			try:
				bpy.data.collections[asset.view_layer]
			except KeyError as e:
				print('Lineup Maker : The collection "{}" doesn\'t exist' .format(asset.view_layer))

				if asset.view_layer in collections:
					bpy.data.collections[asset.view_layer].exclude = False
				else:
					bpy.data.collections[asset.view_layer].exclude = True


	def build_output_nodegraph(self, context):
		tree = context.scene.node_tree
		nodes = tree.nodes

		nodes.clear()

		location = (0, 0)
		incr = 300

		need_render_asset = [a for a in context.scene.lm_asset_list if a.need_render]

		for asset in need_render_asset:

			rl = nodes.new('CompositorNodeRLayers')
			rl.location = location
			rl.layer = asset.view_layer
			of = nodes.new('CompositorNodeOutputFile')

			sub_location = (location[0] + incr, location[1])
			
			of.location = sub_location

			of.base_path = asset.render_path
			of.file_slots[0].path = asset.name + '_'

			tree.links.new(rl.outputs[0], of.inputs[0])

			location = (location[0], location[1] - incr)
			

		print('Lineup Maker : Output Node graph built')

	def build_composite_nodegraph(self, context):
		tree = context.scene.node_tree
		nodes = tree.nodes

		location = (600, 0)
		incr = 300

		need_render_asset = [a for a in context.scene.lm_asset_list if a.need_render]

		composite_res = self.get_composite_resolution(context)

		for asset in need_render_asset:
			composite = bpy.data.images.new(name='{}_composite'.format(asset.name), width=composite_res[0], height=composite_res[1])
			for f in os.listdir(asset.render_path):
				image = nodes.new('CompositorNodeImage')
				bpy.ops.image.open(filepath=os.path.join(asset.render_path, f), directory=asset.render_path, show_multiview=False)
				image.image = bpy.data.images[f]
				image.location = location

				location = (location[0], location[1] - 300)

	def get_composite_resolution(self, context):
		fc = context.scene.frame_end-context.scene.frame_start
		res_x = bpy.context.scene.render.resolution_x
		res_y = bpy.context.scene.render.resolution_y
		margin = math.ceil(res_y/3)

		x = math.ceil(fc/2) * res_x
		y = math.floor(fc/2) * res_y + margin

		return (x, y)
		

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


class LM_OP_CompositeRenders(bpy.types.Operator):
	bl_idname = "scene.lm_compositerenders"
	bl_label = "Lineup Maker: composite all rendered assets"
	bl_options = {'REGISTER', 'UNDO'}

	def execute(self, context):
		
		
		return {'FINISHED'}