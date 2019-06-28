import bpy

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

    def execute(self, context):
        scn = context.scene
        name_list = [a.name for a in scn.lm_render_queue]
        if scn.lm_asset_list and scn.lm_asset_list[scn.lm_asset_list_idx].name not in name_list:
            c = scn.lm_render_queue.add()
            c.name = scn.lm_asset_list[scn.lm_asset_list_idx].name
            c.rendered = scn.lm_asset_list[scn.lm_asset_list_idx].rendered
            c.render_path = scn.lm_asset_list[scn.lm_asset_list_idx].render_path
            c.composited = scn.lm_asset_list[scn.lm_asset_list_idx].composited
            c.final_composite_filepath = scn.lm_asset_list[scn.lm_asset_list_idx].final_composite_filepath
            c.asset_path = scn.lm_asset_list[scn.lm_asset_list_idx].asset_path
            
            scn.lm_render_queue_idx = len(scn.lm_render_queue) - 1

        return {'FINISHED'}

class LM_UI_MoveAssetToRender(bpy.types.Operator):
    bl_idname = "scene.lm_move_asset_to_render"
    bl_label = "Move Asset To Render"
    bl_options = {'REGISTER', 'UNDO'}
    bl_description = "Move asset to render"

    direction: bpy.props.EnumProperty(items=[("UP", "Up", ""), ("DOWN", "Down", "")])

    def execute(self, context):
        idx, asset, _ = get_assets(context)

        if self.direction == "UP":
            nextidx = max(idx - 1, 0)
        elif self.direction == "DOWN":
            nextidx = min(idx + 1, len(asset) - 1)

        asset.move(idx, nextidx)
        context.scene.lm_asset_list_idx = nextidx

        return {'FINISHED'}


class LM_UI_ClearAssetToRenderQueueList(bpy.types.Operator):
    bl_idname = "scene.lm_clear_asset_to_render_queue_list"
    bl_label = "Clear all assets of render queue"
    bl_options = {'REGISTER', 'UNDO'}
    bl_description = "Clear all assets of render queue."

    @classmethod
    def poll(cls, context):
        return context.scene.lm_render_queue

    def execute(self, context):
        context.scene.lm_render_queue.clear()

        return {'FINISHED'}


class LM_UI_RemoveAssetToRender(bpy.types.Operator):
    bl_idname = "scene.lm_remove_asset_to_render"
    bl_label = "Remove selected asset to render"
    bl_options = {'REGISTER', 'UNDO'}
    bl_description = "Remove selected asset to render."

    @classmethod
    def poll(cls, context):
        return context.scene.lm_render_queue and context.scene.lm_render_queue_idx is not None

    def execute(self, context):
        idx, _, _ = get_assets(context)

        context.scene.lm_render_queue.remove(idx)

        return {'FINISHED'}
