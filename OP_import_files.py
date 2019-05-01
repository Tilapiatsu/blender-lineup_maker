import bpy
import os,time
from os import path
from . import variables as V
from . import helper as H
from . import asset_format as A

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
        asset_collection = H.create_asset_collection(context, V.LM_ASSET_COLLECTION)
        H.set_active_collection(context, asset_collection.name)
        
        object_list = asset_collection.objects

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
                
                print(curr_asset.asset)


        return {'FINISHED'}
    
    def import_update_loop(self, context, function, mesh_files, asset_collection):
        for f in mesh_files:
            function()
            H.set_active_collection(context, asset_collection.name)

    def import_asset(self, context, mesh_path, texturepath):
        name,ext = path.splitext(path.basename(mesh_path))
        curr_asset_collection = H.create_asset_collection(context, name)
        H.set_active_collection(context, curr_asset_collection.name)

        print('Lineup Maker : Importing asset "{}"'.format(name))
        if ext.lower() == '.fbx':
            bpy.ops.import_scene.fbx(filepath=mesh_path, filter_glob='*.fbx;', axis_forward='-Z', axis_up='Y')
        
        # register the current asset in scene variable
        curr_asset = context.scene.lm_asset_list.add()
        curr_asset.name = name
        curr_asset.file_name = name
        curr_asset.last_update = path.getmtime(mesh_path)

        for t in texturepath:
            # Store textures as textureSet based on naming convention
            pass

        for o in curr_asset_collection.objects:
            curr_asset.mesh_name += '{},'.format(o.name)
            for m in o.material_slots:
                material_list = curr_asset.material_list.add()
                material_list.name = m.material.name
                material_list.material = m.material
        
    
    def update_asset(self, context, mesh_path, texturepath):
        name,ext = path.splitext(path.basename(mesh_path))
        curr_asset_collection = bpy.data.collections[name]
        H.set_active_collection(context, curr_asset_collection.name)

        curr_asset = context.scene.lm_asset_list[name]
        if curr_asset.last_update < path.getmtime(mesh_path):
            print('Lineup Maker : Updating asset "{}" : {}'.format(name, time.ctime(curr_asset.last_update)))
            print('Lineup Maker : Updating file "{}" : {}'.format(name, time.ctime(path.getmtime(mesh_path))))

            bpy.ops.object.select_all(action='DESELECT')
            for o in curr_asset_collection.objects:
                o.select_set(True)

            bpy.ops.object.delete()
            del curr_asset

            self.import_asset(context, mesh_path)


class LM_Material_List(bpy.types.PropertyGroup):
    material_name = bpy.props.StringProperty(name="Material Name")
    material = bpy.props.PointerProperty(name='Material', type=bpy.types.Material)

class LM_Mesh_List(bpy.types.PropertyGroup):
    mesh_name = bpy.props.StringProperty(name="Mesh Name")
    file_path = bpy.props.StringProperty(name="File Path")
    mesh = bpy.props.PointerProperty(name='Mesh', type=bpy.types.Object)
    material_list = bpy.props.CollectionProperty(type=LM_Material_List)

class LM_Texture_List(bpy.types.PropertyGroup):
    textureset_name = bpy.props.StringProperty(name="TextureSet Name")
    albedo = bpy.props.PointerProperty(name='Albedo', type=bpy.types.Texture)
    normal = bpy.props.PointerProperty(name='Normal', type=bpy.types.Texture)
    roughness = bpy.props.PointerProperty(name='Roughness', type=bpy.types.Texture)
    metalic = bpy.props.PointerProperty(name='Metalic', type=bpy.types.Texture)

class LM_Asset_List(bpy.types.PropertyGroup):
    last_update = bpy.props.FloatProperty(name="Last Update")
    mesh_list = bpy.props.CollectionProperty(type=LM_Mesh_List)
    material_list = bpy.props.CollectionProperty(type=LM_Material_List)
    texture_list = bpy.props.CollectionProperty(type=LM_Texture_List)

