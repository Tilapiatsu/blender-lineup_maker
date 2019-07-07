import bpy
import os, subprocess
from . import logger as L

class LM_OP_OpenFolder(bpy.types.Operator):
    bl_idname = "scene.lm_openfolder"
    bl_label = "Lineup Maker: OpenFolder"
    bl_options = {'REGISTER', 'UNDO'}

    folder_path : bpy.props.StringProperty(name="Folder Path", subtype='DIR_PATH',default="", description='Path to the folder to open')

    def execute(self, context):
        self.folder_path = bpy.path.abspath(self.folder_path)
        
        if os.path.isdir(self.folder_path):
            print('Opening folder {}'.format(self.folder_path))
            subprocess.Popen(r'explorer /open,"{}"'.format(self.folder_path))
        else:
            print('Lineup Maker : The folder path "{}" is not valid'.format(self.folder_path))

        return {'FINISHED'}