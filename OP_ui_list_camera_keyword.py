import bpy
from . import logger as L
from . import helper as H

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

def get_camera_keywords(context):
	idx = context.scene.lm_camera_idx
	cameras = context.scene.lm_cameras

	active = cameras[idx] if cameras else None

	return idx, cameras, active

class LM_UI_MoveCameraKeyword(bpy.types.Operator):
	bl_idname = "scene.lm_move_camera_keyword"
	bl_label = "Move Keyword"
	bl_options = {'REGISTER', 'UNDO'}
	bl_description = "Move Camera keyword Name up or down.\nThis controls the position in the Menu."

	direction: bpy.props.EnumProperty(items=[("UP", "Up", ""), ("DOWN", "Down", "")])

	def execute(self, context):
		idx, camera, _ = get_camera_keywords(context)

		if self.direction == "UP":
			nextidx = max(idx - 1, 0)
		elif self.direction == "DOWN":
			nextidx = min(idx + 1, len(camera) - 1)

		camera.move(idx, nextidx)
		context.scene.lm_camera_idx = nextidx

		return {'FINISHED'}


class LM_UI_ClearCameraKeyword(bpy.types.Operator):
	bl_idname = "scene.lm_clear_camera_keywords"
	bl_label = "Clear All Camera keyword"
	bl_options = {'REGISTER', 'UNDO'}
	bl_description = "Clear All Texture keyword Names."

	@classmethod
	def poll(cls, context):
		return context.scene.lm_cameras

	def execute(self, context):
		context.scene.lm_cameras.clear()

		return {'FINISHED'}


class LM_UI_RemoveCameraKeyword(bpy.types.Operator):
	bl_idname = "scene.lm_remove_camera_keyword"
	bl_label = "Remove Camera Keyword Name"
	bl_options = {'REGISTER', 'UNDO'}
	bl_description = "Remove selected camera keyword Name."

	@classmethod
	def poll(cls, context):
		return context.scene.lm_cameras

	def execute(self, context):
		idx, camera, _ = get_camera_keywords(context)

		camera.remove(idx)

		context.scene.lm_camera_idx = min(idx, len(context.scene.lm_cameras) - 1)

		return {'FINISHED'}

class LM_UI_EditCameraKeywords(bpy.types.Operator):
	bl_idname = "scene.lm_edit_camera_keywords"
	bl_label = "Edit Camera Keywords"
	bl_options = {'REGISTER', 'UNDO'}
	bl_description = "Edit Camera Keyword"

	index : bpy.props.IntProperty(name="Camera Index", default=-1, description='Index of the item')

	camera = None
	protected = ['camera', 'index', 'new_camera']

	def populate_property(self, property_name, property_value):
		setattr(self, property_name, property_value)

	def create_keyword_annotations(self, context):
		for k in context.scene.lm_keywords:
			if k in self.__class__.__annotations__.keys():
				continue
			self.__class__.__annotations__[k.name] = bpy.props.StringProperty(name=k.name, default='')
		key_to_delete=[]
		for k in self.__class__.__annotations__.keys():
			if k not in context.scene.lm_keywords and k not in self.protected and k not in ['protected']:
				key_to_delete.append(k)

		for k in key_to_delete:
			del self.__class__.__annotations__[k]

	def invoke(self, context, event):
		if self.index == -1:
			self.report({'ERROR'}, 'Lineup Maker : index is not valid')
			return {'CANCELLED'}

		self.camera = context.scene.lm_cameras[self.index]
		context.scene.lm_select_camera_object.camera = self.camera.camera
		self.create_keyword_annotations(context)

		for k in self.__class__.__annotations__:
			# Cleaning Previous keyword Values
			for kw in self.camera.keywords:
				kw = ""
			# populate each set keyword
			for kw in self.camera.keywords:
				if k == kw.keyword:
					self.populate_property(k, kw.keyword_value)
					continue
		
		bpy.utils.unregister_class(LM_UI_EditCameraKeywords)
		bpy.utils.register_class(LM_UI_EditCameraKeywords)

		wm = context.window_manager
		return wm.invoke_props_dialog(self, width=800)

	def execute(self, context):
		self.camera.camera = context.scene.lm_select_camera_object.camera
		self.camera.name = str(str(self.index))
		camera_keywords = [kk.keyword for kk in self.camera.keywords]

		for k in context.scene.lm_keywords:
			curr_keyword_value = getattr(self, k.name)
			if k.name in camera_keywords:
				if curr_keyword_value == '':
					for i, kk in enumerate(self.camera.keywords):
						if kk.keyword == k.name:
							self.camera.keywords.remove(i)
							break
				for kk in self.camera.keywords:
					if kk.keyword == k.name:
						kk.keyword_value = curr_keyword_value
			else:
				if curr_keyword_value == '':
					continue
				curr_camera_keyword = self.camera.keywords.add()
				curr_camera_keyword.keyword = k.name
				curr_camera_keyword.keyword_value = getattr(self, k.name)
				
		return {'FINISHED'}

	def draw(self, context):
		layout = self.layout
		col = layout.column()
		col.prop(context.scene.lm_select_camera_object, 'camera')
		for k in self.__class__.__annotations__.keys():
			if k in ['index', 'camera']:
				continue
			col.prop(self, k)

