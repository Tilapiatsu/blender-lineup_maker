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
#   - Need to better sort Chapters by name
#   - Create an operator to update/import render and export PDF in a row
#   
# 
#   - Log and repport
#       - Pop up message at the end to notify what is happening
#   - Need to update JSon Exporter to support
#       - section
#       - fromFile
#   - Use Section to create chapters

#   - The addon don't render the proper asset if updated if there is already renders existing in the folder ( check date )


#  DEPENDENCIES :
#      pyfpdf : pip install fpdf
#      https://www.blog.pythonlibrary.org/2018/06/05/creating-pdfs-with-pyfpdf-and-python/

import bpy

try:
    from .OP_main import *
except (ModuleNotFoundError, ImportError) as e:
    from . import setup
    setup.install_dependencies()
    from .OP_main import *

from .OP_files import *
from .UI_properties_pannel import *
from .preferences import *
from .properties import *
from .OP_ui_list_import import *
from .OP_ui_list_asset import *
from .OP_ui_list_render_queue import *
from .OP_ui_list_texture import *
from .OP_ui_list_channel import *
from .OP_ui_list_shader import *
from .OP_ui_list_keyword import *
from .OP_ui_list_camera_keyword import *
from .OP_ui_list_chapter import *
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
    LM_PT_ExportAsset,
    LM_OP_UpdateLineup,
    LM_OP_ImportAssets,
    LM_OP_RenderAssets,
    LM_OP_OpenFolder,
    LM_OP_CompositeRenders,
    LM_OP_ExportPDF,
    LM_OP_RefreshAssetStatus,
    LM_OP_ExportAsset,
    LM_OP_UpdateJson,
    LM_PT_NamingConvention,
    LM_PT_TextureSetSettings,
    LM_PT_Cameras,
    LM_PT_Chapter,
    LM_PT_CompositLayout,
    LM_PT_main,
    LM_PT_AssetList,
    LM_Render_List,
    LM_Texture_List,
    LM_Material_List,
    LM_MeshObject_List,
    LM_MeshFile_List,
    LM_AssetWarnings_List,
    LM_Asset_List,
    LM_TextureChannels,
    LM_Channels,
    LM_Shaders,
    LM_Keywords,
    LM_KeywordValues,
    LM_CamerasKeywords,
    LM_Cameras,
    LM_UL_TextureSet_UIList,
    LM_UL_Channel_UIList,
    LM_UL_Shader_UIList,
    LM_UL_Keywords_UIList,
    LM_UL_KeywordValues_UIList,
    LM_UL_Cameras_UIList,
    LM_UL_ImportList_UIList,
    LM_UL_AssetList_UIList,
    LM_UL_AssetListRQ_UIList,
    LM_IU_RefreshImportList,
    LM_UI_RemoveAsseFolder,
    LM_UI_RemoveAsseFromImportList,
    LM_UI_ClearAssetFolder,
    LM_UI_OpenImportFolder,
    LM_UI_RenameAssetFolder,
    LM_UI_CheckAllImportList,
    LM_UI_UncheckAllImportList,
    LM_UI_ImportAssetList,
    LM_UI_ShowImportAssetWarning,
    LM_UI_PrintNamingConvention,
    LM_UI_AddAssetToRenderQueue,
    LM_UI_AddNeedRenderToRenderQueue,
    LM_UI_MoveAssetToRender,
    LM_UI_ClearAssetToRenderQueueList,
    LM_UI_RemoveAssetToRender,
    LM_UI_CheckAllRenderQueuedAsset,
    LM_UI_UncheckAllRenderQueuedAsset,
    LM_UI_ExportRenderQueueList,
    LM_UI_MoveAsset,
    LM_UI_ClearAssetList,
    LM_UI_RemoveAsset,
    LM_UI_OpenRenderFolder,
    LM_UI_OpenAssetFolder,
    LM_UI_RenameAsset,
    LM_UI_ShowAssetWarning,
    LM_UI_FixViewLayers,
    LM_UI_ShowAsset,
    LM_UI_PrintAssetData,
    LM_UI_AddChapterKeyword,
    LM_UI_RemoveChapterKeyword,
    LM_UI_MoveCameraKeyword,
    LM_UI_ClearCameraKeyword,
    LM_UI_RemoveCameraKeyword,
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

