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

		b = layout.box()
		if path.isdir(asset_path):
			icon = "DOWNARROW_HLT"
		else:
			icon = "BLANK1"
		b.prop(scn, 'lm_asset_path', text='Asset Path', icon=icon)
		
		row = b.row(align=True)
		if path.isdir(render_path):
			icon = "DOWNARROW_HLT"
		else:
			icon = "BLANK1"
		
		row.prop(scn, 'lm_render_path', text='Render Path', icon=icon)
		
		if path.isdir(render_path):

			row.operator("scene.lm_openfolder", icon='WINDOW', text='Open Folder').folder_path = render_path
			
		b.prop(scn, 'lm_render_collection', text='Render Collection', icon='LIGHT')
		
		b = layout.box()
		
		if len(scn.lm_asset_list) == 0:
			text = 'Import all assets'
			imported = False
		else:
			text = 'Update modified assets'
			imported = True
		b.operator("scene.lm_import_assets", icon='IMPORT', text=text).mode = "ALL"
		if len(context.scene.lm_import_message):
			b.label(text=context.scene.lm_import_message)
		if len(context.scene.lm_import_progress):
			b.label(text=context.scene.lm_import_progress)
		if len(context.scene.lm_viewlayer_progress):
			b.label(text=context.scene.lm_viewlayer_progress)
		

		if imported:
			b = layout.box()
			b.prop(scn, 'lm_precomposite_frames')
			b.prop(scn, 'lm_override_frames')
			
			b.prop(scn, 'lm_force_render', text='Force Render')
			b.prop(scn, 'lm_pdf_export_last_rendered', text='Export Last rendered asset to pdf')
			b.operator('scene.lm_update_json', icon='IMPORT', text='Update all Json Data').mode = 'ALL'
			b.operator("scene.lm_render_assets", icon='OUTPUT', text='Render all assets').render_list = 'ALL'
			b.operator("scene.lm_render_assets", icon='OUTPUT', text='Re-Render last rendered assets').render_list = 'LAST_RENDERED'
			
			if len(context.scene.lm_render_message):
				b.label(text=context.scene.lm_render_message)
			if len(context.scene.lm_render_progress):
				b.label(text=context.scene.lm_render_progress)
			b = layout.box()
			b.prop(scn,'lm_force_composite', text='Force Composite')
			b.operator("scene.lm_compositerenders", icon='NODE_COMPOSITING', text='Composite rendered assets').composite_list = 'ALL'
			b = layout.box()
			b.prop(scn, 'lm_open_pdf_when_exported', text='Open When Exported')
			b.operator("scene.lm_export_pdf", icon='WORDWRAP_ON', text='Export PDF').mode = 'ALL'
			if len(context.scene.lm_pdf_message):
				b.label(text=context.scene.lm_pdf_message)
			if len(context.scene.lm_pdf_progress):
				b.label(text=context.scene.lm_pdf_progress)


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
		c.operator("scene.lm_clear_keywords", text="", icon='TRASH')
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
		c.operator("scene.lm_clear_keyword_values", text="", icon='TRASH')
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
		c.operator("scene.lm_clear_shaders", text="", icon='TRASH')
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
		c.operator("scene.lm_clear_channels", text="", icon='TRASH')
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
		c.operator("scene.lm_clear_texture_channels", text="", icon='TRASH')
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

		r = b.row(align=True)
		r.prop(scn, 'lm_override_material_specular', text='Override Material Specular')
		r.scale_x = 3
		r.prop(scn, 'lm_default_material_specular',text='')


class LM_PT_Cameras(bpy.types.Panel):          
	bl_label = "Camera Assignment"
	bl_space_type = "VIEW_3D"
	bl_region_type = "UI"
	bl_category = 'Lineup Maker'
	bl_options = {"DEFAULT_CLOSED"}

	
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
		c.operator("scene.lm_clear_camera_keywords", text="", icon='TRASH')
		c.operator("scene.lm_remove_camera_keyword", text="", icon='X')
		c.separator()
		b.prop(scn, 'lm_camera_keyword_name', text='Camera Keyword')


class LM_PT_Chapter(bpy.types.Panel):          
	bl_label = "Chapter Definition"
	bl_space_type = "VIEW_3D"
	bl_region_type = "UI"
	bl_category = 'Lineup Maker'
	bl_options = {"DEFAULT_CLOSED"}

	
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


class LM_PT_AssetList(bpy.types.Panel):          
	bl_label = "Asset List"
	bl_space_type = "VIEW_3D"
	bl_region_type = "UI"
	bl_category = 'Lineup Maker'
	bl_options = {"DEFAULT_CLOSED"}

	
	def draw(self, context):
		scn = context.scene
		layout = self.layout

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
		c.operator('scene.lm_import_assets', text='', icon='IMPORT').mode = 'IMPORT'

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
		c.separator()
		c.operator("scene.lm_import_assets", text="", icon='IMPORT').mode = "QUEUE"
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