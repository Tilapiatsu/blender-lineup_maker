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

	asset_name : bpy.props.StringProperty(name="Asset Name", default="", description='Name of the asset to remove')

	@classmethod
	def poll(cls, context):
		return len(context.scene.lm_asset_path) and path.isdir(context.scene.lm_asset_path)
	
	def execute(self, context):
		folder_src = context.scene.lm_asset_path

		# If asset_name is not specified, processed all assets
		if not len(self.asset_name):
			asset_folders = [path.join(folder_src, f,) for f in os.listdir(folder_src) if path.isdir(os.path.join(folder_src, f))]
			asset_folders_name = [path.basename(f) for f in asset_folders]
			bpy.ops.scene.lm_refresh_asset_status()
		# Else process only specified asset
		else:
			folder_path = path.join(folder_src, self.asset_name,)
			if not path.isdir(folder_path):
				self.report({'ERROR'}, 'Lineup Maker : Asset folder "{}" doesn\'t exists'.format(self.asset_name))
				return {'CANCELLED'}
			else:
				asset_folders = [folder_path]
				asset_folders_name = [self.asset_name]
				bpy.ops.scene.lm_refresh_asset_status(asset_name = self.asset_name)

		for f in asset_folders:
			asset_name = path.basename(f)
			# If asset is not in the import list nor in the asset list
			if asset_name not in context.scene.lm_import_list and asset_name not in context.scene.lm_asset_list:
				asset = context.scene.lm_import_list.add()
				asset.name = asset_name
				asset.asset_path = f
				asset.asset_folder_exists = True

				asset_naming_convention = N.NamingConvention(context, asset_name, context.scene.lm_asset_naming_convention)
				asset.is_valid = asset_naming_convention.is_valid

			# If asset is already imported and is not yet in Import List
			elif asset_name in context.scene.lm_asset_list and asset_name not in context.scene.lm_import_list:
				# Check if the asset need to be updated
				asset = context.scene.lm_asset_list[asset_name]
				if asset.need_update:
					asset_import = context.scene.lm_import_list.add()
					asset_import.name = asset.name
					asset_import.asset_path = asset.asset_path
					asset_import.asset_folder_exists = True
					asset_import.is_valid = True
					asset_import.need_update = True

		for a in context.scene.lm_import_list:
			if a.name not in asset_folders_name or ( a.name in context.scene.lm_asset_list and not context.scene.lm_import_list[a.name].need_update):
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

		shutil.rmtree(assets[idx].asset_path, ignore_errors=True)
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
		return wm.invoke_confirm(self, event)

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
		if self.new_name in context.scene.lm_asset_list:
			self.report({'ERROR'}, 'Lineup Maker : Asset "{}" Already Exists'.format(self.new_name))
			return {'CANCELLED'}
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

class LM_UI_CheckAllImportList(bpy.types.Operator):
	bl_idname = "scene.lm_check_all_import_list"
	bl_label = "Check all import list"
	bl_options = {'REGISTER', 'UNDO'}
	bl_description = "Check all render import list"

	@classmethod
	def poll(cls, context):
		return context.scene.lm_import_list

	def execute(self, context):
		for a in context.scene.lm_import_list:
			a.checked = True

		return {'FINISHED'}

class LM_UI_UncheckAllImportList(bpy.types.Operator):
	bl_idname = "scene.lm_uncheck_all_import_list"
	bl_label = "Uncheck all render import list"
	bl_options = {'REGISTER', 'UNDO'}
	bl_description = "Uncheck all render import list"

	@classmethod
	def poll(cls, context):
		return context.scene.lm_import_list

	def execute(self, context):
		for a in context.scene.lm_import_list:
			a.checked = False

		return {'FINISHED'}

class LM_UI_PrintNamingConvention(bpy.types.Operator):
	bl_idname = "scene.lm_print_naming_convention"
	bl_label = "Print Naming Convention"
	bl_options = {'REGISTER', 'UNDO'}
	bl_description = "Print Naming Convention"

	asset_name : bpy.props.StringProperty(name="Asset Name", default="", description='Name of the asset to inspect')
	naming_convention = None

	@classmethod
	def poll(cls, context):
		return context.scene.lm_import_list
	
	def invoke(self, context, event):
		self.naming_convention = N.NamingConvention(context, self.asset_name, context.scene.lm_asset_naming_convention)
		wm = context.window_manager
		return wm.invoke_props_dialog(self, width=800)

	def execute(self, context):
		return {'FINISHED'}

	def draw(self, context):
		layout = self.layout
		col = layout.column()
		col.label(text='Fullname = {}'.format(self.asset_name))
		col.label(text='Is Valid = {}'.format(self.naming_convention.is_valid))
		for k, v in zip(self.naming_convention.name_list, self.naming_convention.included_words):
			col.label(text='{} = {}'.format(k, v))
		