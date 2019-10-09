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

    if not path.exists(blender_python_pip) and not path.exists(pip_file):
        subprocess.call('curl https://bootstrap.pypa.io/get-pip.py -o get-pip.py')
        subprocess.call(path.join(blender_python_bin, 'python get-pip.py'))


    subprocess.call(pip_file + ' install pillow')
    subprocess.call(pip_file + ' install fpdf')
