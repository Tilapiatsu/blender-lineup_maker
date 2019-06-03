import bpy
from os import path

class LM_PT_main(bpy.types.Panel):          
    bl_label = "Make Lineup"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_category = 'Lineup Maker'

    
    def draw(self, context):
        scn = context.scene
        asset_path = bpy.path.abspath(scn.lm_asset_path)
        render_path = bpy.path.abspath(scn.lm_render_path)
        layout = self.layout

        
        if path.isdir(asset_path):
            icon = "DOWNARROW_HLT"
        else:
            icon = "BLANK1"
        layout.prop(scn, 'lm_asset_path', text='Asset Path', icon=icon)
        
        row = layout.row(align=True)
        if path.isdir(render_path):
            icon = "DOWNARROW_HLT"
        else:
            icon = "BLANK1"
        
        row.prop(scn, 'lm_render_path', text='Render Path', icon=icon)
        
        if path.isdir(render_path):
            row.scale_x = 0.3
            row.operator("scene.lm_openfolder", icon='WINDOW', text='Open Folder').folder_path = render_path
            
        layout.prop(scn, 'lm_render_collection', text='Render Collection', icon='LIGHT')
        layout.separator()
        b = layout.box()
        b.operator("scene.lm_update_lineup", icon='SHADERFX', text="Create / Update Lineup")
        b.separator()
        if len(scn.lm_asset_list) == 0:
            text = 'Import all assets'
            imported = False
        else:
            text = 'Update modified assets'
            imported = True
        b.operator("scene.lm_importassets", icon='IMPORT', text=text)

        if imported:
            row = b.row()
            
            row.prop(scn, 'lm_force_render', text='Force')
            row.scale_x = 3
            row.operator("scene.lm_renderassets", icon='OUTPUT', text='Render all assets')
            
            # b.operator("scene.lm_compositerenders", icon='NODE_COMPOSITING', text='Composite rendered assets')
            row = b.row()
            row.prop(scn, 'lm_open_pdf_when_exported', text='Open When Exported')
            row.operator("scene.lm_export_pdf", icon='WORDWRAP_ON', text='Export PDF')


class LM_PT_CompositLayout(bpy.types.Panel):          
    bl_label = "Composite Layout"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_category = 'Lineup Maker'
    bl_options = {"DEFAULT_CLOSED"}

    
    def draw(self, context):
        scn = context.scene
        asset_path = bpy.path.abspath(scn.lm_asset_path)
        render_path = bpy.path.abspath(scn.lm_render_path)
        layout = self.layout

        col = layout.column(align=True)

        col.prop(scn, 'lm_content_background_color', text='Content Backgroud Color')
        col.prop(scn, 'lm_text_background_color', text='Text Backgroud Color')
        col.prop(scn, 'lm_font_color', text='Font Color')


