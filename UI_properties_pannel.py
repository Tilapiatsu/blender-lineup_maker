import bpy, textwrap
from os import path

not_a_lineup = 'The current scene should be set as a Lineup to acces to this part'
not_a_catalog = 'The current scene should be set as a Catalog to acces to this part'

def _label_multiline(context, text, parent):
    chars = int(context.region.width / 7)   # 7 pix on 1 character
    wrapper = textwrap.TextWrapper(width=chars)
    text_lines = wrapper.wrap(text=text)
    for text_line in text_lines:
        parent.label(text=text_line)

class LM_PT_LineupSetup:          
	bl_space_type = "VIEW_3D"
	bl_region_type = "UI"
	bl_category = 'Lineup Maker'
	bl_options = {"DEFAULT_CLOSED"}

class LM_PT_LineupSetupPanel(LM_PT_LineupSetup, bpy.types.Panel): 
	bl_label = "Lineup Setup"
	bl_idname = 'lineup_setup'         

	def draw(self, context):
		layout = self.layout
		layout.label(text='This is where you can configure the lineup. You should start here bofore using it')


class LM_PT_SceneStatus(LM_PT_LineupSetup, bpy.types.Panel):          
	bl_label = "1- Scene status"
	bl_parent_id = 'lineup_setup'


	def draw(self, context):
		layout = self.layout
		b = layout.box()
		text = 'Unset as Lineup Scene' if context.window_manager.lm_is_lineup_scene else 'Set as Lineup Scene'
		b.prop(context.window_manager, "lm_is_lineup_scene", text=text, toggle=True)

		text = 'Unset as Catalog Scene' if context.window_manager.lm_is_catalog_scene else 'Set as Catalog Scene'
		b.prop(context.window_manager, "lm_is_catalog_scene", text=text, toggle=True)


class LM_PT_SceneSetup(LM_PT_LineupSetup, bpy.types.Panel): 
	bl_label = "2- Scene Setup"         
	bl_parent_id = 'lineup_setup'

	
	def draw(self, context):
		scn = context.scene
		wm = context.window_manager
		asset_path = bpy.path.abspath(scn.lm_asset_path)
		render_path = bpy.path.abspath(scn.lm_render_path)
		layout = self.layout
		
		b = layout.box()
		b.prop(wm, "lm_show_help", text='', icon='QUESTION')
		if wm.lm_show_help:
			text='Here are the main pathes, objects and collection you need to fill for the lineup to work correctly'
			_label_multiline(context=context, text=text, parent=b)

		b = layout.box()
		if path.isdir(asset_path):
			icon = "DOWNARROW_HLT"
		else:
			icon = "BLANK1"
		b.prop(scn, 'lm_asset_path', text='Asset Path', icon=icon)
		b.prop(scn, 'lm_blend_catalog_path', text='BlenderCatalog Path', icon="FILE_BLEND")
		
		row = b.row(align=True)
		if path.isdir(render_path):
			icon = "DOWNARROW_HLT"
		else:
			icon = "BLANK1"
		
		row.prop(scn, 'lm_render_path', text='Render Path', icon=icon)
		
		if path.isdir(render_path):
			row.operator("scene.lm_openfolder", icon='WINDOW', text='Open Folder').folder_path = render_path
		
		b.prop(scn, 'lm_default_camera', text='Default Camera', icon='CAMERA_DATA')
		b.prop(scn, 'lm_camera_collection', text='Camera Collection', icon='CAMERA_DATA')
		b.prop(scn, 'lm_lighting_collection', text='Lighting Collection', icon='LIGHT')
		
		
		# b = layout.box()
		
		# if len(scn.lm_asset_list) == 0:
		# 	text = 'Import all assets'
		# 	imported = False
		# else:
		# 	text = 'Update modified assets'
		# 	imported = True
		# b.operator("scene.lm_create_blend_catalog_file", icon='IMPORT', text=text).mode = "ALL"
		# if len(context.scene.lm_import_message):
		# 	b.label(text=context.scene.lm_import_message)
		# if len(context.scene.lm_import_progress):
		# 	b.label(text=context.scene.lm_import_progress)
		# if len(context.scene.lm_viewlayer_progress):
		# 	b.label(text=context.scene.lm_viewlayer_progress)
		

		# if imported:
		# 	b = layout.box()
		# 	b.prop(scn, 'lm_precomposite_frames')
		# 	b.prop(scn, 'lm_override_frames')
			
		# 	b.prop(scn, 'lm_force_render', text='Force Render')
		# 	b.prop(scn, 'lm_pdf_export_last_rendered', text='Export Last rendered asset to pdf')
		# 	b.operator('scene.lm_update_json', icon='IMPORT', text='Update all Json Data').mode = 'ALL'
		# 	b.operator("scene.lm_render_assets", icon='OUTPUT', text='Render all assets').render_list = 'ALL'
		# 	b.operator("scene.lm_render_assets", icon='OUTPUT', text='Re-Render last rendered assets').render_list = 'LAST_RENDERED'
			
		# 	if len(context.scene.lm_render_message):
		# 		b.label(text=context.scene.lm_render_message)
		# 	if len(context.scene.lm_render_progress):
		# 		b.label(text=context.scene.lm_render_progress)
		# 	b = layout.box()
		# 	b.prop(scn,'lm_force_composite', text='Force Composite')
		# 	b.operator("scene.lm_compositerenders", icon='NODE_COMPOSITING', text='Composite rendered assets').composite_list = 'ALL'
		# 	b = layout.box()
		# 	b.prop(scn, 'lm_open_pdf_when_exported', text='Open When Exported')
		# 	b.operator("scene.lm_export_pdf", icon='WORDWRAP_ON', text='Export PDF').mode = 'ALL'
		# 	if len(context.scene.lm_pdf_message):
		# 		b.label(text=context.scene.lm_pdf_message)
		# 	if len(context.scene.lm_pdf_progress):
		# 		b.label(text=context.scene.lm_pdf_progress)


