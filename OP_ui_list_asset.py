import bpy, os, subprocess
from os import path
from . import helper as H
from . import logger as L
from . import naming_convention as N
from . import properties as P
from . import variables as V

def get_assets(context, name):
	H.renumber_assets(context)
	assets = context.scene.lm_asset_list
	if name in assets:
		idx = context.scene.lm_asset_list[name].asset_index
		asset = context.scene.lm_asset_list[name]
		active = context.scene.lm_asset_list[idx]
	else:
		idx = context.scene.lm_asset_list_idx
		asset = None
		active = context.scene.lm_asset_list[idx]

	return asset, idx, assets, active

class LM_UI_MoveAsset(bpy.types.Operator):
	bl_idname = "scene.lm_move_asset"
	bl_label = "Move Keyword"
	bl_options = {'REGISTER', 'UNDO'}
	bl_description = "Move Camera keyword Name up or down.\nThis controls the position in the Menu."

	direction: bpy.props.EnumProperty(items=[("UP", "Up", ""), ("DOWN", "Down", "")])
	asset_name : bpy.props.StringProperty(name="Asset Name", default="", description='Name of the asset to move')

	def execute(self, context):
		_, idx, asset, _ = get_assets(context, self.asset_name)

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
			H.remove_asset_in_library(context, asset.name)
		
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
		return len(context.scene.lm_asset_list)

	def execute(self, context):
		asset, idx, _, _ = get_assets(context, self.asset_name)

		H.remove_asset(context, asset.name)
		context.scene.lm_asset_list_idx = idx - 1 if idx else 0

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

class LM_UI_OpenAssetCatalog(bpy.types.Operator):
	bl_idname = "scene.lm_open_asset_catalog"
	bl_label = "Open Asset Catalog"
	bl_options = {'REGISTER', 'UNDO'}
	bl_description = "Open Asset Catalog"

	asset_name : bpy.props.StringProperty(name="Asset Name", default="", description='Name of the asset folder to Open')

	@classmethod
	def poll(cls, context):
		return context.scene.lm_asset_list

	def execute(self, context):
		asset_path = path.join(bpy.context.scene.lm_blend_catalog_path, self.asset_name + '.blend')

		command = '''import bpy
bpy.ops.wm.open_mainfile("EXEC_DEFAULT", filepath=r"{}")
'''.format(asset_path)

		subprocess.check_call([bpy.app.binary_path, V.LM_CATALOG_PATH, '--python-expr', command])

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
		if self.asset_name in context.scene.lm_asset_list and path.exists(context.scene.lm_asset_list[self.asset_name].catalog_path):
			if V.LM_PREVIEW_COLLECTION in bpy.data.collections:
				bpy.data.collections.remove(bpy.data.collections[V.LM_PREVIEW_COLLECTION])
				bpy.data.batch_remove(ids=(bpy.data.libraries[context.scene.lm_asset_in_preview + '.blend'],))
				bpy.data.batch_remove(ids=(bpy.data.objects[context.scene.lm_asset_in_preview],))
					
			H.create_asset_collection(context, V.LM_PREVIEW_COLLECTION)
			H.set_active_collection(context, V.LM_PREVIEW_COLLECTION)

			asset_filepath = context.scene.lm_asset_list[self.asset_name].catalog_path
			datablock_dir = '\\Collection\\'

			H.link_blend_file(asset_filepath, datablock_dir, self.asset_name)

			if self.asset_name in context.scene.lm_asset_list:
				camera_name = context.scene.lm_asset_list[self.asset_name].render_camera
				self.set_local_camera(context, camera_name)
			else:
				camera_name = context.scene.lm_default_camera.name
				self.set_local_camera(context, camera_name)

			context.scene.lm_asset_in_preview = self.asset_name
			return {'FINISHED'}
		
		elif self.asset_name == '':
			bpy.data.collections.remove(bpy.data.collections[V.LM_PREVIEW_COLLECTION])
			bpy.data.batch_remove(ids=(bpy.data.libraries[context.scene.lm_asset_in_preview + '.blend'],))
			bpy.data.batch_remove(ids=(bpy.data.objects[context.scene.lm_asset_in_preview],))
			context.scene.lm_asset_in_preview = ''
			return {'FINISHED'}
		else:
			self.report({'ERROR'}, 'Lineup Maker : The asset {} doesn\'t exists'.format(self.asset_name))
			return {'CANCELLED'}

	def set_local_camera(self, context, camera_name):
		camera_list = [o.name for o in context.scene.objects if o.type == 'CAMERA']
		if not len(camera_name) or camera_name not in camera_list:
			return
		for a in context.screen.areas:
			if a.type == 'VIEW_3D':
				for s in a.spaces:
					if s.type =='VIEW_3D':
						s.camera = bpy.data.objects[camera_name]
						s.use_local_camera=True

