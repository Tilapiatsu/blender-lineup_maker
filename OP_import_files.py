import bpy
import os,time
from os import path
from . import variables as V
from . import helper as H
from . import asset_format as A
from . import naming_convention as N

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

        H.set_active_collection(context, V.LM_MASTER_COLLECTION)
        asset_collection, _ = H.create_asset_collection(context, V.LM_ASSET_COLLECTION)
        H.set_active_collection(context, asset_collection.name)
        
        object_list = asset_collection.objects

        # Store the Global View_Layer
        global_view_layer = context.window.view_layer

        asset_view_layers = {}
        if path.isdir(folder_src):
            subfolders = [path.join(folder_src, f,) for f in os.listdir(folder_src) if path.isdir(os.path.join(folder_src, f))]
            for subfolder in subfolders:
                mesh_files = [path.join(subfolder, f) for f in os.listdir(subfolder) if path.isfile(os.path.join(subfolder, f)) and path.splitext(f)[1].lower() in V.LM_COMPATIBLE_MESH_FORMAT.keys()]
                texture_files = {}
                mesh_names = [path.basename(path.splitext(t)[0]) for t in mesh_files]
                for m in mesh_names:
                    texture_files[m] = [path.join(subfolder, m, t) for t in os.listdir(path.join(subfolder, m)) if path.isfile(os.path.join(subfolder, m, t)) and path.splitext(t)[1].lower() in V.LM_COMPATIBLE_TEXTURE_FORMAT.keys()]
                asset_name = path.basename(subfolder)
                curr_asset = A.BpyAsset(context, mesh_files, texture_files)
                
                if asset_name not in bpy.data.collections and asset_name not in context.scene.lm_asset_list:
                    curr_asset.import_asset()
                    H.set_active_collection(context, asset_collection.name)
                else:
                    curr_asset.update_asset()
                    H.set_active_collection(context, asset_collection.name)

                assigned = False
                for mesh_name in curr_asset.asset.keys():
                    for mat in context.scene.lm_asset_list[curr_asset.asset_name].mesh_list[mesh_name].material_list:
                        for t in curr_asset.asset[mesh_name][1].keys():
                            tnc = N.NamingConvention(context, t, context.scene.lm_texture_naming_convention)
                            mnc = N.NamingConvention(context, mat.name.lower(), context.scene.lm_texture_naming_convention)

                            if tnc == mnc:
                                curr_asset.feed_material(mat.material, curr_asset.asset[mesh_name][1][t])
                                assigned = True
                                break

                        else:
                            if not assigned:
                                print('Lineup Maker : No Texture found for material "{}"'.format(mat.name))

                del assigned

                curr_asset_view_layer = H.get_layer_collection(context.view_layer.layer_collection, curr_asset.asset_name)
                # Store asset colection view layer
                asset_view_layers[curr_asset_view_layer.name] = curr_asset_view_layer
                # Hide asset in Global View Layer
                curr_asset_view_layer.hide_viewport = True
            
            for name in asset_view_layers.keys():
                bpy.ops.scene.view_layer_add()
                context.window.view_layer.name = name

                for n, l in asset_view_layers.items():
                    if name != n:
                        curr_asset_view_layer = H.get_layer_collection(context.view_layer.layer_collection, n)
                        curr_asset_view_layer.hide_viewport = True
            
            # Set the global View_layer active
            context.window.view_layer = global_view_layer

        return {'FINISHED'}