class LM_PT_NamingConvention(LM_PT_LineupSetup, bpy.types.Panel):
	bl_label = "3- Naming Convention"
	bl_parent_id = 'lineup_setup'

	def draw(self, context):
		scn = context.scene
		wm = context.window_manager
		layout = self.layout

		if not wm.lm_is_lineup_scene:
			layout.label(text=not_a_lineup)
			return

		b = layout.box()
		b.prop(wm, "lm_show_help", text='', icon='QUESTION')
		if wm.lm_show_help:
			text='Here you need to define the naming convention for your project. It is necessary to organise the output renders into chapters for exemple'
			_label_multiline(context=context, text=text, parent=b)
			text='1- Start by defining the what keywords is used in your naming convention, like the project, the team,  the gender or biome'
			_label_multiline(context=context, text=text, parent=b)
			text='2- Then for each keyword you can assign multiple keyword values to help for better recognition. It is not mandatory but if you know some specific value can be set for some keywords,  I would recomend to fill them'
			_label_multiline(context=context, text=text, parent=b)
			text='3- Finaly for Asset, Mesh and Texture Naming convention, you have to build in which order each keyword is used in your naming convention'
			_label_multiline(context=context, text=text, parent=b)
			text='		3-a- Start by selecting a keyword you have created on step1'
			_label_multiline(context=context, text=text, parent=b)
			text='		3-b- Then click on "Regular", "Optionnal" or "Excluded" to insert the selected keyword in the good naming convention category'
			_label_multiline(context=context, text=text, parent=b)
			text='		3-c- You can also edit the naming convention line directly by adding hard coded text. For exemple if you can add "LOD0" at the end of Mesh naming convention if you know that all of your mesh object finish by that'
			_label_multiline(context=context, text=text, parent=b)

		# Keywords Setup
		# Main Box
		main_box = layout.box()	
		main_row = main_box.row(align=True)
		keyword_box = main_row.box()
		keyword_box.label(text='Keywords')
		sub_row = keyword_box.row()
		col = sub_row.column(align=True)
		
		rows = len(scn.lm_keywords) if len(scn.lm_keywords) > 2 else 2
		col.template_list('LM_UL_keywords', '', scn, 'lm_keywords', scn, 'lm_keyword_idx', rows=rows)

		col = sub_row.column(align=True)
		col.operator('scene.lm_add_keyword', text="", icon='ADD')

		col.separator()
		col.operator("scene.lm_move_keyword", text="", icon='TRIA_UP').direction = "UP"
		col.operator("scene.lm_move_keyword", text="", icon='TRIA_DOWN').direction = "DOWN"

		col.separator()
		col.operator("scene.lm_clear_keywords", text="", icon='TRASH')

		# Keyword Value
		keyword_value_box = main_row.box()
		keyword_value_box.label(text=f'"{scn.lm_keywords[scn.lm_keyword_idx].name}" keyword values')
		sub_row = keyword_value_box.row()
		col = sub_row.column(align=True)
		
		rows = len(scn.lm_keyword_values) if len(scn.lm_keyword_values) > 4 else 4
		col.template_list('LM_UL_keyword_values', '', scn, 'lm_keyword_values', scn, 'lm_keyword_value_idx', rows=rows)

		col = sub_row.column(align=True)
		col.operator('scene.lm_add_keyword_value', text="", icon='ADD')

		col.separator()
		col.operator("scene.lm_move_keyword_value", text="", icon='TRIA_UP').direction = "UP"
		col.operator("scene.lm_move_keyword_value", text="", icon='TRIA_DOWN').direction = "DOWN"

		col.separator()
		col.operator("scene.lm_clear_keyword_values", text="", icon='TRASH')

		# NAMING CONVENTION SETUP
		col = layout.column(align=True)
		col.separator()
		col.prop(scn, 'lm_separator', text = 'Separator')
		col.separator()
		b = col.box()
		b.label(text='Asset Naming Convention')
		br = b.box()
		bbr = br.split(align=True)
		
		op = bbr.operator("scene.lm_add_asset_keyword", text='Regular', icon='ADD')
		op.optionnal = False
		op.excluded = False
		op = bbr.operator("scene.lm_add_asset_keyword", text='Optionnal(?)', icon='ADD')
		op.optionnal = True
		op.excluded = False
		op = bbr.operator("scene.lm_add_asset_keyword", text='Excluded(!)', icon='ADD')
		op.optionnal = False
		op.excluded = True
		bbr.operator("scene.lm_remove_asset_keyword", text='Remove Last', icon='REMOVE')
		
		b.prop(scn, 'lm_asset_naming_convention', text='')
		col.separator()

		b = col.box()
		b.label(text='Mesh Naming Convention')
		br = b.box()
		bbr = br.split(align=True)
		op = bbr.operator("scene.lm_add_mesh_keyword", text='Regular', icon='ADD')
		op.optionnal = False
		op.excluded = False
		op = bbr.operator("scene.lm_add_mesh_keyword", text='Optionnal(?)', icon='ADD')
		op.optionnal = True
		op.excluded = False
		op = bbr.operator("scene.lm_add_mesh_keyword", text='Excluded(!)', icon='ADD')
		op.optionnal = False
		op.excluded = True
		bbr.operator("scene.lm_remove_mesh_keyword", text='Remove Last', icon='REMOVE')

		b.prop(scn, 'lm_mesh_naming_convention', text='')
		col.separator()

		b = col.box()
		b.label(text='Texture Naming Convention')
		br = b.box()
		bbr = br.split(align=True)
		op = bbr.operator("scene.lm_add_texture_keyword", text='Regular', icon='ADD')
		op.optionnal = False
		op.excluded = False
		op = bbr.operator("scene.lm_add_texture_keyword", text='Optionnal(?)', icon='ADD')
		op.optionnal = True
		op.excluded = False
		op = bbr.operator("scene.lm_add_texture_keyword", text='Excluded(!)', icon='ADD')
		op.optionnal = False
		op.excluded = True
		bbr.operator("scene.lm_remove_texture_keyword", text='Remove Last', icon='REMOVE')

		b.prop(scn, 'lm_texture_naming_convention', text='')
		col.separator()




