import bpy
from . import logger as L
from . import helper as H

def get_keyword_values(context):
	
	keyword_values = context.scene.lm_keywords[context.scene.lm_keyword_idx].keyword_values
	idx = context.scene.lm_keyword_value_idx if context.scene.lm_keyword_value_idx < len(keyword_values) else 0

	active = keyword_values[idx] if keyword_values else None

	return idx, keyword_values, active

class LM_UI_AddKeywordValue(bpy.types.Operator):
	bl_idname = "scene.lm_add_keyword_value"
	bl_label = "Add Keyword"
	bl_options = {'REGISTER', 'UNDO'}
	bl_description = "Add Keyword value ( # reprent one digit, put many # to represent many )"

	new_keyword : bpy.props.StringProperty(name="New keyword value", default="", description='New Keyword Value')

	def invoke(self, context, event):
		self.new_keyword = ''
		wm = context.window_manager
		return wm.invoke_props_dialog(self)

	def execute(self, context):
		_, keyword_values, _ = get_keyword_values(context)
		for k in keyword_values:
			if k.name == self.new_keyword:
				self.report({'ERROR'}, 'Lineup Maker : Keyword Already Exists')
				return {'CANCELLED'}
		else:
			k = keyword_values.add()
			k.keyword_value = self.new_keyword
			H.update_keyword_values(self, context)
			return {'FINISHED'}

	def draw(self, context):
		layout = self.layout
		col = layout.column()
		col.prop(self, 'new_keyword')

class LM_UI_MoveKeywordValue(bpy.types.Operator):
	bl_idname = "scene.lm_move_keyword_value"
	bl_label = "Move Keyword value"
	bl_options = {'REGISTER', 'UNDO'}
	bl_description = "Move keyword_value Name up or down.\nThis controls the position in the Menu."

	direction: bpy.props.EnumProperty(items=[("UP", "Up", ""), ("DOWN", "Down", "")])

	def execute(self, context):
		idx, keyword_value, _ = get_keyword_values(context)

		if self.direction == "UP":
			nextidx = max(idx - 1, 0)
		elif self.direction == "DOWN":
			nextidx = min(idx + 1, len(keyword_value) - 1)

		keyword_value.move(idx, nextidx)
		context.scene.lm_keyword_value_idx = nextidx
		H.update_keyword_values(self, context)

		return {'FINISHED'}



class LM_UI_RenameKeywordValue(bpy.types.Operator):
	bl_idname = "scene.lm_rename_keyword_value"
	bl_label = "Rename Keyword value"
	bl_options = {'REGISTER', 'UNDO'}
	bl_description = "Rename the selected Keyword value Name"

	index : bpy.props.IntProperty(name="Index", default=-1, description='Index of the item')
	new_name: bpy.props.StringProperty(name="New Name")

	def check(self, context):
		return True

	@classmethod
	def poll(cls, context):
		return context.scene.lm_keywords

	def draw(self, context):
		layout = self.layout

		column = layout.column()

		column.prop(self, "new_name")

	def invoke(self, context, event):
		if self.index == -1:
			self.index, keyword_values, self.active = get_keyword_values(context)
		else:
			_, keyword_values, _ = get_keyword_values(context)
			if self.index >= len(keyword_values):
				self.report({'ERROR'}, f'Lineup Maker : No Keyword with index {self.index}')
				return {'CANCELLED'}
			
			self.active = keyword_values[self.index]
		
		self.new_name = self.active.keyword_value

		wm = context.window_manager
		return wm.invoke_props_dialog(self)

	def execute(self, context):
		if self.new_name:
			self.active.keyword_value = self.new_name
			H.update_keyword_values(self, context)

		return {'FINISHED'}


class LM_UI_ClearKeywordValue(bpy.types.Operator):
	bl_idname = "scene.lm_clear_keyword_values"
	bl_label = "Clear All Texture keyword_value"
	bl_options = {'REGISTER', 'UNDO'}
	bl_description = "Clear All Texture keyword_value Names."

	def execute(self, context):
		context.scene.lm_keywords[context.scene.lm_keyword_idx].keyword_values.clear()
		H.update_keyword_values(self, context)

		return {'FINISHED'}


class LM_UI_RemoveKeywordValue(bpy.types.Operator):
	bl_idname = "scene.lm_remove_keyword_value"
	bl_label = "Remove Material Name"
	bl_options = {'REGISTER', 'UNDO'}
	bl_description = "Remove selected Texture keyword_value Name."

	index : bpy.props.IntProperty(name="Index", default=-1, description='Index of the item')

	@classmethod
	def poll(cls, context):
		return context.scene.lm_keywords

	def execute(self, context):
		if self.index == -1:
			self.index, keyword_values, _ = get_keyword_values(context)
		else:
			_, keyword_values, _ = get_keyword_values(context)

		keyword_values.remove(self.index)

		context.scene.lm_keyword_value_idx = min(self.index, len(context.scene.lm_keywords) - 1)
		H.update_keyword_values(self, context)

		return {'FINISHED'}
