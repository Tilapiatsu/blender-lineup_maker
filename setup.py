import subprocess
import sys

from os import path

dependencies = ['Pillow', 'fpdf']

def install_dependencies():
    current_dir = path.dirname(path.realpath(__file__))
    LineupMaker_dependencies_path = path.join(current_dir, 'LineupMakerDependencies')
    if LineupMaker_dependencies_path not in sys.path: sys.path.append(LineupMaker_dependencies_path)

    subprocess.check_call([sys.executable, '-m', 'pip', 'install', '-U', *dependencies, '--target', LineupMaker_dependencies_path])
