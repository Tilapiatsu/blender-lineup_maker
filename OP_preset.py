import bpy
import os, subprocess
from . import logger as L
from bpy_extras.io_utils import ImportHelper

class LM_OP_SavePreset(bpy.types.Operator, ImportHelper):
    bl_idname = "scene.lm_save_preset"
    bl_label = "Lineup Maker: Save Preset"
    bl_options = {'REGISTER', 'UNDO'}

    path : bpy.props.StringProperty(name="Save Path", subtype='DIR_PATH',default="", description='Path to the preset destination')

    def execute(self, context):
        self.path = bpy.path.abspath(self.path)
        
        if os.path.isdir(self.path):
            print('Saving preset in : {}'.format(self.path))
            subprocess.Popen(r'explorer /open,"{}"'.format(self.path))
        else:
            print('Lineup Maker : The folder path "{}" is not valid'.format(self.path))

        return {'FINISHED'}

class LM_OP_OpenPreset(bpy.types.Operator, ImportHelper):
    bl_idname = "scene.lm_open_preset"
    bl_label = "Lineup Maker: Open Preset"
    bl_options = {'REGISTER', 'UNDO'}

    path : bpy.props.StringProperty(name="Path", subtype='DIR_PATH',default="", description='Path to the folder to open')

    def execute(self, context):
        self.path = bpy.path.abspath(self.path)
        
        if os.path.isdir(self.path):
            print('Opening folder {}'.format(self.path))
            subprocess.Popen(r'explorer /open,"{}"'.format(self.path))
        else:
            print('Lineup Maker : The folder path "{}" is not valid'.format(self.path))

        return {'FINISHED'}