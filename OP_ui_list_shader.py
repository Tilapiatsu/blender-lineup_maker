import bpy
from . import logger as L
from . import helper as H

def get_shaders(context):
	idx = context.scene.lm_shader_idx
	shaders = context.scene.lm_shaders

	active = shaders[idx] if shaders else None

	return idx, shaders, active


class LM_UI_AddShader(bpy.types.Operator):
	bl_idname = "scene.lm_add_shader"
	bl_label = "Add shader"
	bl_options = {'REGISTER', 'UNDO'}
	bl_description = "Add shader"

	new_shader : bpy.props.StringProperty(name="New Shader", default="", description='New Shader')

	def invoke(self, context, event):
		self.new_shader = ''
		wm = context.window_manager
		return wm.invoke_props_dialog(self)

	def execute(self, context):
		for k in context.scene.lm_shaders:
			if k.name == self.new_shader:
				self.report({'ERROR'}, 'Lineup Maker : Shader Already Exists')
				return {'CANCELLED'}
		else:
			k = context.scene.lm_shaders.add()
			k.name = self.new_shader

			return {'FINISHED'}

	def draw(self, context):
		layout = self.layout
		col = layout.column()
		col.prop(self, 'new_shader')


class LM_UI_MoveShader(bpy.types.Operator):
	bl_idname = "scene.lm_move_shader"
	bl_label = "Move shader"
	bl_options = {'REGISTER', 'UNDO'}
	bl_description = "Move Shader Name up or down.\nThis controls the position in the Menu."

	direction: bpy.props.EnumProperty(items=[("UP", "Up", ""), ("DOWN", "Down", "")])

	def execute(self, context):
		idx, shader, _ = get_shaders(context)

		if self.direction == "UP":
			nextidx = max(idx - 1, 0)
		elif self.direction == "DOWN":
			nextidx = min(idx + 1, len(shader) - 1)

		shader.move(idx, nextidx)
		context.scene.lm_shader_idx = nextidx

		return {'FINISHED'}



class LM_UI_RenameShader(bpy.types.Operator):
	bl_idname = "scene.lm_rename_shader"
	bl_label = "Rename Shader"
	bl_options = {'REGISTER', 'UNDO'}
	bl_description = "Rename the selected shader Name"

	index : bpy.props.IntProperty(name="Index", default=-1, description='Index of the item')
	new_name: bpy.props.StringProperty(name="New Name")

	@classmethod
	def poll(cls, context):
		return context.scene.lm_shaders

	def draw(self, context):
		layout = self.layout

		column = layout.column()
		column.prop(self, "new_name")

	def invoke(self, context, event):
		if self.index == -1:
			_, _, self.active = get_shaders(context)
		else:
			if self.index >= len(context.scene.lm_keywords):
				self.report({'ERROR'}, f'Lineup Maker : No Keyword with index {self.index}')
				return {'CANCELLED'}

			self.active = context.scene.lm_shaders[self.index]

		self.new_name = self.active.name

		wm = context.window_manager
		return wm.invoke_props_dialog(self)

	def execute(self, context):
		if self.new_name:
			self.active.name = self.new_name

		return {'FINISHED'}


class LM_UI_ClearShader(bpy.types.Operator):
	bl_idname = "scene.lm_clear_shaders"
	bl_label = "Clear All Texture shader"
	bl_options = {'REGISTER', 'UNDO'}
	bl_description = "Clear All Texture shader Names."

	@classmethod
	def poll(cls, context):
		return context.scene.lm_shaders

	def execute(self, context):
		context.scene.lm_shaders.clear()

		H.update_shader_channels(self, context)
		return {'FINISHED'}


class LM_UI_RemoveShader(bpy.types.Operator):
	bl_idname = "scene.lm_remove_shader"
	bl_label = "Remove Material Name"
	bl_options = {'REGISTER', 'UNDO'}
	bl_description = "Remove selected Texture shader Name."

	index : bpy.props.IntProperty(name="Index", default=-1, description='Index of the item')

	@classmethod
	def poll(cls, context):
		return context.scene.lm_shaders

	def execute(self, context):
		if self.index < 0:
			self.index, shaders, _ = get_shaders(context)
		else:
			_, shaders, _ = get_shaders(context)

		shaders.remove(self.index)

		context.scene.lm_shader_idx = min(self.index, len(context.scene.lm_shaders) - 2)
		H.update_shader_channels(self, context)
		return {'FINISHED'}
