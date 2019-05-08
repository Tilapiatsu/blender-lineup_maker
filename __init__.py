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
from .OP_ui_list_texture import *
from .OP_ui_list_channel import *
from .OP_ui_list_shader import *

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
    LM_PT_NamingConvention,
    LM_PT_TextureSetSettings,
    LM_PT_main,
    LM_Material_List,
    LM_Mesh_List,
    LM_Texture_List,
    LM_Asset_List,
    LM_TextureChannels,
    LM_Channels,
    LM_Shaders,
    LM_TextureSet_UIList,
    LM_Channel_UIList,
    LM_Shader_UIList,
    LM_UI_MoveChannel,
    LM_UI_RenameChannel,
    LM_UI_ClearChannel,
    LM_UI_RemoveChannel,
    LM_UI_MoveShader,
    LM_UI_RenameShader,
    LM_UI_ClearShader,
    LM_UI_RemoveShader,
    LM_UI_MoveTexture,
    LM_UI_RenameTexture,
    LM_UI_ClearTexture,
    LM_UI_RemoveTexture
)

def update_textureChannelName(self, context):
    scn = context.scene
    if scn.lm_avoid_update:
        scn.lm_avoid_update = False
        return

    else:
        if scn.lm_texture_channel_name and scn.lm_texture_channel_name not in scn.lm_texture_channels and len(scn.lm_channels) and len(scn.lm_shaders):
            tc = scn.lm_texture_channels.add()
            tc.name = scn.lm_texture_channel_name
            tc.channel = scn.lm_channels[scn.lm_channel_idx].name
            tc.shader = scn.lm_shaders[scn.lm_shader_idx].name

            scn.lm_texture_channel_idx = len(scn.lm_texture_channels) - 1

        scn.lm_avoid_update = True
        scn.lm_texture_channel_name = ""

def update_channelName(self, context):
    scn = context.scene
    if scn.lm_avoid_update:
        scn.lm_avoid_update = False
        return

    else:
        if scn.lm_channel_name and scn.lm_channel_name not in scn.lm_channels and len(scn.lm_shaders):
            c = scn.lm_channels.add()
            c.name = scn.lm_channel_name
            c.shader = scn.lm_shaders[scn.lm_shader_idx].name

            scn.lm_channel_idx = len(scn.lm_texture_channels) - 1

        scn.lm_avoid_update = True
        scn.lm_channel_name = ""

def update_shaderName(self, context):
    scn = context.scene
    if scn.lm_avoid_update:
        scn.lm_avoid_update = False
        return

    else:
        if scn.lm_shader_name and scn.lm_shader_name not in scn.lm_shaders:
            c = scn.lm_shaders.add()
            c.name = scn.lm_shader_name

            scn.lm_shader_idx = len(scn.lm_shaders) - 1

        scn.lm_avoid_update = True
        scn.lm_shader_name = ""

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

    bpy.types.Scene.lm_texture_channel_idx = bpy.props.IntProperty()
    bpy.types.Scene.lm_channel_idx = bpy.props.IntProperty()
    bpy.types.Scene.lm_shader_idx = bpy.props.IntProperty()

    bpy.types.Scene.lm_texture_channel_name = bpy.props.StringProperty(name="Add Texture Channel", update=update_textureChannelName)
    bpy.types.Scene.lm_channel_name = bpy.props.StringProperty(name="Add Channel", update=update_channelName)
    bpy.types.Scene.lm_shader_name = bpy.props.StringProperty(name="Add Shader", update=update_shaderName)

    for cls in classes:
        bpy.utils.register_class(cls)
    
    bpy.types.Scene.lm_asset_list = bpy.props.CollectionProperty(type=LM_Asset_List)

    bpy.types.Scene.lm_texture_channels =  bpy.props.CollectionProperty(type=LM_TextureChannels)
    bpy.types.Scene.lm_channels =  bpy.props.CollectionProperty(type=LM_Channels)
    bpy.types.Scene.lm_shaders =  bpy.props.CollectionProperty(type=LM_Shaders)
    
    


def unregister():
    del bpy.types.Scene.lm_shaders
    del bpy.types.Scene.lm_channels
    del bpy.types.Scene.lm_texture_channels
    del bpy.types.Scene.lm_asset_list

    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)
    
    del bpy.types.Scene.lm_avoid_update
    del bpy.types.Scene.lm_shader_name
    del bpy.types.Scene.lm_shader_idx
    del bpy.types.Scene.lm_channel_name
    del bpy.types.Scene.lm_channel_idx
    del bpy.types.Scene.lm_texture_channel_name
    del bpy.types.Scene.lm_texture_channel_idx
    del bpy.types.Scene.lm_texture_naming_convention
    del bpy.types.Scene.lm_mesh_naming_convention
    del bpy.types.Scene.lm_asset_naming_convention
    del bpy.types.Scene.lm_asset_path 
      

if __name__ == "__main__":
    register()