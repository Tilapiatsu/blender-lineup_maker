import bpy
from . import logger as L
from . import helper as H

def get_texture_channels(context):
	idx = context.scene.lm_texture_channel_idx
	texture_channels = context.scene.lm_shaders[context.scene.lm_shader_idx].shader_channels[context.scene.lm_shader_channel_idx].texture_channels

	active = texture_channels[idx] if texture_channels else None

	return idx, texture_channels, active


class LM_UI_AddTextureChannel(bpy.types.Operator):
	bl_idname = "scene.lm_add_texture_channel"
	bl_label = "Add Texture Channel"
	bl_options = {'REGISTER', 'UNDO'}
	bl_description = "Add Texture Channel"

	new_texture_channel : bpy.props.StringProperty(name="New Texture Channel", default="", description='New Texture Channel')

	def invoke(self, context, event):
		self.new_texture_channel = ''
		wm = context.window_manager
		return wm.invoke_props_dialog(self)

	def execute(self, context):
		for k in context.scene.lm_shaders[context.scene.lm_shader_idx].shader_channels[context.scene.lm_shader_channel_idx].texture_channels:
			if k.name == self.new_texture_channel:
				self.report({'ERROR'}, 'Lineup Maker : Keyword Already Exists')
				return {'CANCELLED'}
		else:
			k = context.scene.lm_shaders[context.scene.lm_shader_idx].shader_channels[context.scene.lm_shader_channel_idx].texture_channels.add()
			k.name = self.new_texture_channel
			H.update_texture_channels(self, context)
			return {'FINISHED'}

	def draw(self, context):
		layout = self.layout
		col = layout.column()
		col.prop(self, 'new_texture_channel')


class LM_UI_MoveTexture(bpy.types.Operator):
	bl_idname = "scene.lm_move_texture_channel"
	bl_label = "Move Texture Channel"
	bl_options = {'REGISTER', 'UNDO'}
	bl_description = "Move Texture Channel Name up or down.\nThis controls the position in the Menu."

	direction: bpy.props.EnumProperty(items=[("UP", "Up", ""), ("DOWN", "Down", "")])

	def execute(self, context):
		idx, texture_channel, _ = get_texture_channels(context)

		if self.direction == "UP":
			nextidx = max(idx - 1, 0)
		elif self.direction == "DOWN":
			nextidx = min(idx + 1, len(texture_channel) - 1)

		texture_channel.move(idx, nextidx)
		context.scene.lm_texture_channel_idx = nextidx
		H.update_texture_channels(self, context)

		return {'FINISHED'}



class LM_UI_RenameTexture(bpy.types.Operator):
	bl_idname = "scene.lm_rename_texture_channel"
	bl_label = "Rename Texture Channel"
	bl_options = {'REGISTER', 'UNDO'}
	bl_description = "Rename the selected Texture Channel Name"
	
	index : bpy.props.IntProperty(name="Index", default=-1, description='Index of the item')
	new_name: bpy.props.StringProperty(name="New Name")

	def check(self, context):
		return True

	@classmethod
	def poll(cls, context):
		return context.scene.lm_texture_channels

	def draw(self, context):
		layout = self.layout

		column = layout.column()
		column.prop(self, "new_name")

	def invoke(self, context, event):
		if self.index == -1:
			self.index, _, self.active = get_texture_channels(context)
		else:
			if self.index >= len(context.scene.lm_keywords):
				self.report({'ERROR'}, f'Lineup Maker : No Texture channels with index {self.index}')
				return {'CANCELLED'}

			self.active = context.scene.lm_shaders[context.scene.lm_shader_idx].shader_channels[context.scene.lm_shader_channel_idx].texture_channels[self.index]

		self.new_name = self.active.name

		wm = context.window_manager
		return wm.invoke_props_dialog(self)

	def execute(self, context):
		if self.new_name:
			self.active.name = self.new_name
			H.update_texture_channels(self, context)

		return {'FINISHED'}


class LM_UI_ClearTexture(bpy.types.Operator):
	bl_idname = "scene.lm_clear_texture_channels"
	bl_label = "Clear All Texture Channel"
	bl_options = {'REGISTER', 'UNDO'}
	bl_description = "Clear All Texture Channel Names."

	@classmethod
	def poll(cls, context):
		condition = len(context.scene.lm_shaders) and context.scene.lm_shader_idx < len(context.scene.lm_shaders)
		if not condition:
			return False

		condition = len(context.scene.lm_shaders[context.scene.lm_shader_idx].shader_channels) and context.scene.lm_shader_channel_idx < len(context.scene.lm_shaders[context.scene.lm_shader_idx].shader_channels)
		if not condition:
			return False

		return context.scene.lm_shaders[context.scene.lm_shader_idx].shader_channels[context.scene.lm_shader_channel_idx].texture_channels

	def execute(self, context):
		context.scene.lm_shaders[context.scene.lm_shader_idx].shader_channels[context.scene.lm_shader_channel_idx].texture_channels.clear()
		H.update_texture_channels(self, context)
		return {'FINISHED'}


class LM_UI_RemoveTexture(bpy.types.Operator):
	bl_idname = "scene.lm_remove_texture_channel"
	bl_label = "Remove Material Name"
	bl_options = {'REGISTER', 'UNDO'}
	bl_description = "Remove selected Texture Channel Name."

	index : bpy.props.IntProperty(name="Index", default=-1, description='Index of the item')

	@classmethod
	def poll(cls, context):
		return context.scene.lm_texture_channels

	def execute(self, context):
		if self.index == -1:
			self.index, texture_channel, _ = get_texture_channels(context)
		else:
			_, texture_channel, _ = get_texture_channels(context)

		texture_channel.remove(self.index)

		context.scene.lm_texture_channel_idx = min(self.index, len(context.scene.lm_texture_channels) - 1)
		H.update_texture_channels(self, context)
		return {'FINISHED'}