class LM_PT_NamingConvention(bpy.types.Panel):
    bl_label = "Naming Convention"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_category = "Lineup Maker"
    bl_options = {"DEFAULT_CLOSED"}

    def draw(self, context):
        scn = context.scene
        layout = self.layout

        # NAMING CONVENTION SETUP
        col = layout.column(align=True)

        col.prop(scn, 'lm_separator', text = 'Separator')

        b = col.box()
        b.label(text='Asset Naming Convention')
        br = b.box()
        bbr = br.split(align=True)
        
        op = bbr.operator("scene.lm_add_asset_keyword", text='Add', icon='ADD')
        op.optionnal = False
        op.excluded = False
        op = bbr.operator("scene.lm_add_asset_keyword", text='Optionnal', icon='ADD')
        op.optionnal = True
        op.excluded = False
        op = bbr.operator("scene.lm_add_asset_keyword", text='Excluded', icon='ADD')
        op.optionnal = False
        op.excluded = True
        bbr.operator("scene.lm_remove_asset_keyword", text='Remove', icon='REMOVE')
        
        b.prop(scn, 'lm_asset_naming_convention', text='')
        col.separator()

        b = col.box()
        b.label(text='Mesh Naming Convention')
        br = b.box()
        bbr = br.split(align=True)
        op = bbr.operator("scene.lm_add_mesh_keyword", text='Add', icon='ADD')
        op.optionnal = False
        op.excluded = False
        op = bbr.operator("scene.lm_add_mesh_keyword", text='Optionnal', icon='ADD')
        op.optionnal = True
        op.excluded = False
        op = bbr.operator("scene.lm_add_mesh_keyword", text='Excluded', icon='ADD')
        op.optionnal = False
        op.excluded = True
        bbr.operator("scene.lm_remove_mesh_keyword", text='Remove', icon='REMOVE')

        b.prop(scn, 'lm_mesh_naming_convention', text='')
        col.separator()

        b = col.box()
        b.label(text='Texture Naming Convention')
        br = b.box()
        bbr = br.split(align=True)
        op = bbr.operator("scene.lm_add_texture_keyword", text='Add', icon='ADD')
        op.optionnal = False
        op.excluded = False
        op = bbr.operator("scene.lm_add_texture_keyword", text='Optionnal', icon='ADD')
        op.optionnal = True
        op.excluded = False
        op = bbr.operator("scene.lm_add_texture_keyword", text='Excluded', icon='ADD')
        op.optionnal = False
        op.excluded = True
        bbr.operator("scene.lm_remove_texture_keyword", text='Remove', icon='REMOVE')

        b.prop(scn, 'lm_texture_naming_convention', text='')
        col.separator()

        # Keywords Setup

        col = layout.column(align=True)
        b = col.box()
        b.label(text='Keywords')
        
        row = b.row()
        
        rows = len(scn.lm_keywords) if len(scn.lm_keywords) > 2 else 2
        row.template_list('LM_UL_keywords', '', scn, 'lm_keywords', scn, 'lm_keyword_idx', rows=rows)
        c = row.column(align=True)
        c.operator("scene.lm_move_keyword", text="", icon='TRIA_UP').direction = "UP"
        c.operator("scene.lm_move_keyword", text="", icon='TRIA_DOWN').direction = "DOWN"

        c.separator()
        c.operator("scene.lm_clear_keywords", text="", icon='LOOP_BACK')
        c.operator("scene.lm_remove_keyword", text="", icon='X')
        c.separator()
        c.operator("scene.lm_rename_keyword", text="", icon='OUTLINER_DATA_FONT')

        b.prop(scn, 'lm_keyword_name')

        c.separator()

        col = layout.column(align=True)
        b = col.box()
        b.label(text='Keyword Value')
        row = b.row()
        
        rows = len(scn.lm_keyword_values) if len(scn.lm_keyword_values) > 4 else 4
        row.template_list('LM_UL_keyword_values', '', scn, 'lm_keyword_values', scn, 'lm_keyword_value_idx', rows=rows)
        c = row.column(align=True)
        c.operator("scene.lm_move_keyword_value", text="", icon='TRIA_UP').direction = "UP"
        c.operator("scene.lm_move_keyword_value", text="", icon='TRIA_DOWN').direction = "DOWN"

        c.separator()
        c.operator("scene.lm_clear_keyword_values", text="", icon='LOOP_BACK')
        c.operator("scene.lm_remove_keyword_value", text="", icon='X')
        c.separator()
        c.operator("scene.lm_rename_keyword_value", text="", icon='OUTLINER_DATA_FONT')

        b.prop(scn, 'lm_keyword_value')

        c.separator()


