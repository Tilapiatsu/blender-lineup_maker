import bpy
from . import logger as L
from . import helper as H

def get_channels(context):
	idx = context.scene.lm_shader_channel_idx
	channels = context.scene.lm_shaders[context.scene.lm_shader_idx].shader_channels

	active = channels[idx] if channels else None

	return idx, channels, active

class LM_UI_AddShaderChannel(bpy.types.Operator):
	bl_idname = "scene.lm_add_shader_channel"
	bl_label = "Add Shader Channel"
	bl_options = {'REGISTER', 'UNDO'}
	bl_description = "Add Shader Channel"

	name : bpy.props.StringProperty(name="name", default="", description='name')
	linear : bpy.props.BoolProperty(name="Linear", default=False, description='Linear')
	normal_map : bpy.props.BoolProperty(name="Normal Map", default=False, description='Normal Map')
	inverted : bpy.props.BoolProperty(name="Inverted", default=False, description='Inverted')

	def invoke(self, context, event):
		self.name = ''
		self.linear = False
		self.normal_map = False
		self.inverted = False
		wm = context.window_manager
		return wm.invoke_props_dialog(self)

	def execute(self, context):
		_, channels, _ = get_channels(context)
		for k in channels:
			if k.name == self.name:
				self.report({'ERROR'}, 'Lineup Maker : Shader Channel Already Exists')
				return {'CANCELLED'}
		else:
			k = context.scene.lm_shaders[context.scene.lm_shader_idx].shader_channels.add()
			k.name = self.name
			k.linear = self.linear
			k.normal_map = self.normal_map
			k.inverted = self.inverted
			H.update_shader_channels(self, context)
			return {'FINISHED'}

	def draw(self, context):
		layout = self.layout
		col = layout.column()
		col.prop(self, 'name')
		col.prop(self, 'linear')
		col.prop(self, 'normal_map')
		if self.normal_map:
			text='Invert Green'
		else:
			text='Invert'
		col.prop(self, 'inverted', text=text)


class LM_UI_MoveChannel(bpy.types.Operator):
	bl_idname = "scene.lm_move_channel"
	bl_label = "Move Channel"
	bl_options = {'REGISTER', 'UNDO'}
	bl_description = "Move Channel Name up or down.\nThis controls the position in the Menu."

	direction: bpy.props.EnumProperty(items=[("UP", "Up", ""), ("DOWN", "Down", "")])

	def execute(self, context):
		idx, channel, _ = get_channels(context)

		if self.direction == "UP":
			nextidx = max(idx - 1, 0)
		elif self.direction == "DOWN":
			nextidx = min(idx + 1, len(channel) - 1)

		channel.move(idx, nextidx)
		context.scene.lm_shader_channel_idx = nextidx

		H.update_shader_channels(self, context)

		return {'FINISHED'}


class LM_UI_RenameChannel(bpy.types.Operator):
	bl_idname = "scene.lm_rename_channel"
	bl_label = "Rename Shader Channel"
	bl_options = {'REGISTER', 'UNDO'}
	bl_description = "Rename the selected Shader Channel Name"

	index : bpy.props.IntProperty(name="Index", default=-1, description='Index of the item')
	new_channel_name: bpy.props.StringProperty(name="New Name")
	new_linear_channel: bpy.props.BoolProperty(name="Linear Channel")
	new_normal_map_channel: bpy.props.BoolProperty(name="NormalMap Channel")
	new_inverted_channel: bpy.props.BoolProperty(name="Inverted Channel")

	def check(self, context):
		return True

	@classmethod
	def poll(cls, context):
		return context.scene.lm_shader_channels

	def draw(self, context):
		layout = self.layout

		column = layout.column()

		column.prop(self, "new_channel_name")
		column.prop(self, "new_linear_channel")
		column.prop(self, "new_normal_map_channel")
		if self.new_normal_map_channel:
			text='Invert Green'
		else:
			text='Invert'
		column.prop(self, "new_inverted_channel", text=text)

	def invoke(self, context, event):
		if self.index == -1:
			self.index, _, self.active = get_channels(context)
		else:
			if self.index >= len(context.scene.lm_shaders[context.scene.lm_shader_idx].shader_channels):
				self.report({'ERROR'}, f'Lineup Maker : No Keyword with index {self.index}')
				return {'CANCELLED'}
			self.active = context.scene.lm_shaders[context.scene.lm_shader_idx].shader_channels[self.index]

		self.new_channel_name = self.active.name
		self.new_linear_channel = self.active.linear
		self.new_normal_map_channel = self.active.normal_map
		self.new_inverted_channel = self.active.inverted

		wm = context.window_manager
		return wm.invoke_props_dialog(self)

	def execute(self, context):
		if self.new_channel_name:

			self.active.name = self.new_channel_name
			self.active.linear = self.new_linear_channel
			self.active.normal_map = self.new_normal_map_channel
			self.active.inverted = self.new_inverted_channel
		
			H.update_shader_channels(self, context)
			
		return {'FINISHED'}


class LM_UI_ClearChannel(bpy.types.Operator):
	bl_idname = "scene.lm_clear_channels"
	bl_label = "Clear All Texture Channel"
	bl_options = {'REGISTER', 'UNDO'}
	bl_description = "Clear All Texture Channel Names."

	@classmethod
	def poll(cls, context):
		condition = len(context.scene.lm_shaders) and context.scene.lm_shader_idx < len(context.scene.lm_shaders)
		if not condition:
			return False

		return context.scene.lm_shaders[context.scene.lm_shader_idx].shader_channels

	def execute(self, context):
		context.scene.lm_shaders[context.scene.lm_shader_idx].shader_channels.clear()
		H.update_shader_channels(self, context)

		return {'FINISHED'}


class LM_UI_RemoveChannel(bpy.types.Operator):
	bl_idname = "scene.lm_remove_channel"
	bl_label = "Remove Material Name"
	bl_options = {'REGISTER', 'UNDO'}
	bl_description = "Remove selected Texture Channel Name."
	
	index : bpy.props.IntProperty(name="Index", default=-1, description='Index of the item')

	@classmethod
	def poll(cls, context):
		return context.scene.lm_shader_channels

	def execute(self, context):
		if self.index < 0:
			self.index, channel, _ = get_channels(context)
		else:
			_, channel, _ = get_channels(context)

		channel.remove(self.index)

		context.scene.lm_shader_channel_idx = min(self.index, len(context.scene.lm_shader_channels) - 2)

		H.update_shader_channels(self, context)

		return {'FINISHED'}
