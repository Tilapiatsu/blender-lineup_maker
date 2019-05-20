import bpy
import os,time
from os import path
from . import variables as V
from . import helper as H
from . import asset_format as A
from . import naming_convention as N

class LM_OP_ImportAssets(bpy.types.Operator):
    bl_idname = "scene.lm_importassets"
    bl_label = "Lineup Maker: Import all assets from source folder"
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
                context.scene.lm_asset_list[curr_asset_view_layer.name].view_layer = curr_asset_view_layer.name
                # Hide asset in Global View Layer
                curr_asset_view_layer.hide_viewport = True
            
            for name in asset_view_layers.keys():
                bpy.ops.scene.view_layer_add()
                context.window.view_layer.name = name

                for n, _ in asset_view_layers.items():
                    if name != n and name != context.scene.lm_render_collection.name:
                        curr_asset_view_layer = H.get_layer_collection(context.view_layer.layer_collection, n)
                        curr_asset_view_layer.exclude = True
            
            # Set the global View_layer active
            context.window.view_layer = global_view_layer

        return {'FINISHED'}

class LM_OP_RenderAssets(bpy.types.Operator):
    bl_idname = "scene.lm_renderassets"
    bl_label = "Lineup Maker: Render all assets in the scene"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        # Store renderpath
        initial_render_path = bpy.context.scene.render.filepath

        

        for asset in context.scene.lm_asset_list:
            # # switch view layer to the current asset
            
            
            render_path = os.path.abspath(os.path.join(os.path.abspath(context.scene.lm_render_path), asset.name))
            render_filename = render_path + '\\{}_'.format(asset.name)
            if not os.path.exists(render_path):
                os.makedirs(render_path)

            need_render = True
            if asset.render_date:
                need_render = False
                rendered_files = os.listdir(render_path)
                if len(rendered_files) < context.scene.frame_end-context.scene.frame_start:
                    need_render = True
                else:
                    for f in os.listdir(render_path):
                        if asset.render_date < asset.import_date:
                            need_render = True
                            break
                        
            if need_render:
                print(asset.view_layer)
                asset_view_layer = context.scene.view_layers[asset.view_layer]
                context.window.view_layer = asset_view_layer
                bpy.context.scene.render.filepath = render_filename
                bpy.ops.render.render(animation=True, write_still=True, use_viewport=True, layer=asset.view_layer)
                asset.render_date = time.time()
            else:
                print('Lineup Maker : Render of asset "{}" not needed'.format(asset.name) )



        # Restore renderpath
        bpy.context.scene.render.filepath = initial_render_path

        
        return {'FINISHED'}


class LM_OP_CompositeRenders(bpy.types.Operator):
    bl_idname = "scene.lm_compositerenders"
    bl_label = "Lineup Maker: composite all rendered assets"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        
        
        return {'FINISHED'}