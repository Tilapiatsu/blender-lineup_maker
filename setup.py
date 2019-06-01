import bpy
import subprocess
import pip
# import requests
from os import path

def install_dependencies():
    blender_path = path.dirname(bpy.app.binary_path)
    blender_version = bpy.app.version_string.split(' ')[0]
    blender_python_bin = path.join(blender_path, blender_version, 'python\\bin')
    blender_python_pip = path.join(blender_path, blender_version, 'python\\Scripts')

    pip_file = path.join(blender_python_pip, 'pip.exe')

    subprocess.call(pip_file + ' install pillow')
    subprocess.call(pip_file + ' install fpdf')