class LM_PT_TextureSetSettings(LM_PT_LineupSetup, bpy.types.Panel):
	bl_label = "4- TextureSet Settings"
	bl_parent_id = 'lineup_setup'

	def draw(self, context):
		scn = context.scene
		wm = context.window_manager

		layout = self.layout

		if not wm.lm_is_lineup_scene:
			layout.label(text=not_a_lineup)
			return

		b = layout.box()
		b.prop(wm, "lm_show_help", text='', icon='QUESTION')
		if wm.lm_show_help:
			text='Here you need to define the shaders, channel and textureset informations, in case data come from another DCC or if you need to control how textures are linked to the shader'
			_label_multiline(context=context, text=text, parent=b)

		main_row = layout.row()
		box1 = main_row.box()
		col = box1.column(align=True)
		col.label(text='Shader Name')
		row = col.row()
		
		rows = len(scn.lm_shaders) if len(scn.lm_shaders) > 2 else 2
		row.template_list('LM_UL_shaders', '', scn, 'lm_shaders', scn, 'lm_shader_idx', rows=rows)

		c = row.column(align=True)
		c.operator('scene.lm_add_shader', text="", icon='ADD')

		c.separator()
		c.operator("scene.lm_move_shader", text="", icon='TRIA_UP').direction = "UP"
		c.operator("scene.lm_move_shader", text="", icon='TRIA_DOWN').direction = "DOWN"

		c.separator()
		c.operator("scene.lm_clear_shaders", text="", icon='TRASH')

		box2 = main_row.box()
		col = box2.column(align=True)
		col.label(text='Channel Name')
		row = col.row()
		
		rows = len(scn.lm_shader_channels) if len(scn.lm_shader_channels) > 4 else 4
		row.template_list('LM_UL_shaderChannels', '', scn, 'lm_shader_channels', scn, 'lm_shader_channel_idx', rows=rows)
		c = row.column(align=True)
		c.operator('scene.lm_add_shader_channel', text="", icon='ADD')

		c.separator()
		c.operator("scene.lm_move_channel", text="", icon='TRIA_UP').direction = "UP"
		c.operator("scene.lm_move_channel", text="", icon='TRIA_DOWN').direction = "DOWN"

		c.separator()
		c.operator("scene.lm_clear_channels", text="", icon='TRASH')


		box3 = main_row.box()
		col = box3.column(align=True)
		col.label(text='Texture Name')
		row = col.row()
		
		rows = len(scn.lm_texture_channels) if len(scn.lm_texture_channels) > 4 else 4
		row.template_list('LM_UL_texturesets', '', scn, 'lm_texture_channels', scn, 'lm_texture_channel_idx', rows=rows)
		c = row.column(align=True)

		c.operator('scene.lm_add_texture_channel', text="", icon='ADD')

		c.separator()
		c.operator("scene.lm_move_texture_channel", text="", icon='TRIA_UP').direction = "UP"
		c.operator("scene.lm_move_texture_channel", text="", icon='TRIA_DOWN').direction = "DOWN"

		c.separator()
		c.operator("scene.lm_clear_texture_channels", text="", icon='TRASH')

		b = layout.box()
		b.label(text='Material Override')

		r = b.row(align=True)
		r.prop(scn, 'lm_override_material_color', text='Override Material Color')
		r.scale_x = 3
		r.prop(scn, 'lm_default_material_color', text='')

		r = b.row(align=True)
		r.prop(scn, 'lm_override_material_roughness', text='Override Material Roughness')
		r.scale_x = 3
		r.prop(scn, 'lm_default_material_roughness',text='')

		r = b.row(align=True)
		r.prop(scn, 'lm_override_material_specular', text='Override Material Specular')
		r.scale_x = 3
		r.prop(scn, 'lm_default_material_specular',text='')