class LM_UI_PrintAssetData(bpy.types.Operator):
	bl_idname = "scene.lm_print_asset_data"
	bl_label = "Print asset data"
	bl_options = {'REGISTER', 'UNDO'}
	bl_description = "Print all asset data in the scene"

	asset_name : bpy.props.StringProperty(name="Asset Name", default="", description='Name of the asset to print')

	render_date : bpy.props.FloatProperty(name="Last Render")
	import_date : bpy.props.FloatProperty(name="Import Date")
	mesh_list : bpy.props.StringProperty()
	material_list : bpy.props.StringProperty()
	texture_list : bpy.props.StringProperty()
	view_layer : bpy.props.StringProperty(name="View Layer")
	collection : bpy.props.StringProperty()
	need_update : bpy.props.BoolProperty(default=False)
	need_render : bpy.props.BoolProperty()
	rendered : bpy.props.BoolProperty()
	need_composite : bpy.props.BoolProperty()
	composited : bpy.props.BoolProperty()
	asset_path : bpy.props.StringProperty(subtype='DIR_PATH')
	catalog_path : bpy.props.StringProperty(subtype='DIR_PATH')
	render_path : bpy.props.StringProperty(subtype='DIR_PATH')
	render_camera : bpy.props.StringProperty(name="Render camera")
	asset_folder_exists : bpy.props.BoolProperty()
	
	raw_composite_filepath : bpy.props.StringProperty(subtype='FILE_PATH')
	final_composite_filepath : bpy.props.StringProperty(subtype='FILE_PATH')
	render_list : bpy.props.StringProperty()

	need_write_info : bpy.props.BoolProperty(default=False)
	info_written : bpy.props.BoolProperty(default=False)

	is_valid : bpy.props.BoolProperty(default=False)

	hd_status : bpy.props.IntProperty(default=-1)
	ld_status : bpy.props.IntProperty(default=-1)
	baking_status : bpy.props.IntProperty(default=-1)
	triangles : bpy.props.IntProperty()
	vertices : bpy.props.IntProperty()
	has_uv2 : bpy.props.BoolProperty(default=False)
	section : bpy.props.StringProperty(name="Section")
	from_file : bpy.props.StringProperty(name="From File")

	checked : bpy.props.BoolProperty(default=True)

	asset = None
	list_properties = ['mesh_list', 'material_list', 'texture_list', 'render_list', 'collection']


	@classmethod
	def poll(cls, context):
		return context.scene.lm_asset_list

	def invoke(self, context, event):
		_, _, assets, _ = get_assets(context, self.asset_name)
		try:
			self.asset = assets[self.asset_name]
		except ValueError:
			self.report({'ERROR'}, 'Lineup Maker : The asset "{}" is not valid'.format(self.asset_name))

		self.registered_annotations = []
		for k in self.__annotations__.keys():
			if k in ['asset_name']:
				continue
			
			asset_value = getattr(self.asset, k, None)
			if asset_value is None:
				continue
			if k in self.list_properties:
				value = []
				if not isinstance(asset_value, bpy.types.Collection):
					for e in asset_value:
						if 'name' in dir(e):
							v = e.name
						else:
							v = e
						value.append(v)
				setattr(self, k, str(value).strip('[]'))
			else:
				setattr(self, k, asset_value)
			self.registered_annotations.append(k)

		wm = context.window_manager
		return wm.invoke_props_dialog(self, width=800)

	def execute(self, context):
		for k in self.registered_annotations:
			if not k in ['name'] + self.list_properties:
				setattr(self.asset, k, getattr(self, k))
		return {'FINISHED'}
	
	def draw(self, context):
		layout = self.layout
		col = layout.column()
		col.label(text='{} Datas'.format(self.asset_name))
		col.separator()

		if self.asset:
			for k in self.registered_annotations:
				if not k in ['name']:
					col.prop(self, k)

		
