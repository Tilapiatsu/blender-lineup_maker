import bpy
import os,time
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
            subfolders = [path.join(folder_src, f,) for f in os.listdir(folder_src) if path.isdir(os.path.join(folder_src, f))]
            for subfolder in subfolders:
                mesh_files = [path.join(subfolder, f) for f in os.listdir(subfolder) if path.isfile(os.path.join(subfolder, f)) and path.splitext(f)[1].lower() in V.LM_COMPATIBLE_MESH_FORMAT.values()]
                for f in mesh_files:
                    texture_files = [path.join(subfolder, t) for t in os.listdir(subfolder) if path.isfile(os.path.join(subfolder, t)) and path.splitext(t)[1].lower() in V.LM_COMPATIBLE_TEXTURE_FORMAT.values()]
                    name,ext = path.splitext(path.basename(f))

                    if name not in bpy.data.collections:
                        self.import_asset(context, f, texture_files)
                        set_active_collection(context, asset_collection.name)
                    else:
                        self.update_asset(context, f, texture_files)
                        set_active_collection(context, asset_collection.name)

        return {'FINISHED'}
    
    def import_asset(self, context, mesh_path, texturepath):
        name,ext = path.splitext(path.basename(mesh_path))
        curr_asset_collection = create_asset_collection(context, name)
        set_active_collection(context, curr_asset_collection.name)

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
        set_active_collection(context, curr_asset_collection.name)

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

class LM_Mesh_List(bpy.types.PropertyGroup):
    mesh_name = bpy.props.StringProperty(name="Mesh Name")
    mesh = bpy.props.PointerProperty(name='Mesh', type=bpy.types.Object)

class LM_Material_List(bpy.types.PropertyGroup):
    material_name = bpy.props.StringProperty(name="Material Name")
    material = bpy.props.PointerProperty(name='Material', type=bpy.types.Material)

class LM_Texture_List(bpy.types.PropertyGroup):
    textureset_name = bpy.props.StringProperty(name="TextureSet Name")
    albedo = bpy.props.PointerProperty(name='Albedo', type=bpy.types.Texture)
    normal = bpy.props.PointerProperty(name='Normal', type=bpy.types.Texture)
    roughness = bpy.props.PointerProperty(name='Roughness', type=bpy.types.Texture)
    metalic = bpy.props.PointerProperty(name='Metalic', type=bpy.types.Texture)

class LM_Asset_List(bpy.types.PropertyGroup):
    last_update = bpy.props.FloatProperty(name="last_update")
    file_name = bpy.props.StringProperty(name="File Name")
    mesh_name = bpy.props.StringProperty(name="Mesh Name", default="")
    material_list = bpy.props.CollectionProperty(type=LM_Material_List)
    texture_list = bpy.props.CollectionProperty(type=LM_Texture_List)


