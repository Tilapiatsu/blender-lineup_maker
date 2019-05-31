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

# TODO: 
#   - Create PDF at the end of the compositing process
#   - Composite text on top of the image at the end of compositing process
#   - Create UI to Assign a camera by Category
#   - Create an operator to update/import render and compoosite in a row
#   - Create a render selected asset operator

#  DEPENDENCIES :
#      PyPDF: pip install PyPDF2
#      https://github.com/mstamy2/PyPDF2
# 
#   PIL Installation :
#   1. remove the modules/PIL folder, you don’t need it anymore
#   2. open ‘cmd’ as an admin and navigate to the blender installation folder (c:\program files\Blender Foundation…)
#   3. find the 2.78\python\bin folder, you are looking for a file called ‘python.exe’
#   4. download https://bootstrap.pypa.io/get-pip.py 13 and put it into the bin folder
#   5. in cmd, from the bin folder, type ‘python.exe get-pip.py’
#   6. when done, go one folder up(from bin) and go into the (new) Scripts folder. You are looking for a file called ‘pip.exe’
#   7. when you’ve found it, run ‘pip.exe install pillow’

import bpy

try:
    from .OP_main import *
except ModuleNotFoundError as e:
    print(e)
    from . import setup
    setup.install_dependencies()
    from .OP_main import *

from .OP_files import *
from .UI_properties_pannel import *
from .preferences import *
from .properties import *
from .OP_ui_list_texture import *
from .OP_ui_list_channel import *
from .OP_ui_list_shader import *
from .OP_ui_list_keyword import *
from .OP_ui_list_keyword_value import *
from .OP_ui_naming_convention import *

bl_info = {
    "name" : "Lineup Maker",
    "author" : "Tilapiatsu",
    "description" : "This addon will help you to import file from a directory, keep them up to date in your blend scene, and render each asset separatedly",
    "version": (1, 0, 0, 0),
    "blender" : (2, 80, 0),
    "location" : "",
    "warning" : "",
    "category" : "Generic"
}

classes = (
    LM_Preferences,
    LM_OP_ImportAssets,
    LM_OP_RenderAssets,
    LM_OP_OpenFolder,
    LM_OP_CompositeRenders,
    LM_PT_NamingConvention,
    LM_PT_TextureSetSettings,
    LM_PT_CompositLayout,
    LM_PT_main,
    LM_Render_List,
    LM_Material_List,
    LM_Mesh_List,
    LM_Texture_List,
    LM_Asset_List,
    LM_TextureChannels,
    LM_Channels,
    LM_Shaders,
    LM_Keywords,
    LM_KeywordValues,
    LM_TextureSet_UIList,
    LM_Channel_UIList,
    LM_Shader_UIList,
    LM_Keywords_UIList,
    LM_KeywordValues_UIList,
    LM_UI_MoveKeyword,
    LM_UI_RenameKeyword,
    LM_UI_ClearKeyword,
    LM_UI_RemoveKeyword,
    LM_UI_MoveKeywordValue,
    LM_UI_RenameKeywordValue,
    LM_UI_ClearKeywordValue,
    LM_UI_RemoveKeywordValue,
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
    LM_UI_RemoveTexture,
    LM_UI_AddAssetKeyword,
    LM_UI_AddMeshKeyword,
    LM_UI_AddTextureKeyword,
    LM_UI_RemoveAssetKeyword,
    LM_UI_RemoveMeshKeyword,
    LM_UI_RemoveTextureKeyword
)

def update_texture_channel_name(self, context):
    def is_valid_textureChannelName(scn):
        valid = False
        if scn.lm_texture_channel_name and len(scn.lm_channels):
            if not len(scn.lm_texture_channels):
                return True
            curr_channel_textures = [c.name for c in scn.lm_texture_channels if c.channel == scn.lm_channels[scn.lm_channel_idx].name]
            if scn.lm_texture_channel_name not in curr_channel_textures:
                return True
                    
        return valid

    scn = context.scene
    if scn.lm_avoid_update:
        scn.lm_avoid_update = False
        return

    else:
        if is_valid_textureChannelName(scn):
            tc = scn.lm_texture_channels.add()
            tc.name = scn.lm_texture_channel_name
            tc.channel = scn.lm_channels[scn.lm_channel_idx].name
            tc.shader = scn.lm_shaders[scn.lm_shader_idx].name

            scn.lm_texture_channel_idx = len(scn.lm_texture_channels) - 1

        scn.lm_avoid_update = True
        scn.lm_texture_channel_name = ""

