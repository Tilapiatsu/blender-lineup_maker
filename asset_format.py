import bpy
from . import variables as V
from . import helper as H
from os import path
import time
import sys

class BpyAsset(object):
    def __init__(self, context, meshes, textures):
        self.context = context
        self.asset_name = self.get_asset_name(meshes)
        self.asset_root = self.get_asset_root(meshes)
        self.meshes = meshes
        self.textures = textures
        
    # Decorators
    def check_asset_exist(func):
        def func_wrapper(self, *args, **kwargs):
            if self.asset_name in bpy.data.collections:
                return func(self, *args, **kwargs)
            else:
                print('Lineup Maker : Asset doesn\'t exist in current scene')
                return None
        return func_wrapper

    def check_length(func):
        def func_wrapper(self, *args, **kwargs):
            if not len(self.meshes):
                print('Lineup Maker : No file found in the asset folder')
                return None
            else:
                return func(self, *args, **kwargs)
        return func_wrapper
    # Methods
    def import_asset(self):
        self.import_mesh()
        self.import_texture()
    
    def update_asset(self):
        self.update_mesh()
        self.update_texture()

    def import_mesh(self, update=False):
        name,ext = path.splitext(path.basename(self.meshes[0]))

        if self.asset_name not in bpy.data.collections:
            curr_asset_collection = H.create_asset_collection(self.context, self.asset_name)
        else:
            curr_asset_collection = bpy.data.collections[self.asset_name]

        H.set_active_collection(self.context, curr_asset_collection.name)

        for i,f in enumerate(self.meshes):
            name,ext = path.splitext(path.basename(f))

            # Import asset
            if ext.lower() in V.LM_COMPATIBLE_MESH_FORMAT.keys():
                print('Lineup Maker : Importing mesh "{}"'.format(name))
                compatible_format = V.LM_COMPATIBLE_MESH_FORMAT[ext.lower()]
                kwargs = {}
                kwargs.update({'filepath':f})
                kwargs.update(compatible_format[1])
                compatible_format[0](**kwargs)
            else:
                print('Lineup Maker : Skipping file "{}"\n     Incompatible format'.format(f))
                continue
            
            # register the mesh in scene variable
            if update:
                curr_asset = self.context.scene.lm_asset_list[self.asset_name]
            else:
                curr_asset = self.context.scene.lm_asset_list.add()
                curr_asset.name = self.asset_name
            
            curr_asset.last_update = path.getmtime(f)

            if update:
                curr_mesh_list = curr_asset.mesh_list[i]
            else:
                curr_mesh_list = curr_asset.mesh_list.add()
                curr_mesh_list.file_path = f

            for o in curr_asset_collection.objects:
                curr_mesh_list.mesh_name = o.name
                curr_mesh_list.mesh = o

                for m in o.material_slots:
                    if m.name not in curr_asset.material_list:
                        material_list = curr_asset.material_list.add()
                        material_list.material_name = m.material.name
                        material_list.material = m.material

                    curr_mesh_material_list = curr_mesh_list.material_list.add()
                    curr_mesh_material_list.material_name = m.material.name
                    curr_mesh_material_list.material = m.material
    

    @check_length
    def update_mesh(self):
        name,ext = path.splitext(path.basename(self.meshes[0]))
        if self.asset_name not in bpy.data.collections:
            curr_asset_collection = H.create_asset_collection(self.context, self.asset_name)
        else:
            curr_asset_collection = bpy.data.collections[self.asset_name]

        H.set_active_collection(self.context, self.asset_name)

        if self.asset_name not in self.context.scene.lm_asset_list:
            self.remove_objects()
            self.import_mesh(update=True)
        else:
            curr_asset = self.context.scene.lm_asset_list[self.asset_name]

            for f in self.meshes:
                if curr_asset.last_update < path.getmtime(f):
                    print('Lineup Maker : Updating asset "{}" : {}'.format(name, time.ctime(curr_asset.last_update)))
                    print('Lineup Maker : Updating file "{}" : {}'.format(name, time.ctime(path.getmtime(f))))

                    self.remove_objects()
                    self.context.scene.update()
                    self.import_mesh(update=True)
                else:
                    print('Lineup Maker : Asset "{}" is already up to date'.format(name))

    def import_texture(self):
        pass
    
    def update_texture(self):
        pass

    # Helper
    def get_asset_name(self, meshes):
        return path.basename(path.dirname(meshes[0]))
    
    def get_asset_root(self, meshes):
        return path.dirname(meshes[0])

    @check_asset_exist
    def select_asset(self):
        bpy.data.collections[self.asset_name].select_set(True)


    @check_asset_exist    
    def select_objects(self):
        curr_asset_collection = bpy.data.collections[self.asset_name]
        bpy.ops.object.select_all(action='DESELECT')
        for o in curr_asset_collection.all_objects:
            o.select_set(True)

    
    def remove_objects(self):
        self.select_objects()

        bpy.ops.object.delete()


    @check_asset_exist
    def print_asset_object_name(self):
        curr_asset_collection = bpy.data.collections[self.asset_name]
        for o in curr_asset_collection.all_objects:
            print(o.name)

class BpyAssetFBX(BpyAsset):
    def __init__(self, context, meshes, textures):
        super(BpyAssetFBX, self).__init__(context, meshes, textures)