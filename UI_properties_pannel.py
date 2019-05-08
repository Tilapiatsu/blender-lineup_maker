import bpy
from os import path

class LM_PT_main(bpy.types.Panel):          
    bl_label = "Lineup Maker"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_category = 'Lineup Maker'

    # def update_textureChannelName(self, context):
    #     if self.avoid_update:
    #         self.avoid_update = False
    #         return

    #     else:
    #         if self.textureChannelName and self.textureChannelName not in context.scene.lm_texture_channels:
    #             tc = context.scene.lm_texture_channels.add()
    #             tc.name = self.textureChannelName

    #             self.textureChannelIDX = len(context.scene.lm_texture_channels) - 1

    #         self.avoid_update = True
    #         self.textureChannelName = ""
    
    # PROPERTIES

    # textureChannelName: bpy.props.StringProperty(name="Add Texture Channel", update=update_textureChannelName)
    # textureChannelsIDX: bpy.props.IntProperty()

    # HIDDEN
    # avoid_update: bpy.props.BoolProperty(default=False)
    
    def draw(self, context):
        scn = context.scene
        assetPath = bpy.path.abspath(scn.lm_asset_path)
        layout = self.layout

        # TEXTURESET SETUP
        col = layout.column(align=True)
        rows = len(scn.lm_texture_channels) if len(scn.lm_texture_channels) > 4 else 4
        col.template_list('LM_UL_append_textureset', '', scn, 'lm_texture_channels', scn, 'lm_texture_channels_idx', rows=rows)
        col.prop(scn, 'lm_texture_channel_name')

        # NAMING CONVENTION SETUP
        col = layout.column(align=True)
        row = col.row(align=True)
        if path.exists(assetPath):
            icon = "DOWNARROW_HLT"
        else:
            icon = "BLANK1"
        row.prop(scn, 'lm_asset_path', text = 'Asset Path', icon=icon)
        
        col.prop(scn, 'lm_asset_naming_convention', text = 'Asset Naming Convention')
        col.prop(scn, 'lm_mesh_naming_convention', text = 'Mesh Naming Convention')
        col.prop(scn, 'lm_texture_naming_convention', text = 'Texture Naming Convention')
        col.operator("scene.lm_importfiles", icon='IMPORT', text="Import all assets")