def update_channel_name(self, context):
    def is_valid_channelName(scn):
        valid = False
        if scn.lm_channel_name and len(scn.lm_shaders):
            if not len(scn.lm_channels):
                return True
            curr_shader_channels = [c.name for c in scn.lm_channels if c.shader == scn.lm_shaders[scn.lm_shader_idx].name]
            if scn.lm_channel_name not in curr_shader_channels:
                return True
        
        return valid

    scn = context.scene
    if scn.lm_avoid_update:
        scn.lm_avoid_update = False
        return

    else:
        if is_valid_channelName(scn):
            c = scn.lm_channels.add()
            c.name = scn.lm_channel_name
            c.shader = scn.lm_shaders[scn.lm_shader_idx].name

            scn.lm_channel_idx = len(scn.lm_texture_channels) - 1

        scn.lm_avoid_update = True
        scn.lm_channel_name = ""

def update_shader_name(self, context):
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

def update_keyword_value(self, context):
    def is_valid_keyword_value(scn):
        valid = False
        if scn.lm_keyword_value and len(scn.lm_keywords):
            if not len(scn.lm_keywords):
                return True
            curr_keyword_values = [k.name for k in scn.lm_keyword_values if k.keyword == scn.lm_keywords[scn.lm_keyword_idx].name]
            if scn.lm_keyword_value not in curr_keyword_values:
                return True
        
        return valid

    scn = context.scene
    if scn.lm_avoid_update:
        scn.lm_avoid_update = False
        return

    else:
        if is_valid_keyword_value(scn):
            c = scn.lm_keyword_values.add()
            c.name = scn.lm_keyword_value
            c.keyword = scn.lm_keywords[scn.lm_keyword_idx].name

            scn.lm_keyword_value_idx = len(scn.lm_keyword_values) - 1

        scn.lm_avoid_update = True
        scn.lm_keyword_value = ""

def update_keyword_name(self, context):
    scn = context.scene
    if scn.lm_avoid_update:
        scn.lm_avoid_update = False
        return

    else:
        if scn.lm_keyword_name and scn.lm_keyword_name not in scn.lm_keywords:
            c = scn.lm_keywords.add()
            c.name = scn.lm_keyword_name

            scn.lm_keyword_idx = len(scn.lm_keywords) - 1

        scn.lm_avoid_update = True
        scn.lm_keyword_name = ""

