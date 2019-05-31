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

    # pip_url = 'https://bootstrap.pypa.io/get-pip.py'

    # r = requests.get(pip_url)

    # with open(os.path.join(blender_python_bin, 'get-pip.py'), 'wb') as f:  
    #     f.write(r.content)
    pip_file = path.join(blender_python_pip, 'pip.exe')
    print(pip_file)
    subprocess.call(pip_file + ' install pillow')
