import bpy
import os
from os import path
from . import variables as V

bl_info = {
    "name": "Lineup Maker : Import Files",
    "author": "Tilapiatsu",
    "version": (1, 0, 0, 0),
    "blender": (2, 80, 0),
    "location": "View3D",
    "category": "Object",
}
def get_layer_collection(layer_collection, collection_name):
    found = None
    if (layer_collection.name == collection_name):
        return layer_collection
    for layer in layer_collection.children:
        found = get_layer_collection(layer, collection_name)
        if found:
            return found

def create_asset_collection(context, name):
    collections = bpy.data.collections
    if name in collections:
        return collections[name]
    else:
        new_collection = bpy.data.collections.new(name)
        context.collection.children.link(new_collection)
        return new_collection

def set_active_collection(context, name):
    context.view_layer.active_layer_collection = get_layer_collection(context.view_layer.layer_collection, name)

class LM_OP_ImportFiles(bpy.types.Operator):
    bl_idname = "scene.lm_importfiles"
    bl_label = "Lineup Maker: Import all files from source folder"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        folder_src = bpy.path.abspath(context.scene.lm_asset_path)

        set_active_collection(context, V.LM_MASTER_COLLECTION)
        asset_collection = create_asset_collection(context, V.LM_ASSET_COLLECTION)
        set_active_collection(context, asset_collection.name)
        
        object_list = asset_collection.objects

        if path.isdir(folder_src):
            subfolders = [os.path.join(folder_src, f) for f in os.listdir(folder_src) if path.isdir(os.path.join(folder_src, f))]
            for subfolder in subfolders:
                files = [os.path.join(subfolder, f) for f in os.listdir(subfolder) if path.isfile(os.path.join(subfolder, f))]
                for f in files:
                    name,ext = path.splitext(path.basename(f))

                    curr_asset_collection = create_asset_collection(context, name)
                    set_active_collection(context, curr_asset_collection.name)

                    if ext.lower() == '.fbx':
                        bpy.ops.import_scene.fbx(filepath=f, filter_glob='*.fbx;', axis_forward='-Z', axis_up='Y')
                    
                    # register the current asset in scene variable
                    curr_asset = context.scene.lm_asset_list.add()
                    curr_asset.fileName = name

                    for o in curr_asset_collection.objects:
                        curr_asset.meshName += '{},'.format(o.name)
                    set_active_collection(context, asset_collection.name)
        return {'FINISHED'}

class LM_Asset_List(bpy.types.PropertyGroup):
    fileName = bpy.props.StringProperty(name="File Name")
    meshName = bpy.props.StringProperty(name="Mesh Name", default="")