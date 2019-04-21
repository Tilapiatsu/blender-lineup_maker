# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful, but
# WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTIBILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU
# General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program. If not, see <http://www.gnu.org/licenses/>.

import bpy
from .OP_import_files import *
from .UI_properties_pannel import *

bl_info = {
    "name" : "Lineup Maker",
    "author" : "Tilapiatsu",
    "description" : "",
    "blender" : (2, 80, 0),
    "location" : "",
    "warning" : "",
    "category" : "Generic"
}

classes = (
    LM_OP_ImportFiles,
    LM_PT_main
)

def register():
    bpy.types.Scene.lm_asset_path = bpy.props.StringProperty(
                                    name="Assets Path",
                                    subtype='DIR_PATH',
                                    default="",
                                    update = None,
                                    description = 'Path to the folder containing the assets'      
                                    )
    bpy.types.Scene.lm_naming_convention = bpy.props.StringProperty(
                                    name="Naming Convetion",
                                    subtype='NONE',
                                    default="prefix_<PROJECT>_<TEAM>_<ASSET_NAME>_<INCR>_<GENDER>_suffix",
                                    update = None,
                                    description = 'Naming Convention'      
                                    )                          
    for cls in classes:
        print('register :', cls.bl_label)
        bpy.utils.register_class(cls)
    
    


def unregister():
    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)
    
    del bpy.types.Scene.lm_asset_path 

if __name__ == "__main__":
    register()