class LM_UI_AddCamera(bpy.types.Operator):
	bl_idname = "scene.lm_add_camera_keywords"
	bl_label = "Add Camera"
	bl_options = {'REGISTER', 'UNDO'}
	bl_description = "Add Camera Keyword"

	new_camera_name : bpy.props.StringProperty(name="New Camera Name", default="", description='New Camera Name')

	camera = None
	protected = ['new_camera_name', 'camera']

	@classmethod
	def poll(cls, context):
		return context.scene.lm_keywords

	def create_keyword_annotations(self, context):
		for k in context.scene.lm_keywords:
			if k in self.__class__.__annotations__.keys():
				continue
			self.__class__.__annotations__[k.name] = bpy.props.StringProperty(name=k.name, default='')
		key_to_delete=[]
		for k in self.__class__.__annotations__.keys():
			if k not in context.scene.lm_keywords and k not in self.protected and k not in ['protected']:
				key_to_delete.append(k)

		for k in key_to_delete:
			del self.__class__.__annotations__[k]


	def populate_property(self, property_name, property_value):
		self.__class__.__annotations__[property_name] = property_value

	def invoke(self, context, event):
		self.create_keyword_annotations(context)
		if context.object is not None and context.object.type == 'CAMERA':
			context.scene.lm_select_camera_object.camera = context.object
		else:
			context.scene.lm_select_camera_object.camera = None

		bpy.utils.unregister_class(LM_UI_AddCamera)
		bpy.utils.register_class(LM_UI_AddCamera)

		wm = context.window_manager
		return wm.invoke_props_dialog(self, width=800)

	def execute(self, context):
		if context.scene.lm_select_camera_object.camera is None:
			self.report({'ERROR'}, 'Lineup Maker : Please Select a Valid Camera')
			return {'CANCELLED'}

		self.camera = context.scene.lm_cameras.add()
		self.camera.camera = context.scene.lm_select_camera_object.camera
		for i,c in enumerate(context.scene.lm_cameras):
			if c == self.camera:
				self.camera.name = str(i)

		for k in context.scene.lm_keywords:
			# If keyword is not set, skip
			if getattr(self, k.name) == '':
				continue
			
			curr_camera_keyword = self.camera.keywords.add()
			curr_camera_keyword.keyword = k.name
			curr_camera_keyword.keyword_value = getattr(self, k.name)

		return {'FINISHED'}

	def draw(self, context):
		layout = self.layout
		col = layout.column()
		col.prop(context.scene.lm_select_camera_object, 'camera')
		for k in self.__class__.__annotations__.keys():
			if k not in self.protected:
				col.prop(self, k)
