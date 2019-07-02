import bpy

def get_assets(context):
    idx = context.scene.lm_asset_list_idx
    assets = context.scene.lm_asset_list

    active = assets[idx] if assets else None

    return idx, assets, active

def remove_asset(self, context, asset, index, remove=True):
    self.report({'INFO'},'Remove {}'.format(asset.name))
    try:
        context.window.view_layer = context.scene.view_layers[asset.view_layer]
    except KeyError as e:
        print(e)

    if context.scene.lm_asset_list[asset.name].collection:
        for m in context.scene.lm_asset_list[asset.name].material_list:
            try:
                if m.material:
                    bpy.data.materials.remove(bpy.data.materials[m.material.name])
            except KeyError as e:
                print(e)
        for o in context.scene.lm_asset_list[asset.name].collection.all_objects:
            bpy.ops.object.select_all(action='DESELECT')
            bpy.data.objects[o.name].select_set(True)
            bpy.ops.object.delete() 
        bpy.data.collections.remove(context.scene.lm_asset_list[asset.name].collection)
    context.scene.view_layers.remove(context.scene.view_layers[context.scene.lm_asset_list[asset.name].view_layer])
    if remove:
        context.scene.lm_asset_list.remove(index)
    idx, _, _ = get_assets(context)
    
    if idx > 0 :
        context.scene.lm_asset_list_idx = idx - 1

    
    


class LM_UI_MoveAsset(bpy.types.Operator):
    bl_idname = "scene.lm_move_asset"
    bl_label = "Move Keyword"
    bl_options = {'REGISTER', 'UNDO'}
    bl_description = "Move Camera keyword Name up or down.\nThis controls the position in the Menu."

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
            remove_asset(self, context, asset, 0, remove=False)
        
        context.scene.lm_asset_list.clear()

        return {'FINISHED'}


class LM_UI_RemoveAsset(bpy.types.Operator):
    bl_idname = "scene.lm_remove_asset"
    bl_label = "Remove Selected Asset"
    bl_options = {'REGISTER', 'UNDO'}
    bl_description = "Remove selected Asset."

    @classmethod
    def poll(cls, context):
        return context.scene.lm_asset_list

    def execute(self, context):
        idx, asset, _ = get_assets(context)

        remove_asset(self, context, asset[idx], idx)

        return {'FINISHED'}


class LM_UI_OpenRenderFolder(bpy.types.Operator):
    bl_idname = "scene.lm_open_render_folder"
    bl_label = "Open Render Folder"
    bl_options = {'REGISTER', 'UNDO'}
    bl_description = "Open Render Folder"

    @classmethod
    def poll(cls, context):
        return context.scene.lm_asset_list and context.scene.lm_asset_list_idx is not None

    def execute(self, context):
        bpy.ops.scene.lm_openfolder(folder_path=context.scene.lm_asset_list[context.scene.lm_asset_list_idx].render_path)

        return {'FINISHED'}

class LM_UI_OpenAssetFolder(bpy.types.Operator):
    bl_idname = "scene.lm_open_asset_folder"
    bl_label = "Open Asset Folder"
    bl_options = {'REGISTER', 'UNDO'}
    bl_description = "Open Render Folder"

    @classmethod
    def poll(cls, context):
        return context.scene.lm_asset_list and context.scene.lm_asset_list_idx is not None

    def execute(self, context):
        bpy.ops.scene.lm_openfolder(folder_path=context.scene.lm_asset_list[context.scene.lm_asset_list_idx].asset_path)

        return {'FINISHED'}