def register():
    bpy.types.Scene.lm_asset_path = bpy.props.StringProperty(
                                    name="Assets Path",
                                    subtype='DIR_PATH',
                                    default="",
                                    update = None,
                                    description = 'Path to the folder containing the assets'      
                                    )
    
    bpy.types.Scene.lm_render_path = bpy.props.StringProperty(
                                    name="Rendered Asset Path",
                                    subtype='DIR_PATH',
                                    default="",
                                    update = None,
                                    description = 'Path to the folder containing the rendered assets'      
                                    )
    bpy.types.Scene.lm_render_collection = bpy.props.PointerProperty(type=bpy.types.Collection)
    bpy.types.Scene.lm_asset_collection = bpy.props.PointerProperty(type=bpy.types.Collection)
    bpy.types.Scene.lm_force_render = bpy.props.BoolProperty(name='Force Rendering of all assets')
    bpy.types.Scene.lm_asset_naming_convention = bpy.props.StringProperty(
                                    name="Asset Naming Convetion",
                                    subtype='NONE',
                                    update = None,
                                    description = 'Naming Convention'      
                                    )
    bpy.types.Scene.lm_mesh_naming_convention = bpy.props.StringProperty(
                                    name="Mesh Naming Convetion",
                                    subtype='NONE',
                                    update = None,
                                    description = 'Naming Convention'      
                                    )
    
    bpy.types.Scene.lm_texture_naming_convention = bpy.props.StringProperty(
                                    name="Texture Naming Convetion",
                                    subtype='NONE',
                                    update = None,
                                    description = 'Naming Convention'
                                    )

    bpy.types.Scene.lm_avoid_update = bpy.props.BoolProperty()

    bpy.types.Scene.lm_separator = bpy.props.StringProperty(name="Separator")
    bpy.types.Scene.lm_optionnal_asset_keyword = bpy.props.BoolProperty(default=False)
    bpy.types.Scene.lm_optionnal_mesh_keyword = bpy.props.BoolProperty(default=False)
    bpy.types.Scene.lm_optionnal_texture_keyword = bpy.props.BoolProperty(default=False)

    bpy.types.Scene.lm_keyword_idx = bpy.props.IntProperty()
    bpy.types.Scene.lm_keyword_value_idx = bpy.props.IntProperty()

    bpy.types.Scene.lm_keyword_name = bpy.props.StringProperty(name="Add Keyword", update=update_keyword_name)
    bpy.types.Scene.lm_keyword_value = bpy.props.StringProperty(name="Add Keyword Value", update=update_keyword_value)
    
    bpy.types.Scene.lm_texture_channel_idx = bpy.props.IntProperty()
    bpy.types.Scene.lm_channel_idx = bpy.props.IntProperty()
    bpy.types.Scene.lm_shader_idx = bpy.props.IntProperty()
    
    bpy.types.Scene.lm_texture_channel_name = bpy.props.StringProperty(name="Add Texture Channel", update=update_texture_channel_name)
    bpy.types.Scene.lm_channel_name = bpy.props.StringProperty(name="Add Channel", update=update_channel_name)
    bpy.types.Scene.lm_shader_name = bpy.props.StringProperty(name="Add Shader", update=update_shader_name)

    bpy.types.Scene.lm_linear_channel = bpy.props.BoolProperty(name="Linear Channel")
    bpy.types.Scene.lm_normalMap_channel = bpy.props.BoolProperty(name="NormalMap Channel")
    bpy.types.Scene.lm_inverted_channel = bpy.props.BoolProperty(name="Inverted Channel")

    bpy.types.Scene.lm_override_material_color = bpy.props.BoolProperty(name="Override Material Color", default=True)
    bpy.types.Scene.lm_default_material_color = bpy.props.FloatVectorProperty(name='Default Material Color', subtype='COLOR', default=(0.5,0.5,0.5), min=0, max=1)
    bpy.types.Scene.lm_override_material_roughness = bpy.props.BoolProperty(name="Override Material Roughness", default=True)
    bpy.types.Scene.lm_default_material_roughness = bpy.props.FloatProperty(name='Default Material Roughness', default=0.6, min=0, max=1)

    bpy.types.Scene.lm_background_color = bpy.props.FloatVectorProperty(name='Background Color', subtype='COLOR', default=(0.05,0.05,0.05), min=0, max=1)
    bpy.types.Scene.lm_font_color = bpy.props.FloatVectorProperty(name='Font Color', subtype='COLOR', default=(0.85,0.85,0.85), min=0, max=1)

    for cls in classes:
        bpy.utils.register_class(cls)
    
    bpy.types.Scene.lm_asset_list = bpy.props.CollectionProperty(type=LM_Asset_List)

    bpy.types.Scene.lm_initial_view_layer = bpy.props.StringProperty(name="Initial ViewLayer")

    bpy.types.Scene.lm_texture_channels =  bpy.props.CollectionProperty(type=LM_TextureChannels)
    bpy.types.Scene.lm_channels =  bpy.props.CollectionProperty(type=LM_Channels)
    bpy.types.Scene.lm_shaders =  bpy.props.CollectionProperty(type=LM_Shaders)

    bpy.types.Scene.lm_keywords =  bpy.props.CollectionProperty(type=LM_Keywords)
    bpy.types.Scene.lm_keyword_values =  bpy.props.CollectionProperty(type=LM_KeywordValues)
    
    
    


def unregister():
    del bpy.types.Scene.lm_keyword_values
    del bpy.types.Scene.lm_keywords
    del bpy.types.Scene.lm_shaders
    del bpy.types.Scene.lm_channels
    del bpy.types.Scene.lm_texture_channels
    del bpy.types.Scene.lm_initial_view_layer
    del bpy.types.Scene.lm_asset_list

    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)

    del bpy.types.Scene.lm_override_material_roughness
    del bpy.types.Scene.lm_override_material_color
    del bpy.types.Scene.lm_avoid_update
    del bpy.types.Scene.lm_separator
    del bpy.types.Scene.lm_optionnal_asset_keyword
    del bpy.types.Scene.lm_optionnal_mesh_keyword
    del bpy.types.Scene.lm_optionnal_texture_keyword
    del bpy.types.Scene.lm_keyword_name
    del bpy.types.Scene.lm_font_color
    del bpy.types.Scene.lm_background_color
    del bpy.types.Scene.lm_default_material_roughness
    del bpy.types.Scene.lm_default_material_color
    del bpy.types.Scene.lm_force_render
    del bpy.types.Scene.lm_keyword_value
    del bpy.types.Scene.lm_shader_name
    del bpy.types.Scene.lm_shader_idx
    del bpy.types.Scene.lm_channel_name
    del bpy.types.Scene.lm_channel_idx
    del bpy.types.Scene.lm_normalMap_channel
    del bpy.types.Scene.lm_linear_channel
    del bpy.types.Scene.lm_inverted_channel
    del bpy.types.Scene.lm_texture_channel_name
    del bpy.types.Scene.lm_texture_channel_idx
    del bpy.types.Scene.lm_texture_naming_convention
    del bpy.types.Scene.lm_mesh_naming_convention
    del bpy.types.Scene.lm_asset_naming_convention
    del bpy.types.Scene.lm_asset_collection
    del bpy.types.Scene.lm_render_collection
    del bpy.types.Scene.lm_asset_path
    del bpy.types.Scene.lm_render_path
      

if __name__ == "__main__":
    register()