class LM_UI_RenameAsset(bpy.types.Operator):
	bl_idname = "scene.lm_rename_asset"
	bl_label = "Rename Asset"
	bl_options = {'REGISTER', 'UNDO'}
	bl_description = "Rename Asset"

	asset_name : bpy.props.StringProperty(name="Asset Name", default="", description='Name of the asset to rename')
	new_name : bpy.props.StringProperty(name="New Name", default="", description='New Name')

	@classmethod
	def poll(cls, context):
		return context.scene.lm_asset_list

	def invoke(self, context, event):
		self.new_name = self.asset_name
		wm = context.window_manager
		return wm.invoke_props_dialog(self)

	def execute(self, context):
		asset_naming_convention = N.NamingConvention(context, self.new_name, context.scene.lm_asset_naming_convention)

		_, _, _, current_asset = get_assets(context, self.asset_name)
		removed = False
		if current_asset.name in context.scene.lm_render_queue:
			removed=True
			bpy.ops.scene.lm_remove_asset_from_render_queue(asset_name=self.asset_name)

		new_asset_path = current_asset.asset_path.replace(self.asset_name, self.new_name)
		new_render_path = current_asset.render_path.replace(self.asset_name, self.new_name)
		new_final_composite_filepath = current_asset.final_composite_filepath.replace(self.asset_name, self.new_name)
		
		# renaming asset and rendering folder
		os.rename(current_asset.asset_path, new_asset_path)

		if len(new_render_path):
			os.rename(current_asset.render_path, new_render_path)

		if len(new_final_composite_filepath):
			os.rename(current_asset.final_composite_filepath, new_final_composite_filepath)
		
		# update the assets Datas
		current_asset.name = self.new_name
		current_asset.asset_path = new_asset_path
		current_asset.render_path = new_render_path
		current_asset.final_composite_filepath = new_final_composite_filepath
		current_asset.collection.name = current_asset.collection.name.replace(self.asset_name, self.new_name)
		current_asset.view_layer = current_asset.view_layer.replace(self.asset_name, self.new_name)
		bpy.context.scene.view_layers[self.asset_name].name = self.new_name

		# Rename the rendered files
		if path.isdir(current_asset.render_path):
			for f in os.listdir(current_asset.render_path):
				filepath = path.join(current_asset.render_path, f)
				new_filepath = path.join(current_asset.render_path, f.replace(self.asset_name, self.new_name))
				os.rename(filepath, new_filepath)
		
		if removed:
			bpy.ops.scene.lm_add_asset_to_render_queue(asset_name= self.new_name)

		return {'FINISHED'}

	def draw(self, context):
		layout = self.layout
		col = layout.column()
		col.label(text='From "{}" to :'.format(self.asset_name))
		col.prop(self, 'new_name')


class LM_UI_ShowAssetWarning(bpy.types.Operator):
	bl_idname = "scene.lm_show_asset_warnings"
	bl_label = "Show Asset Warnings"
	bl_options = {'REGISTER', 'UNDO'}
	bl_description = "Show Asset Warnings"

	asset_name : bpy.props.StringProperty(name="Asset Name", default="", description='Name of the asset to rename')

	@classmethod
	def poll(cls, context):
		return context.scene.lm_asset_list

	def invoke(self, context, event):
		wm = context.window_manager
		return wm.invoke_props_dialog(self, width=1000)

	def execute(self, context):
		return {'FINISHED'}

	def draw(self, context):
		layout = self.layout
		col = layout.column()
		col.label(text='Warning for asset : "{}"'.format(self.asset_name))
		col.separator()
		col.separator()
		for w in context.scene.lm_asset_list[self.asset_name].warnings:
			col.label(text='{}'.format(w.message))

		
class LM_UI_FixViewLayers(bpy.types.Operator):
	bl_idname = "scene.lm_fix_view_layers"
	bl_label = "Fix View layers visibility"
	bl_options = {'REGISTER', 'UNDO'}
	bl_description = "Fix View layers visibility"

	asset_name : bpy.props.StringProperty(name="Asset Name", default="", description='Name of the asset to rename')

	@classmethod
	def poll(cls, context):
		return context.scene.lm_asset_list


	def execute(self, context):
		view_layer_list = H.get_view_layer_dict(context)

		if len(self.asset_name):
			updated_asset_list = [self.asset_name]
		else:
			updated_asset_list = [a.name for a in context.scene.lm_asset_list]

		for l in context.scene.view_layers:
			H.update_view_layer(context, l.name, updated_asset_list, view_layer_list)

		return {'FINISHED'}