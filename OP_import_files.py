import bpy
import os
from os import path
bl_info = {
    "name": "Lineup Maker : Import Files",
    "author": "Tilapiatsu",
    "version": (1, 0, 0, 0),
    "blender": (2, 80, 0),
    "location": "View3D",
    "category": "Object",
}

class LM_OP_ImportFiles(bpy.types.Operator):
    bl_idname = "scene.lm_importfiles"
    bl_label = "Lineup Maker: Import all files from source folder"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        folder_src = bpy.path.abspath(context.scene.lm_asset_path)
        if path.isdir(folder_src):
            subfolders = [os.path.join(folder_src, f) for f in os.listdir(folder_src) if path.isdir(os.path.join(folder_src, f))]
            for subfolder in subfolders:
                files = [os.path.join(subfolder, f) for f in os.listdir(subfolder) if path.isfile(os.path.join(subfolder, f))]
                for f in files:
                    if path.splitext(f)[1].lower() == '.fbx':
                        bpy.ops.import_scene.fbx(filepath=f, filter_glob='*.fbx;', axis_forward='-Z', axis_up='Y')
        return {'FINISHED'}