class LM_PT_Cameras(LM_PT_LineupSetup, bpy.types.Panel):          
	bl_label = "5- Camera Assignment"
	bl_parent_id = 'lineup_setup'

	
	def draw(self, context):
		scn = context.scene
		wm = context.window_manager
		layout = self.layout

		if not wm.lm_is_lineup_scene:
			layout.label(text=not_a_lineup)
			return

		col = layout.column(align=True)
		b = col.box()
		b.prop(scn, 'lm_default_camera', text='Default Camera')
		b.label(text='Cameras')
		row = b.row()
		rows = 20 if len(scn.lm_cameras) > 20 else len(scn.lm_cameras) + 1
		
		row.template_list('LM_UL_cameras', '', scn, 'lm_cameras', scn, 'lm_camera_idx', rows=rows)
		c = row.column(align=True)
		
		c.operator("scene.lm_add_camera_keywords", text="", icon='ADD')
		c.operator("scene.lm_move_camera_keyword", text="", icon='TRIA_UP').direction = "UP"
		c.operator("scene.lm_move_camera_keyword", text="", icon='TRIA_DOWN').direction = "DOWN"

		c.separator()
		c.operator("scene.lm_clear_camera_keywords", text="", icon='TRASH')
		c.operator("scene.lm_remove_camera_keyword", text="", icon='X')



