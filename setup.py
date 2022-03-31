import subprocess
import sys

from os import path
from . import variable as V

def install_dependencies():
    if V.LM_DEPENDENCIES_PATH not in sys.path: sys.path.append(V.LM_DEPENDENCIES_PATH)
    subprocess.check_call([sys.executable, '-m', 'pip', 'install', '-U', *V.LM_DEPENDENCIES, '--target', V.LM_DEPENDENCIES_PATH])
