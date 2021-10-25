import bpy, shutil
import os
from os import path
from . import helper as H
from . import logger as L
from . import naming_convention as N


def get_assets(context, name):
	H.renumber_assets(context, context.scene.lm_import_list)
	assets = context.scene.lm_import_list
	if name in context.scene.lm_import_list:
		idx = context.scene.lm_import_list[name].asset_index
	else:
		idx = 0

	active = assets[idx] if assets else None

	return idx, assets, active

class LM_IU_RefreshImportList(bpy.types.Operator):
	bl_idname = "scene.lm_refresh_import_list"
	bl_label = "Refresh Import List"
	bl_options = {'REGISTER', 'UNDO'}
	bl_description = "Refresh Import List"

	@classmethod
	def poll(cls, context):
		return len(context.scene.lm_asset_path) and path.isdir(context.scene.lm_asset_path)
	
	def execute(self, context):
		folder_src = context.scene.lm_asset_path
		asset_folders = [path.join(folder_src, f,) for f in os.listdir(folder_src) if path.isdir(os.path.join(folder_src, f))]
		asset_folders_name = [path.basename(f) for f in asset_folders]
		for f in asset_folders:
			asset_name = path.basename(f)
			if asset_name not in context.scene.lm_import_list and asset_name not in context.scene.lm_asset_list:
				asset = context.scene.lm_import_list.add()
				asset.name = asset_name
				asset.asset_path = f
				asset.asset_folder_exists = True

				asset_nameing_convention = N.NamingConvention(context, asset_name, context.scene.lm_asset_naming_convention)
				asset.is_valid = asset_nameing_convention.is_valid
			

		for a in context.scene.lm_import_list:
			if a.name not in asset_folders_name or a.name in context.scene.lm_asset_list:
				H.remove_bpy_struct_item(context.scene.lm_import_list, a.name)

		return {'FINISHED'}

class LM_UI_RemoveAsseFolder(bpy.types.Operator):
	bl_idname = "scene.lm_remove_asset_folder"
	bl_label = "Remove Selected Asset Folder"
	bl_options = {'REGISTER', 'UNDO'}
	bl_description = "Remove selected Asset Folder."

	asset_name : bpy.props.StringProperty(name="Asset Name", default="", description='Name of the asset to remove')

	@classmethod
	def poll(cls, context):
		return context.scene.lm_import_list

	def invoke(self, context, event):
		wm = context.window_manager
		return wm.invoke_confirm(self, event)

	def execute(self, context):
		idx, assets, asset = get_assets(context, self.asset_name)

		shutil.rmtree(assets[idx].asset_path)
		H.remove_bpy_struct_item(context.scene.lm_import_list, self.asset_name)
		return {'FINISHED'}

	def draw(self, context):
		layout = self.layout
		col = layout.column()
		col.label(text='This operation will delete the folder DEFINITELY from your hard drive')

class LM_UI_ClearAssetFolder(bpy.types.Operator):
	bl_idname = "scene.lm_clear_asset_folder"
	bl_label = "Clear Selected Asset Folder"
	bl_options = {'REGISTER', 'UNDO'}
	bl_description = "Clear selected Asset Folder."

	@classmethod
	def poll(cls, context):
		return context.scene.lm_import_list

	def invoke(self, context, event):
		wm = context.window_manager
		return wm.invoke_confirm(self)

	def execute(self, context):
		for a in context.scene.lm_import_list:
			bpy.ops.scene.lm_remove_asset_folder(asset_name=a.name)

		return {'FINISHED'}

	def draw(self, context):
		layout = self.layout
		col = layout.column()
		col.label(text='This operation will delete the folder DEFINITELY from your hard drive')

class LM_UI_OpenImportFolder(bpy.types.Operator):
	bl_idname = "scene.lm_open_import_folder"
	bl_label = "Open Import Folder"
	bl_options = {'REGISTER', 'UNDO'}
	bl_description = "Open Import Folder"

	asset_name : bpy.props.StringProperty(name="Asset Name", default="", description='Name of the asset folder to Open')

	@classmethod
	def poll(cls, context):
		return context.scene.lm_import_list

	def execute(self, context):
		bpy.ops.scene.lm_openfolder(folder_path=context.scene.lm_import_list[self.asset_name].asset_path)

		return {'FINISHED'}

class LM_UI_RenameAssetFolder(bpy.types.Operator):
	bl_idname = "scene.lm_rename_asset_folder"
	bl_label = "Rename Asset"
	bl_options = {'REGISTER', 'UNDO'}
	bl_description = "Rename Asset"

	asset_name : bpy.props.StringProperty(name="Asset Name", default="", description='Name of the asset to rename')
	new_name : bpy.props.StringProperty(name="New Name", default="", description='New Name')

	@classmethod
	def poll(cls, context):
		return context.scene.lm_import_list

	def invoke(self, context, event):
		self.new_name = self.asset_name
		wm = context.window_manager
		return wm.invoke_props_dialog(self)

	def execute(self, context):
		asset_naming_convention = N.NamingConvention(context, self.new_name, context.scene.lm_asset_naming_convention)
		if not asset_naming_convention.is_valid:
			self.report({'ERROR	'}, 'Lineup Maker : The new asset name "{}" is not valid'.format(self.new_name))
			wm = context.window_manager
			return wm.invoke_props_dialog(self)
		# rename the asset in Blender File and in Disk
		else:
			_, _, current_asset = get_assets(context, self.asset_name)
			removed = False

			if current_asset.name in context.scene.lm_render_queue:
				removed=True
				bpy.ops.scene.lm_remove_asset_from_render(asset_name=self.asset_name)

			new_path = current_asset.asset_path.replace(self.asset_name, self.new_name)
			
			os.rename(current_asset.asset_path, new_path)

			current_asset.name = self.new_name
			current_asset.asset_path = new_path
			
			if removed:
				bpy.ops.scene.lm_add_asset_to_render_queue(asset_name= self.new_name)

		return {'FINISHED'}

	def draw(self, context):
		layout = self.layout
		col = layout.column()
		col.label(text='From "{}" to :'.format(self.asset_name))
		col.prop(self, 'new_name')