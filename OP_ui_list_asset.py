import bpy
from os import path
from . import helper as H
from . import logger as L

def get_assets(context, name):
    H.renumber_assets(context)
    assets = context.scene.lm_asset_list
    if name in context.scene.lm_asset_list:
        idx = context.scene.lm_asset_list[name].asset_index
    else:
        idx = 0

    active = assets[idx] if assets else None

    return idx, assets, active

def remove_asset(self, context, asset, index, remove=True):
    self.report({'INFO'},'Remove {}'.format(asset.name))
    try:
        context.window.view_layer = context.scene.view_layers[asset.view_layer]
    except KeyError as e:
        print(e)

    if context.scene.lm_asset_list[asset.name].collection:
        H.remove_asset(context, asset.name, False)

    try:
        context.scene.view_layers.remove(context.scene.view_layers[context.scene.lm_asset_list[asset.name].view_layer])
    except KeyError as e:
        print(e)

    if remove:
        print("Removing asset : {}".format(context.scene.lm_asset_list[index].name))
        context.scene.lm_asset_list.remove(index)
        context.scene.lm_asset_list_idx = index - 1 if index else 0

        H.remove_bpy_struct_item(context.scene.lm_last_render_list, asset.name)

    
    H.renumber_assets(context)
    idx, _, _ = get_assets(context, asset.name)

    
    


class LM_UI_MoveAsset(bpy.types.Operator):
    bl_idname = "scene.lm_move_asset"
    bl_label = "Move Keyword"
    bl_options = {'REGISTER', 'UNDO'}
    bl_description = "Move Camera keyword Name up or down.\nThis controls the position in the Menu."

    direction: bpy.props.EnumProperty(items=[("UP", "Up", ""), ("DOWN", "Down", "")])
    asset_name : bpy.props.StringProperty(name="Asset Name", default="", description='Name of the asset to move')

    def execute(self, context):
        idx, asset, _ = get_assets(context, self.asset_name)

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

    asset_name : bpy.props.StringProperty(name="Asset Name", default="", description='Name of the asset to remove')

    @classmethod
    def poll(cls, context):
        return context.scene.lm_asset_list

    def execute(self, context):
        idx, asset, _ = get_assets(context, self.asset_name)

        remove_asset(self, context, asset[self.asset_name], idx)

        return {'FINISHED'}


class LM_UI_OpenRenderFolder(bpy.types.Operator):
    bl_idname = "scene.lm_open_render_folder"
    bl_label = "Open Render Folder"
    bl_options = {'REGISTER', 'UNDO'}
    bl_description = "Open Render Folder"

    asset_name : bpy.props.StringProperty(name="Asset Name", default="", description='Name of the asset folder to Open')

    @classmethod
    def poll(cls, context):
        return context.scene.lm_asset_list

    def execute(self, context):
        bpy.ops.scene.lm_openfolder(folder_path=context.scene.lm_asset_list[self.asset_name].render_path)

        return {'FINISHED'}

class LM_UI_OpenAssetFolder(bpy.types.Operator):
    bl_idname = "scene.lm_open_asset_folder"
    bl_label = "Open Asset Folder"
    bl_options = {'REGISTER', 'UNDO'}
    bl_description = "Open Asset Folder"

    asset_name : bpy.props.StringProperty(name="Asset Name", default="", description='Name of the asset folder to Open')

    @classmethod
    def poll(cls, context):
        return context.scene.lm_asset_list

    def execute(self, context):
        bpy.ops.scene.lm_openfolder(folder_path=context.scene.lm_asset_list[self.asset_name].asset_path)

        return {'FINISHED'}

class LM_UI_ShowAsset(bpy.types.Operator):
    bl_idname = "scene.lm_show_asset"
    bl_label = "Show Asset"
    bl_options = {'REGISTER', 'UNDO'}
    bl_description = "Show Asset"

    asset_name : bpy.props.StringProperty(name="Asset Name", default="", description='Name of the asset to show')

    @classmethod
    def poll(cls, context):
        return context.scene.lm_asset_list

    def execute(self, context):
        
        context.window.view_layer = context.scene.view_layers[self.asset_name]

        return {'FINISHED'}