def update_camera_keyword_name(self, context):
    scn = context.scene
    if scn.lm_avoid_update:
        scn.lm_avoid_update = False
        return

    else:
        if bpy.context.active_object.type != 'CAMERA':
            print('Lineup Maker : You need to select a Camera First')
            scn.lm_avoid_update = True
            scn.lm_camera_keyword_name = 'You need to select a Camera First'
            return
        elif scn.lm_camera_keyword_name:
            try:
                keywords = [k.keyword for k in scn.lm_cameras[scn.lm_camera_idx].keywords]
                keyword_values = [k.keyword_value for k in scn.lm_cameras[scn.lm_camera_idx].keywords]
            except IndexError:
                keywords = []
                keyword_values = []

            if not len(keywords) or scn.lm_cameras[scn.lm_camera_idx].camera != bpy.context.active_object:
                c = scn.lm_cameras.add()
                c.camera = bpy.context.active_object
                kw = c.keywords.add()
                kw.keyword = scn.lm_keywords[scn.lm_keyword_idx].name
                kw.keyword_value = scn.lm_camera_keyword_name
            else:
                doubles = False
                for keyword, keyword_value in zip(keywords, keyword_values):
                    if keyword == scn.lm_keywords[scn.lm_keyword_idx].name and keyword_value == scn.lm_camera_keyword_name:
                        doubles = True
                        break
                
                if not doubles:
                    kw = scn.lm_cameras[scn.lm_camera_idx].keywords.add()
                    kw.keyword = scn.lm_keywords[scn.lm_keyword_idx].name
                    kw.keyword_value = scn.lm_camera_keyword_name

            scn.lm_camera_idx = len(scn.lm_cameras) - 1

        scn.lm_avoid_update = True
        scn.lm_camera_keyword_name = ""

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
    bpy.types.Scene.lm_default_camera = bpy.props.PointerProperty(type=bpy.types.Camera)
    bpy.types.Scene.lm_force_render = bpy.props.BoolProperty(name='Force Rendering of all assets')
    bpy.types.Scene.lm_force_composite = bpy.props.BoolProperty(name='Force Composite of all assets')
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
    bpy.types.Scene.lm_camera_idx = bpy.props.IntProperty()

    bpy.types.Scene.lm_import_list_idx = bpy.props.IntProperty()
    bpy.types.Scene.lm_asset_list_idx = bpy.props.IntProperty()
    bpy.types.Scene.lm_render_queue_idx = bpy.props.IntProperty()
    
    bpy.types.Scene.lm_texture_channel_name = bpy.props.StringProperty(name="Add Texture Channel", update=update_texture_channel_name)
    bpy.types.Scene.lm_channel_name = bpy.props.StringProperty(name="Add Channel", update=update_channel_name)
    bpy.types.Scene.lm_shader_name = bpy.props.StringProperty(name="Add Shader", update=update_shader_name)
    bpy.types.Scene.lm_camera_keyword_name = bpy.props.StringProperty(name="Add Keyword for selected Chamera", update=update_camera_keyword_name)
    bpy.types.Scene.lm_chapter_naming_convention = bpy.props.StringProperty(name="Chapter")

    bpy.types.Scene.lm_linear_channel = bpy.props.BoolProperty(name="Linear Channel")
    bpy.types.Scene.lm_normalMap_channel = bpy.props.BoolProperty(name="NormalMap Channel")
    bpy.types.Scene.lm_inverted_channel = bpy.props.BoolProperty(name="Inverted Channel")

    bpy.types.Scene.lm_override_material_color = bpy.props.BoolProperty(name="Override Material Color", default=True)
    bpy.types.Scene.lm_default_material_color = bpy.props.FloatVectorProperty(name='Default Material Color', subtype='COLOR', default=(0.5,0.5,0.5), min=0, max=1)
    bpy.types.Scene.lm_override_material_roughness = bpy.props.BoolProperty(name="Override Material Roughness", default=True)
    bpy.types.Scene.lm_default_material_roughness = bpy.props.FloatProperty(name='Default Material Roughness', default=0.6, min=0, max=1)
    bpy.types.Scene.lm_override_material_specular = bpy.props.BoolProperty(name="Override Material Roughness", default=True)
    bpy.types.Scene.lm_default_material_specular = bpy.props.FloatProperty(name='Default Material Roughness', default=0.5, min=0, max=1)

    bpy.types.Scene.lm_content_background_color = bpy.props.FloatVectorProperty(name='Content Background Color', subtype='COLOR', default=(0.05,0.05,0.05), min=0, max=1)
    bpy.types.Scene.lm_text_background_color = bpy.props.FloatVectorProperty(name='Text Background Color', subtype='COLOR', default=(0, 0, 0), min=0, max=1)
    bpy.types.Scene.lm_font_color = bpy.props.FloatVectorProperty(name='Font Color', subtype='COLOR', default=(0.85,0.85,0.85), min=0, max=1)

    bpy.types.Scene.lm_override_frames = bpy.props.BoolProperty(name='Override rendered frames', default=True)
    bpy.types.Scene.lm_precomposite_frames = bpy.props.BoolProperty(name='Precomposite frames', default=True)
    bpy.types.Scene.lm_open_pdf_when_exported = bpy.props.BoolProperty(name="Open PDF File When Exported", default=True)

    bpy.types.Scene.lm_exported_asset_name = bpy.props.StringProperty(name="Export Name")

    bpy.types.Scene.lm_import_message = bpy.props.StringProperty(name="Import Message")
    bpy.types.Scene.lm_import_progress = bpy.props.StringProperty(name="Import Progress")
    bpy.types.Scene.lm_viewlayer_progress = bpy.props.StringProperty(name="View Layer Progress")

    bpy.types.Scene.lm_pdf_message = bpy.props.StringProperty(name="Import Message")
    bpy.types.Scene.lm_pdf_progress = bpy.props.StringProperty(name="Import Progress")
    bpy.types.Scene.lm_pdf_export_last_rendered = bpy.props.BoolProperty(name='Export last rendered assets', default=True)

    bpy.types.Scene.lm_queue_message = bpy.props.StringProperty(name="Queue Message")
    bpy.types.Scene.lm_queue_progress = bpy.props.StringProperty(name="Queue Progress")

    bpy.types.Scene.lm_render_message = bpy.props.StringProperty(name="Render Message")
    bpy.types.Scene.lm_render_progress = bpy.props.StringProperty(name="Render Progress")

    for cls in classes:
        bpy.utils.register_class(cls)
    
    bpy.types.Scene.lm_import_list = bpy.props.CollectionProperty(type=LM_Asset_List)
    bpy.types.Scene.lm_asset_list = bpy.props.CollectionProperty(type=LM_Asset_List)
    bpy.types.Scene.lm_render_queue = bpy.props.CollectionProperty(type=LM_Asset_List)
    bpy.types.Scene.lm_last_render_list = bpy.props.CollectionProperty(type=LM_Asset_List)

    bpy.types.Scene.lm_initial_view_layer = bpy.props.StringProperty(name="Initial ViewLayer")

    bpy.types.Scene.lm_texture_channels =  bpy.props.CollectionProperty(type=LM_TextureChannels)
    bpy.types.Scene.lm_channels =  bpy.props.CollectionProperty(type=LM_Channels)
    bpy.types.Scene.lm_shaders =  bpy.props.CollectionProperty(type=LM_Shaders)

    bpy.types.Scene.lm_keywords =  bpy.props.CollectionProperty(type=LM_Keywords)
    bpy.types.Scene.lm_keyword_values =  bpy.props.CollectionProperty(type=LM_KeywordValues)

    bpy.types.Scene.lm_cameras = bpy.props.CollectionProperty(type=LM_Cameras)

    bpy.types.Scene.lm_exported_hd_status = bpy.props.EnumProperty(name="HD Status",
                                                                    description="Choose in which status is the HD Mesh of the Asset",
                                                                    items=V.STATUS,
                                                                    default='NOT_STARTED')
    bpy.types.Scene.lm_exported_ld_status = bpy.props.EnumProperty(name="LD Status",
                                                                    description="Choose in which status is the LD Mesh of the Asset",
                                                                    items=V.STATUS,
                                                                    default='NOT_STARTED')
    bpy.types.Scene.lm_exported_baking_status = bpy.props.EnumProperty(name="Baking Status",
                                                                    description="Choose in which status is the Baking Mesh of the Asset",
                                                                    items=V.STATUS,
                                                                    default='NOT_STARTED')

    
    