class LM_PT_CompositeLayout(LM_PT_LineupSetup, bpy.types.Panel):
	bl_label = "6- Composite Layout"
	bl_parent_id = 'lineup_setup'

	
	def draw(self, context):
		scn = context.scene
		wm = context.window_manager
		layout = self.layout

		if not wm.lm_is_lineup_scene:
			layout.label(text=not_a_lineup)
			return

		col = layout.column(align=True)

		col.prop(scn, 'lm_content_background_color', text='Content Backgroud Color')
		col.prop(scn, 'lm_text_background_color', text='Text Backgroud Color')
		col.prop(scn, 'lm_font_color', text='Font Color')


class LM_PT_Chapter(LM_PT_LineupSetup, bpy.types.Panel):          
	bl_label = "7- Chapter Definition"
	bl_parent_id = 'lineup_setup'

	
	def draw(self, context):
		scn = context.scene
		wm = context.window_manager
		layout = self.layout

		if not wm.lm_is_lineup_scene:
			layout.label(text=not_a_lineup)
			return

		col = layout.column(align=True)
		b = col.box()
		b.label(text='Keywords')
		
		row = b.row()
		
		rows = 20 if len(scn.lm_keywords) > 20 else len(scn.lm_keywords) + 1
		row.template_list('LM_UL_keywords', '', scn, 'lm_keywords', scn, 'lm_keyword_idx', rows=rows)

		b.operator('scene.lm_add_chapter_keyword', text='Add selected keyword in chapter')
		row = b.row()
		row.prop(scn, 'lm_chapter_naming_convention', text='Chapter Keywords')
		row.operator('scene.lm_remove_chapter_keyword', icon='X', text="")


class LM_PT_Preset(bpy.types.Panel):
	bl_label = "Preset"
	bl_space_type = "VIEW_3D"
	bl_region_type = "UI"
	bl_category = 'Lineup Maker'
	bl_options = {"DEFAULT_CLOSED"}

	
	def draw(self, context):
		scn = context.scene
		layout = self.layout


		col = layout.column(align=True)
		b = col.box()
		
		b.operator('scene.lm_save_preset', text='Save Preset', icon='OPTIONS')
		b.operator('scene.lm_load_preset', text='Load Preset', icon='OPTIONS')

