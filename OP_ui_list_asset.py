import bpy
from os import path
from . import helper as H
from . import logger as L

def get_assets(context, name):
	H.renumber_assets(context)
	assets = context.scene.lm_asset_list
	if name in context.scene.lm_asset_list:
		idx = context.scene.lm_asset_list[name].asset_index
	else:
		idx = 0

	active = assets[idx] if assets else None

	return idx, assets, active

def remove_asset(self, context, asset, index, remove=True):
	self.report({'INFO'},'Remove {}'.format(asset.name))
	try:
		context.window.view_layer = context.scene.view_layers[asset.view_layer]
	except KeyError as e:
		print(e)

	if context.scene.lm_asset_list[asset.name].collection:
		H.remove_asset(context, asset.name, False)

	try:
		context.scene.view_layers.remove(context.scene.view_layers[context.scene.lm_asset_list[asset.name].view_layer])
	except KeyError as e:
		print(e)

	if remove:
		print("Removing asset : {}".format(context.scene.lm_asset_list[index].name))
		context.scene.lm_asset_list.remove(index)
		context.scene.lm_asset_list_idx = index - 1 if index else 0

		H.remove_bpy_struct_item(context.scene.lm_last_render_list, asset.name)

	
	H.renumber_assets(context)
	idx, _, _ = get_assets(context, asset.name)

	
	


class LM_UI_MoveAsset(bpy.types.Operator):
	bl_idname = "scene.lm_move_asset"
	bl_label = "Move Keyword"
	bl_options = {'REGISTER', 'UNDO'}
	bl_description = "Move Camera keyword Name up or down.\nThis controls the position in the Menu."

	direction: bpy.props.EnumProperty(items=[("UP", "Up", ""), ("DOWN", "Down", "")])
	asset_name : bpy.props.StringProperty(name="Asset Name", default="", description='Name of the asset to move')

	def execute(self, context):
		idx, asset, _ = get_assets(context, self.asset_name)

		if self.direction == "UP":
			nextidx = max(idx - 1, 0)
		elif self.direction == "DOWN":
			nextidx = min(idx + 1, len(asset) - 1)

		asset.move(idx, nextidx)
		context.scene.lm_asset_list_idx = nextidx

		return {'FINISHED'}


class LM_UI_ClearAssetList(bpy.types.Operator):
	bl_idname = "scene.lm_clear_asset_list"
	bl_label = "Clear All Assets"
	bl_options = {'REGISTER', 'UNDO'}
	bl_description = "Clear All Assets."

	@classmethod
	def poll(cls, context):
		return context.scene.lm_asset_list

	def execute(self, context):
		for i,asset in enumerate(context.scene.lm_asset_list):
			remove_asset(self, context, asset, 0, remove=False)
		
		context.scene.lm_asset_list.clear()

		return {'FINISHED'}


class LM_UI_RemoveAsset(bpy.types.Operator):
	bl_idname = "scene.lm_remove_asset"
	bl_label = "Remove Selected Asset"
	bl_options = {'REGISTER', 'UNDO'}
	bl_description = "Remove selected Asset."

	asset_name : bpy.props.StringProperty(name="Asset Name", default="", description='Name of the asset to remove')

	@classmethod
	def poll(cls, context):
		return context.scene.lm_asset_list

	def execute(self, context):
		idx, asset, _ = get_assets(context, self.asset_name)

		remove_asset(self, context, asset[self.asset_name], idx)
		H.remove_bpy_struct_item(context.scene.lm_render_queue, self.asset_name)

		return {'FINISHED'}


class LM_UI_OpenRenderFolder(bpy.types.Operator):
	bl_idname = "scene.lm_open_render_folder"
	bl_label = "Open Render Folder"
	bl_options = {'REGISTER', 'UNDO'}
	bl_description = "Open Render Folder"

	asset_name : bpy.props.StringProperty(name="Asset Name", default="", description='Name of the asset folder to Open')

	@classmethod
	def poll(cls, context):
		return context.scene.lm_asset_list

	def execute(self, context):
		bpy.ops.scene.lm_openfolder(folder_path=context.scene.lm_asset_list[self.asset_name].render_path)

		return {'FINISHED'}