def unregister():
    del bpy.types.Scene.lm_exported_hd_status
    del bpy.types.Scene.lm_exported_ld_status
    del bpy.types.Scene.lm_exported_baking_status
    del bpy.types.Scene.lm_cameras
    del bpy.types.Scene.lm_keyword_values
    del bpy.types.Scene.lm_keywords
    del bpy.types.Scene.lm_shaders
    del bpy.types.Scene.lm_channels
    del bpy.types.Scene.lm_texture_channels
    del bpy.types.Scene.lm_initial_view_layer
    del bpy.types.Scene.lm_asset_list
    del bpy.types.Scene.lm_import_list
    del bpy.types.Scene.lm_render_queue
    del bpy.types.Scene.lm_last_render_list

    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)


    del bpy.types.Scene.lm_render_message 
    del bpy.types.Scene.lm_render_progress
    del bpy.types.Scene.lm_queue_message
    del bpy.types.Scene.lm_queue_progress
    del bpy.types.Scene.lm_pdf_export_last_rendered
    del bpy.types.Scene.lm_pdf_message 
    del bpy.types.Scene.lm_pdf_progress
    del bpy.types.Scene.lm_viewlayer_progress
    del bpy.types.Scene.lm_import_progress
    del bpy.types.Scene.lm_import_message
    del bpy.types.Scene.lm_exported_asset_name
    del bpy.types.Scene.lm_open_pdf_when_exported
    del bpy.types.Scene.lm_precomposite_frames
    del bpy.types.Scene.lm_override_frames
    del bpy.types.Scene.lm_override_material_specular
    del bpy.types.Scene.lm_default_material_specular 
    del bpy.types.Scene.lm_override_material_roughness
    del bpy.types.Scene.lm_override_material_color
    del bpy.types.Scene.lm_avoid_update
    del bpy.types.Scene.lm_separator
    del bpy.types.Scene.lm_optionnal_asset_keyword
    del bpy.types.Scene.lm_optionnal_mesh_keyword
    del bpy.types.Scene.lm_optionnal_texture_keyword
    del bpy.types.Scene.lm_keyword_name
    del bpy.types.Scene.lm_font_color
    del bpy.types.Scene.lm_text_background_color
    del bpy.types.Scene.lm_content_background_color
    del bpy.types.Scene.lm_default_material_roughness
    del bpy.types.Scene.lm_default_material_color
    del bpy.types.Scene.lm_force_render
    del bpy.types.Scene.lm_keyword_value
    del bpy.types.Scene.lm_shader_name
    del bpy.types.Scene.lm_shader_idx
    del bpy.types.Scene.lm_asset_list_idx
    del bpy.types.Scene.lm_render_queue_idx
    del bpy.types.Scene.lm_import_list_idx
    del bpy.types.Scene.lm_camera_idx
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
    del bpy.types.Scene.lm_default_camera
    del bpy.types.Scene.lm_camera_keyword_name
    del bpy.types.Scene.lm_chapter_naming_convention
    del bpy.types.Scene.lm_asset_collection
    del bpy.types.Scene.lm_render_collection
    del bpy.types.Scene.lm_asset_path
    del bpy.types.Scene.lm_render_path
      

if __name__ == "__main__":
    register()