class LM_PT_AssetList(bpy.types.Panel):          
	bl_label = "Asset List"
	bl_space_type = "VIEW_3D"
	bl_region_type = "UI"
	bl_category = 'Lineup Maker'
	bl_options = {"DEFAULT_CLOSED"}

	
	def draw(self, context):
		scn = context.scene
		wm = context.window_manager
		layout = self.layout

		if not wm.lm_is_lineup_scene:
			layout.label(text=not_a_lineup)
			return

		col = layout.column(align=True)
		b = col.box()
		
		if len(context.scene.lm_import_message):
			b.label(text=context.scene.lm_import_message)
		if len(context.scene.lm_import_progress):
			b.label(text=context.scene.lm_import_progress)
		if len(context.scene.lm_viewlayer_progress):
			b.label(text=context.scene.lm_viewlayer_progress)
		
		b.label(text='Import List  |  {} asset(s)'.format(len(scn.lm_import_list)))
		
		b.prop(scn, 'lm_import_autosave_step')
		row = b.row()
		rows = 20 if len(scn.lm_import_list) > 10 else len(scn.lm_import_list) * 2 + 1
		
		row.template_list('LM_UL_import_list', '', scn, 'lm_import_list', scn, 'lm_import_list_idx', rows=rows)
		c = row.column(align=True)
		
		c.operator('scene.lm_refresh_import_list', text='', icon='ADD').refresh_warnings = False
		c.operator('scene.lm_refresh_import_list', text='', icon='FILE_REFRESH')
		
		c.separator()
		c.operator("scene.lm_check_all_import_list", text="", icon='CHECKBOX_HLT')
		c.operator("scene.lm_uncheck_all_import_list", text="", icon='CHECKBOX_DEHLT')

		c.separator()
		c.operator("scene.lm_clear_asset_folder", text="", icon='X')
		c.operator("scene.lm_remove_asset_folder", text="", icon='TRASH').mode = 'IMPORT'

		c.separator()
		c.operator('scene.lm_create_blend_catalog_file', text='', icon='IMPORT').mode = 'IMPORT'
		c.operator('scene.lm_create_blend_catalog_file', text='', icon='IMPORT').mode = 'IMPORT_NEW'

		c.separator()
		c.operator('scene.lm_import_list', text='', icon='SORT_ASC')

		c.separator()
		c.separator()
		b.label(text='Asset List  |  {} asset(s)'.format(len(scn.lm_asset_list)))
		row = b.row()
		
		rendered = [a for a in scn.lm_asset_list if a.rendered]
		composited = [a for a in scn.lm_asset_list if a.composited]
		b.label(text='{} assets  /  {} rendered  /  {} composited'.format(len(scn.lm_asset_list), len(rendered), len(composited)))
		b.separator()
		rows = 20 if len(scn.lm_asset_list) > 10 else len(scn.lm_asset_list) * 2 + 1
		
		row.template_list('LM_UL_asset_list', '', scn, 'lm_asset_list', scn, 'lm_asset_list_idx', rows=rows)
		c = row.column(align=True)
		c.operator('scene.lm_refresh_asset_status', text='', icon='FILE_REFRESH').mode='ALL'
		c.operator('scene.lm_fix_view_layers', text='', icon='MODIFIER_DATA').asset_name=''


		c.separator()
		c.operator("scene.lm_clear_asset_list", text="", icon='TRASH')

		c.separator()
		c.operator('scene.lm_add_need_render_to_render_queue', text='', icon='SORT_ASC')


		row.separator()
		row = b.row()
		row.label(text='Render Queue  |  {} asset(s)'.format(len(scn.lm_render_queue)))
		row.label(text='{}'.format(scn.lm_queue_message))
		row.label(text='{}'.format(scn.lm_queue_progress))
		row = b.row()
		rows = 11 if len(scn.lm_render_queue) > 10 else len(scn.lm_render_queue) + 1
		row.template_list('LM_UL_asset_list_RenderQueue', '', scn, 'lm_render_queue', scn, 'lm_render_queue_idx', rows=rows)
		c = row.column(align=True)

		c.operator('scene.lm_check_all_render_queued_asset', text='', icon='CHECKBOX_HLT')
		c.operator('scene.lm_uncheck_all_render_queued_asset', text='', icon='CHECKBOX_DEHLT')
		c.separator()
		c.operator("scene.lm_move_asset_to_render", text="", icon='TRIA_UP').direction = "UP"
		c.operator("scene.lm_move_asset_to_render", text="", icon='TRIA_DOWN').direction = "DOWN"
		c.separator()
		c.operator('scene.lm_refresh_asset_status', text='', icon='FILE_REFRESH').mode='QUEUE'
		c.separator()
		c.operator("scene.lm_delete_render_queue_asset", text="", icon='TRASH')
		c.operator("scene.lm_clear_asset_from_render_queue_list", text="", icon='X')
		c.operator("scene.lm_remove_already_rendered_asset_from_render_queue", text="", icon='RENDER_RESULT')
		
		c.separator()
		c.operator("scene.lm_create_blend_catalog_file", text="", icon='IMPORT').mode = "QUEUE"
		c.operator("scene.lm_export_assets", text="", icon='EXPORT').mode = "QUEUE"
		c.separator()
		c.operator('scene.lm_export_queue_list', text='', icon='SORT_DESC')
		
		# c.operator("scene.lm_remove_asset_from_render", text="", icon='X')

		if len(scn.lm_render_queue):
			b = layout.box()
			b.prop(scn, 'lm_precomposite_frames')
			b.prop(scn, 'lm_override_frames')
			b.prop(scn, 'lm_force_render', text='Force')
			b.prop(scn, 'lm_pdf_export_last_rendered', text='Export Last rendered asset to pdf')
			b.prop(scn, 'lm_simultaneous_render_count', text='Simultaneous render count')
			b.operator('scene.lm_update_json', icon='IMPORT', text='Update Queued Json Data').mode = 'QUEUE'
			b.operator('scene.lm_render_assets', text='Render queued list', icon='OUTPUT').render_list = 'QUEUED'
			b.operator("scene.lm_render_assets", icon='OUTPUT', text='Re-Render last rendered assets').render_list = 'LAST_RENDERED'
			if len(context.scene.lm_render_message):
				b.label(text=context.scene.lm_render_message)
			if len(context.scene.lm_render_progress):
				b.label(text=context.scene.lm_render_progress)
			b = layout.box()
			b.prop(scn,'lm_force_composite', text='Force Composite')
			b.operator("scene.lm_compositerenders", icon='NODE_COMPOSITING', text='Composite rendered assets').composite_list = 'QUEUED'
			b = layout.box()
			b.prop(scn, 'lm_open_pdf_when_exported', text='Open When Exported')
			b.operator("scene.lm_export_pdf", icon='WORDWRAP_ON', text='Export PDF').mode = "QUEUE"
			if len(context.scene.lm_pdf_message):
				b.label(text=context.scene.lm_pdf_message)
			if len(context.scene.lm_pdf_progress):
				b.label(text=context.scene.lm_pdf_progress)


class LM_PT_ExportAsset(bpy.types.Panel):          
	bl_label = "Export Asset"
	bl_space_type = "VIEW_3D"
	bl_region_type = "UI"
	bl_category = 'Lineup Maker'
	bl_options = {"DEFAULT_CLOSED"}

	
	def draw(self, context):
		scn = context.scene
		layout = self.layout
		asset_path = bpy.path.abspath(scn.lm_asset_path)

		col = layout.column(align=True)
		b = col.box()

		if path.isdir(asset_path):
			icon = "DOWNARROW_HLT"
		else:
			icon = "BLANK1"
			
		b.prop(scn, 'lm_asset_path', text='Asset Path', icon=icon)
		
		b.prop(scn, 'lm_exported_asset_name', text='Export Name')
		b.prop(scn, 'lm_exported_hd_status', text='HD Status')
		b.prop(scn, 'lm_exported_ld_status', text='LD Status')
		b.prop(scn, 'lm_exported_baking_status', text='Baking Status')
		if path.exists(asset_path):
			export = b.operator('scene.lm_export_assets', text='Export Selected Asset', icon='EXPORT')
			export.mode = 'SELECTED'