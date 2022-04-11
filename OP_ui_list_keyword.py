import bpy
from . import logger as L

def get_keywords(context):
	idx = context.scene.lm_keyword_idx
	keywords = context.scene.lm_keywords

	active = keywords[idx] if keywords else None

	return idx, keywords, active

class LM_UI_AddKeyword(bpy.types.Operator):
	bl_idname = "scene.lm_add_keywords"
	bl_label = "Add Keyword"
	bl_options = {'REGISTER', 'UNDO'}
	bl_description = "Add Keyword"

	new_keyword : bpy.props.StringProperty(name="New keyword", default="", description='New Keyword')

	def invoke(self, context, event):
		self.new_keyword = ''
		wm = context.window_manager
		return wm.invoke_props_dialog(self)

	def execute(self, context):
		for k in context.scene.lm_keywords:
			if k.name == self.new_keyword:
				self.report({'ERROR'}, 'Lineup Maker : Keyword Already Exists')
				return {'CANCELLED'}
		else:
			k = context.scene.lm_keywords.add()
			k.name = self.new_keyword

			return {'FINISHED'}

	def draw(self, context):
		layout = self.layout
		col = layout.column()
		col.prop(self, 'new_keyword')


class LM_UI_MoveKeyword(bpy.types.Operator):
	bl_idname = "scene.lm_move_keyword"
	bl_label = "Move Keyword"
	bl_options = {'REGISTER', 'UNDO'}
	bl_description = "Move keyword Name up or down.\nThis controls the position in the Menu."

	direction: bpy.props.EnumProperty(items=[("UP", "Up", ""), ("DOWN", "Down", "")])

	def execute(self, context):
		idx, keyword, _ = get_keywords(context)

		if self.direction == "UP":
			nextidx = max(idx - 1, 0)
		elif self.direction == "DOWN":
			nextidx = min(idx + 1, len(keyword) - 1)

		keyword.move(idx, nextidx)
		context.scene.lm_keyword_idx = nextidx

		return {'FINISHED'}



class LM_UI_RenameKeyword(bpy.types.Operator):
	bl_idname = "scene.lm_rename_keyword"
	bl_label = "Rename Keyword"
	bl_options = {'REGISTER', 'UNDO'}
	bl_description = "Rename the selected Keyword Name"

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
			self.index, _, self.active = get_keywords(context)
		else:
			if self.index >= len(context.scene.lm_keywords):
				self.report({'ERROR'}, f'Lineup Maker : No Keyword with index {self.index}')
				return {'CANCELLED'}
			self.active = context.scene.lm_keywords[self.index]
		
		self.new_name = self.active.name

		wm = context.window_manager
		return wm.invoke_props_dialog(self)

	def execute(self, context):
		if self.new_name:
			self.active.name = self.new_name

		return {'FINISHED'}


class LM_UI_ClearKeyword(bpy.types.Operator):
	bl_idname = "scene.lm_clear_keywords"
	bl_label = "Clear All Texture keyword"
	bl_options = {'REGISTER', 'UNDO'}
	bl_description = "Clear All Texture keyword Names."

	@classmethod
	def poll(cls, context):
		return context.scene.lm_keywords

	def execute(self, context):
		context.scene.lm_keywords.clear()

		return {'FINISHED'}


class LM_UI_RemoveKeyword(bpy.types.Operator):
	bl_idname = "scene.lm_remove_keyword"
	bl_label = "Remove Material Name"
	bl_options = {'REGISTER', 'UNDO'}
	bl_description = "Remove selected keyword Name."

	index : bpy.props.IntProperty(name="Index", default=-1, description='Index of the item')

	@classmethod
	def poll(cls, context):
		return context.scene.lm_keywords

	def execute(self, context):
		if self.index == -1:
			self.index, keyword, _ = get_keywords(context)
		else:
			_, keyword, _ = get_keywords(context)

		keyword.remove(self.index)

		context.scene.lm_keyword_idx = min(self.index, len(context.scene.lm_keywords) - 1)

		return {'FINISHED'}