class LM_UI_OpenAssetFolder(bpy.types.Operator):
	bl_idname = "scene.lm_open_asset_folder"
	bl_label = "Open Asset Folder"
	bl_options = {'REGISTER', 'UNDO'}
	bl_description = "Open Asset Folder"

	asset_name : bpy.props.StringProperty(name="Asset Name", default="", description='Name of the asset folder to Open')

	@classmethod
	def poll(cls, context):
		return context.scene.lm_asset_list

	def execute(self, context):
		bpy.ops.scene.lm_openfolder(folder_path=context.scene.lm_asset_list[self.asset_name].asset_path)

		return {'FINISHED'}


class LM_UI_ShowAsset(bpy.types.Operator):
	bl_idname = "scene.lm_show_asset"
	bl_label = "Show Asset"
	bl_options = {'REGISTER', 'UNDO'}
	bl_description = "Show Asset"

	asset_name : bpy.props.StringProperty(name="Asset Name", default="", description='Name of the asset to show')

	@classmethod
	def poll(cls, context):
		return context.scene.lm_asset_list

	def execute(self, context):
		
		context.window.view_layer = context.scene.view_layers[self.asset_name]

		return {'FINISHED'}

class LM_UI_PrintAssetData(bpy.types.Operator):
	bl_idname = "scene.lm_print_asset_data"
	bl_label = "Print asset data"
	bl_options = {'REGISTER', 'UNDO'}
	bl_description = "Print all asset data in the scene"

	asset_name : bpy.props.StringProperty(name="Asset Name", default="", description='Name of the asset to print')
	asset = None

	@classmethod
	def poll(cls, context):
		return context.scene.lm_asset_list

	def invoke(self, context, event):
		idx, assets, _ = get_assets(context, self.asset_name)
		try:
			self.asset = assets[self.asset_name]
		except ValueError:
			self.report({'ERROR'}, 'Lineup Maker : The asset "{}" is not valid'.format(self.asset_name))
		wm = context.window_manager
		return wm.invoke_props_dialog(self, width=800)

	def execute(self, context):

		return {'FINISHED'}
	
	def draw(self, context):
		layout = self.layout
		col = layout.column()
		col.label(text='{} Datas'.format(self.asset_name))
		col.separator()

		if self.asset:
			col.label(text='render_date = {}'.format(self.asset.render_date))
			col.label(text='import_date = {}'.format(self.asset.import_date))
			col.label(text='mesh_list = {}'.format([m.name for m in self.asset.mesh_list]))
			col.label(text='material_list = {}'.format([m.name for m in self.asset.material_list]))
			col.label(text='texture_list = {}'.format([t.name for t in self.asset.texture_list]))
			col.label(text='view_layer = {}'.format(self.asset.view_layer))
			col.label(text='collection = {}'.format(self.asset.collection.name))
			col.label(text='need_render = {}'.format(self.asset.need_render))
			col.label(text='rendered = {}'.format(self.asset.rendered))
			col.label(text='need_composite = {}'.format(self.asset.need_composite))
			col.label(text='composited = {}'.format(self.asset.composited))
			col.label(text='asset_path = {}'.format(self.asset.asset_path))
			col.label(text='render_path = {}'.format(self.asset.render_path))
			col.label(text='render_camera = {}'.format(self.asset.render_camera))
			col.label(text='asset_folder_exists = {}'.format(self.asset.asset_folder_exists))
			col.label(text='raw_composite_filepath = {}'.format(self.asset.raw_composite_filepath))
			col.label(text='final_composite_filepath = {}'.format(self.asset.final_composite_filepath))
			col.label(text='render_list = {}'.format([r.render_filepath for r in self.asset.render_list]))
			col.label(text='need_write_info = {}'.format(self.asset.need_write_info))
			col.label(text='info_written = {}'.format(self.asset.info_written))
			col.label(text='asset_number = {}'.format(self.asset.asset_number))
			col.label(text='asset_index = {}'.format(self.asset.asset_index))
			col.label(text='hd_status = {}'.format(self.asset.hd_status))
			col.label(text='ld_status = {}'.format(self.asset.ld_status))
			col.label(text='baking_status = {}'.format(self.asset.baking_status))
			col.label(text='triangles = {}'.format(self.asset.triangles))
			col.label(text='vertices = {}'.format(self.asset.vertices))
			col.label(text='has_uv2 = {}'.format(self.asset.has_uv2))
			col.label(text='section = {}'.format(self.asset.section))
			col.label(text='from_file = {}'.format(self.asset.from_file))

		
