import subprocess
import sys
from . import helper as H


def install_dependencies(V):
    H.create_folder_if_neeed(V.LM_DEPENDENCIES_PATH)
    if V.LM_DEPENDENCIES_PATH not in sys.path: sys.path.append(V.LM_DEPENDENCIES_PATH)
    subprocess.check_call([sys.executable, '-m', 'pip', 'install', '-U', *V.LM_DEPENDENCIES, '--target', V.LM_DEPENDENCIES_PATH])
