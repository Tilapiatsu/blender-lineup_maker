import bpy

def get_assets(context):
    idx = context.scene.lm_asset_to_render_list_idx
    assets = context.scene.lm_asset_to_render_list

    active = assets[idx] if assets else None

    return idx, assets, active

class LM_UI_AddAssetToRender(bpy.types.Operator):
    bl_idname = "scene.lm_add_asset_to_render"
    bl_label = "Add Asset To Render"
    bl_options = {'REGISTER', 'UNDO'}
    bl_description = "Add asset to render"

    def execute(self, context):
        scn = context.scene
        name_list = [a.name for a in scn.lm_asset_to_render_list]
        if scn.lm_asset_list and scn.lm_asset_list[scn.lm_asset_list_idx].name not in name_list:
            c = scn.lm_asset_to_render_list.add()
            c.name = scn.lm_asset_list[scn.lm_asset_list_idx].name
            c.rendered = scn.lm_asset_list[scn.lm_asset_list_idx].rendered
            
            scn.lm_asset_to_render_list_idx = len(scn.lm_asset_to_render_list) - 1

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


class LM_UI_ClearAssetToRenderList(bpy.types.Operator):
    bl_idname = "scene.lm_clear_asset_to_render_list"
    bl_label = "Clear all assets to render"
    bl_options = {'REGISTER', 'UNDO'}
    bl_description = "Clear all assets to render."

    @classmethod
    def poll(cls, context):
        return context.scene.lm_asset_to_render_list

    def execute(self, context):
        context.scene.lm_asset_to_render_list.clear()

        return {'FINISHED'}


class LM_UI_RemoveAssetToRender(bpy.types.Operator):
    bl_idname = "scene.lm_remove_asset_to_render"
    bl_label = "Remove selected asset to render"
    bl_options = {'REGISTER', 'UNDO'}
    bl_description = "Remove selected asset to render."

    @classmethod
    def poll(cls, context):
        return context.scene.lm_asset_to_render_list

    def execute(self, context):
        idx, _, _ = get_assets(context)

        context.scene.lm_asset_to_render_list.remove(idx)

        return {'FINISHED'}
