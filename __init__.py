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
from .preferences import *
from .properties import *

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
    LM_Preferences,
    LM_OP_ImportFiles,
    LM_PT_main,
    LM_Material_List,
    LM_Mesh_List,
    LM_Texture_List,
    LM_Asset_List,
    LM_TextureChannels,
    LM_TextureSet_UIList
)

def update_textureChannelName(self, context):
    scn = context.scene
    if scn.lm_avoid_update:
        scn.lm_avoid_update = False
        return

    else:
        if scn.lm_texture_channel_name and scn.lm_texture_channel_name not in scn.lm_texture_channels:
            tc = scn.lm_texture_channels.add()
            tc.name = scn.lm_texture_channel_name

            scn.lm_texture_channels_idx = len(scn.lm_texture_channels) - 1

        scn.lm_avoid_update = True
        scn.lm_texture_channel_name = ""

def register():
    bpy.types.Scene.lm_asset_path = bpy.props.StringProperty(
                                    name="Assets Path",
                                    subtype='DIR_PATH',
                                    default="",
                                    update = None,
                                    description = 'Path to the folder containing the assets'      
                                    )

    bpy.types.Scene.lm_asset_naming_convention = bpy.props.StringProperty(
                                    name="Asset Naming Convetion",
                                    subtype='NONE',
                                    default="<PROJECT>_<TEAM>_<CATEGORY>_<INCR>_<GENDER>",
                                    update = None,
                                    description = 'Naming Convention'      
                                    )
    bpy.types.Scene.lm_mesh_naming_convention = bpy.props.StringProperty(
                                    name="Mesh Naming Convetion",
                                    subtype='NONE',
                                    default="<ASSETNAME>_<PLUGNAME>_suffix",
                                    update = None,
                                    description = 'Naming Convention'      
                                    )
    
    bpy.types.Scene.lm_texture_naming_convention = bpy.props.StringProperty(
                                    name="Texture Naming Convetion",
                                    subtype='NONE',
                                    default="<ASSETNAME>_<TINCR>_<MATID>_suffix",
                                    update = None,
                                    description = 'Naming Convention'
                                    )
    bpy.types.Scene.lm_avoid_update = bpy.props.BoolProperty()
    bpy.types.Scene.lm_texture_channels_idx = bpy.props.IntProperty()

    bpy.types.Scene.lm_texture_channel_name = bpy.props.StringProperty(name="Add Texture Channel", update=update_textureChannelName)

    for cls in classes:
        bpy.utils.register_class(cls)
    
    bpy.types.Scene.lm_asset_list = bpy.props.CollectionProperty(type=LM_Asset_List)
    bpy.types.Scene.lm_texture_channels =  bpy.props.CollectionProperty(type=LM_TextureChannels)
    
    


def unregister():
    del bpy.types.Scene.lm_texture_channels
    del bpy.types.Scene.lm_asset_list

    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)
    
    del bpy.types.Scene.lm_avoid_update
    del bpy.types.Scene.lm_texture_channel_name
    del bpy.types.Scene.lm_texture_channels_idx
    del bpy.types.Scene.lm_texture_naming_convention
    del bpy.types.Scene.lm_mesh_naming_convention
    del bpy.types.Scene.lm_asset_naming_convention
    del bpy.types.Scene.lm_asset_path 
      

if __name__ == "__main__":
    register()