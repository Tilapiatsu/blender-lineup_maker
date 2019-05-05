import bpy
import re
import os.path

from . import variables as V
from . import preferences as P

class NamingConvention(object):
    def __init__(self, file_name, naming_convention):
        self.file_name = file_name
        