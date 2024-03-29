import bpy, json
from . import logger as L
from . import helper as H
from bpy_extras.io_utils import ExportHelper

def get_assets(context):
	idx = context.scene.lm_render_queue_idx
	assets = context.scene.lm_render_queue

	active = assets[idx] if assets else None

	return idx, assets, active

class LM_UI_AddAssetToRenderQueue(bpy.types.Operator):
	bl_idname = "scene.lm_add_asset_to_render_queue"
	bl_label = "Add Asset To Render Queue"
	bl_options = {'REGISTER', 'UNDO'}
	bl_description = "Add asset to render_ queue"

	asset_name : bpy.props.StringProperty(name="Asset Name", default="", description='Name of the asset to add to render queue')

	def execute(self, context):
		scn = context.scene
		name_list = [a.name for a in scn.lm_render_queue]
		if scn.lm_asset_list and self.asset_name not in name_list:
			c = scn.lm_render_queue.add()
			c.name = scn.lm_asset_list[self.asset_name].name
			c.rendered = scn.lm_asset_list[self.asset_name].rendered
			c.render_path = scn.lm_asset_list[self.asset_name].render_path
			c.composited = scn.lm_asset_list[self.asset_name].composited
			c.final_composite_filepath = scn.lm_asset_list[self.asset_name].final_composite_filepath
			c.asset_path = scn.lm_asset_list[self.asset_name].asset_path
			c.render_camera = scn.lm_asset_list[self.asset_name].render_camera
			c.checked = True
			
			scn.lm_render_queue_idx = len(scn.lm_render_queue) - 1

		return {'FINISHED'}


class LM_UI_AddNeedRenderToRenderQueue(bpy.types.Operator):
	bl_idname = "scene.lm_add_need_render_to_render_queue"
	bl_label = "Add Need render To Render Queue"
	bl_options = {'REGISTER', 'UNDO'}
	bl_description = "Add all need render asset to render_queue"

	def execute(self, context):
		scn = context.scene
		for a in scn.lm_asset_list:
			if a.need_render or not a.rendered :
				bpy.ops.scene.lm_add_asset_to_render_queue(asset_name=a.name)

		return {'FINISHED'}


class LM_UI_MoveAssetToRender(bpy.types.Operator):
	bl_idname = "scene.lm_move_asset_to_render"
	bl_label = "Move Asset To Render"
	bl_options = {'REGISTER', 'UNDO'}
	bl_description = "Move asset to render"

	direction: bpy.props.EnumProperty(items=[("UP", "Up", ""), ("DOWN", "Down", "")])

	def execute(self, context):
		idx, assets, _ = get_assets(context)

		if self.direction == "UP":
			nextidx = max(idx - 1, 0)
		elif self.direction == "DOWN":
			nextidx = min(idx + 1, len(assets) - 1)

		assets.move(idx, nextidx)
		context.scene.lm_asset_list_idx = nextidx

		return {'FINISHED'}


class LM_UI_ClearAssetFromRenderQueueList(bpy.types.Operator):
	bl_idname = "scene.lm_clear_asset_from_render_queue_list"
	bl_label = "Clear all assets of render queue"
	bl_options = {'REGISTER', 'UNDO'}
	bl_description = "Clear all assets of render queue."

	@classmethod
	def poll(cls, context):
		return context.scene.lm_render_queue

	def execute(self, context):
		context.scene.lm_render_queue.clear()

		return {'FINISHED'}


class LM_UI_RemoveAssetFromRenderQueue(bpy.types.Operator):
	bl_idname = "scene.lm_remove_asset_from_render_queue"
	bl_label = "Remove selected asset to render"
	bl_options = {'REGISTER', 'UNDO'}
	bl_description = "Remove selected asset to render."

	asset_name : bpy.props.StringProperty(name="Asset Name", default="", description='Name of the asset to remove')

	@classmethod
	def poll(cls, context):
		return context.scene.lm_render_queue

	def execute(self, context):
		H.remove_bpy_struct_item(context.scene.lm_render_queue, self.asset_name)

		return {'FINISHED'}

class LM_UI_DeleteRenderQueueAsset(bpy.types.Operator):
	bl_idname = "scene.lm_delete_render_queue_asset"
	bl_label = "Remove Selected asset from file"
	bl_options = {'REGISTER', 'UNDO'}
	bl_description = "Remove Selected asset from file."

	asset_name : bpy.props.StringProperty(name="Asset Name", default="", description='Name of the asset to remove')

	@classmethod
	def poll(cls, context):
		return context.scene.lm_import_list

	def invoke(self, context, event):
		wm = context.window_manager
		return wm.invoke_confirm(self, event)

	def execute(self, context):
		assets = []

		if len(self.asset_name):
			if self.asset_name in context.scene.lm_asset_list:	
				assets [self.asset_name]
		else:
			assets = [a.name for a in context.scene.lm_render_queue if a.checked]

		for a in assets:
			bpy.ops.scene.lm_remove_asset(asset_name = a)

		return {'FINISHED'}

	def draw(self, context):
		layout = self.layout
		col = layout.column()
		col.label(text='This operation will DEFINITELY delete the asset from your file')


class LM_UI_CheckAllRenderQueuedAsset(bpy.types.Operator):
	bl_idname = "scene.lm_check_all_render_queued_asset"
	bl_label = "Check all render queued asset"
	bl_options = {'REGISTER', 'UNDO'}
	bl_description = "Check all render queued asset"

	@classmethod
	def poll(cls, context):
		return context.scene.lm_render_queue

	def execute(self, context):
		for a in context.scene.lm_render_queue:
			a.checked = True

		return {'FINISHED'}

class LM_UI_UncheckAllRenderQueuedAsset(bpy.types.Operator):
	bl_idname = "scene.lm_uncheck_all_render_queued_asset"
	bl_label = "Uncheck all render queued asset"
	bl_options = {'REGISTER', 'UNDO'}
	bl_description = "Uncheck all render queued asset"

	@classmethod
	def poll(cls, context):
		return context.scene.lm_render_queue

	def execute(self, context):
		for a in context.scene.lm_render_queue:
			a.checked = False

		return {'FINISHED'}

class LM_UI_ExportRenderQueueList(bpy.types.Operator, ExportHelper):
	bl_idname = "scene.lm_export_queue_list"
	bl_label = "Export queue list"
	bl_options = {'REGISTER'}
	bl_description = "Export queue list"

	json_data = {'assets':[]}
	filename_ext = ".json"
	filter_glob: bpy.props.StringProperty(
		default="*.json",
		options={'HIDDEN'},
		maxlen=255,  # Max internal buffer length, longer would be clamped.
	)

	@classmethod
	def poll(cls, context):
		return context.scene.lm_render_queue

	def execute(self, context):
		for a in context.scene.lm_render_queue:
			if a.checked:
				asset = context.scene.lm_asset_list[a.name]
				self.json_data['assets'].append({'name':asset.name, 'fromFile':asset.from_file})


		with open(self.filepath, 'w', encoding='utf-8') as outfile:
			json.dump(self.json_data, outfile, ensure_ascii=False, indent=4)
		
		self.json_data = {'assets':[]}

		return {'FINISHED'}