class LM_PT_TextureSetSettings(bpy.types.Panel):
    bl_label = "TextureSet Settings"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_category = "Lineup Maker"
    bl_options = {"DEFAULT_CLOSED"}

    def draw(self, context):
        scn = context.scene
        layout = self.layout

        col = layout.column(align=True)
        col.label(text='Shader Name')
        row = col.row()
        
        rows = len(scn.lm_shaders) if len(scn.lm_shaders) > 2 else 2
        row.template_list('LM_UL_shaders', '', scn, 'lm_shaders', scn, 'lm_shader_idx', rows=rows)
        c = row.column(align=True)
        c.operator("scene.lm_move_shader", text="", icon='TRIA_UP').direction = "UP"
        c.operator("scene.lm_move_shader", text="", icon='TRIA_DOWN').direction = "DOWN"

        c.separator()
        c.operator("scene.lm_clear_shaders", text="", icon='LOOP_BACK')
        c.operator("scene.lm_remove_shader", text="", icon='X')
        c.separator()
        c.operator("scene.lm_rename_shader", text="", icon='OUTLINER_DATA_FONT')

        col.prop(scn, 'lm_shader_name')

        col = layout.column(align=True)
        col.separator()
        col.separator()
        col.label(text='Channel Name')
        row = col.row()
        
        rows = len(scn.lm_channels) if len(scn.lm_channels) > 4 else 4
        row.template_list('LM_UL_channels', '', scn, 'lm_channels', scn, 'lm_channel_idx', rows=rows)
        c = row.column(align=True)
        c.operator("scene.lm_move_channel", text="", icon='TRIA_UP').direction = "UP"
        c.operator("scene.lm_move_channel", text="", icon='TRIA_DOWN').direction = "DOWN"

        c.separator()
        c.operator("scene.lm_clear_channels", text="", icon='LOOP_BACK')
        c.operator("scene.lm_remove_channel", text="", icon='X')
        c.separator()
        c.operator("scene.lm_rename_channel", text="", icon='OUTLINER_DATA_FONT')

        row = col.row()
        row.prop(scn, 'lm_channel_name')
        row.scale_x = 0.4
        row.prop(scn, 'lm_linear_channel')
        row.prop(scn, 'lm_normalMap_channel')
        row.prop(scn, 'lm_inverted_channel')

        col.separator()
        col.separator()
        col.label(text='Texture Name')
        row = col.row()
        
        rows = len(scn.lm_texture_channels) if len(scn.lm_texture_channels) > 4 else 4
        row.template_list('LM_UL_texturesets', '', scn, 'lm_texture_channels', scn, 'lm_texture_channel_idx', rows=rows)
        c = row.column(align=True)
        c.operator("scene.lm_move_texture_channel", text="", icon='TRIA_UP').direction = "UP"
        c.operator("scene.lm_move_texture_channel", text="", icon='TRIA_DOWN').direction = "DOWN"

        c.separator()
        c.operator("scene.lm_clear_texture_channels", text="", icon='LOOP_BACK')
        c.operator("scene.lm_remove_texture_channel", text="", icon='X')
        c.separator()
        c.operator("scene.lm_rename_texture_channel", text="", icon='OUTLINER_DATA_FONT')

        col.prop(scn, 'lm_texture_channel_name')

        col.separator()
        col.separator()
        b = col.box()
        b.label(text='Material Override')

        r = b.row(align=True)
        r.prop(scn, 'lm_override_material_color', text='Override Material Color')
        r.scale_x = 3
        r.prop(scn, 'lm_default_material_color', text='')

        r = b.row(align=True)
        r.prop(scn, 'lm_override_material_roughness', text='Override Material Roughness')
        r.scale_x = 3
        r.prop(scn, 'lm_default_material_roughness',text='')


class LM_PT_Cameras(bpy.types.Panel):          
    bl_label = "Camera Assignment"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_category = 'Lineup Maker'

    
    def draw(self, context):
        scn = context.scene
        layout = self.layout

        col = layout.column(align=True)
        b = col.box()
        b.label(text='Keywords')
        
        row = b.row()
        
        rows = len(scn.lm_keywords) if len(scn.lm_keywords) > 2 else 2
        row.template_list('LM_UL_keywords', '', scn, 'lm_keywords', scn, 'lm_keyword_idx', rows=rows)

        b = col.box()
        b.prop(scn, 'lm_default_camera', text='Default Camera')
        b.label(text='Cameras')
        row = b.row()
        rows = len(scn.lm_cameras) if len(scn.lm_cameras) > 2 else 2
        
        row.template_list('LM_UL_cameras', '', scn, 'lm_cameras', scn, 'lm_camera_idx', rows=rows)
        c = row.column(align=True)
        c.operator("scene.lm_move_camera_keyword", text="", icon='TRIA_UP').direction = "UP"
        c.operator("scene.lm_move_camera_keyword", text="", icon='TRIA_DOWN').direction = "DOWN"

        c.separator()
        c.operator("scene.lm_clear_camera_keywords", text="", icon='LOOP_BACK')
        c.operator("scene.lm_remove_camera_keyword", text="", icon='X')
        c.separator()
        c.operator("scene.lm_rename_camera_keyword", text="", icon='OUTLINER_DATA_FONT')
        b.prop(scn, 'lm_camera_keyword_name', text='Camera Keyword')


class LM_PT_Chapter(bpy.types.Panel):          
    bl_label = "Chapter Definition"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_category = 'Lineup Maker'

    
    def draw(self, context):
        scn = context.scene
        layout = self.layout

        col = layout.column(align=True)
        b = col.box()
        b.label(text='Keywords')
        
        row = b.row()
        
        rows = len(scn.lm_keywords) if len(scn.lm_keywords) > 2 else 2
        row.template_list('LM_UL_keywords', '', scn, 'lm_keywords', scn, 'lm_keyword_idx', rows=rows)

        b.operator('scene.lm_add_chapter_keyword', text='Add selected keyword in chapter')
        row = b.row()
        row.prop(scn, 'lm_chapter_naming_convention', text='Chapter Keywords')
        row.operator('scene.lm_remove_chapter_keyword', icon='X', text="")