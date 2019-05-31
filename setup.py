import bpy
from os import path

blender_path = path.dirname(bpy.app.binary_path)
blender_version = bpy.app.version_string.split(' ')[0]
blender_python_bin = path.join(blender_path, blender_version, 'python\\bin')