import bpy
import subprocess
import sys

from os import path

def install_dependencies():
    current_dir = path.dirname(path.realpath(__file__))
    LineupMaker_dependencies_path = path.join(current_dir, 'LineupMakerDependencies')
    if LineupMaker_dependencies_path not in sys.path: sys.path.append(LineupMaker_dependencies_path)

    dependencies = ['pillow', 'fpdf']
    subprocess.check_call([bpy.app.binary_path_python, '-m', 'pip', 'install', *dependencies, '--target', LineupMaker_dependencies_path])
