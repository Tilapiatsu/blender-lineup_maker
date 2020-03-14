import bpy
from os import path
from . import variables as V

class LM_Render_List(bpy.types.PropertyGroup):
    render_filepath : bpy.props.StringProperty(name="Render path", subtype='FILE_PATH')

class LM_Texture_List(bpy.types.PropertyGroup):
    name : bpy.props.StringProperty(name='Texture name')
    image : bpy.props.PointerProperty(name='Image', type=bpy.types.Image)
    file_path : bpy.props.StringProperty(name='Texture File')
    channel : bpy.props.StringProperty(name='channel')

class LM_Material_List(bpy.types.PropertyGroup):
    name : bpy.props.StringProperty(name="Material Name")
    material : bpy.props.PointerProperty(name='Material', type=bpy.types.Material)
    texture_list : bpy.props.CollectionProperty(type=LM_Texture_List)

class LM_MeshObject_List(bpy.types.PropertyGroup):
    name : bpy.props.StringProperty(name="File Name")
    mesh : bpy.props.PointerProperty(name='Mesh', type=bpy.types.Object) 
    material_list : bpy.props.CollectionProperty(type=LM_Material_List)

class LM_MeshFile_List(bpy.types.PropertyGroup):
    name : bpy.props.StringProperty(name="File Name")
    mesh_object_list : bpy.props.CollectionProperty(type=LM_MeshObject_List)
    file_path : bpy.props.StringProperty(name="File Path")
    file_size : bpy.props.FloatProperty(name="File Size")
    import_date : bpy.props.FloatProperty(name="Last Import")
    material_list : bpy.props.CollectionProperty(type=LM_Material_List)

class LM_Asset_List(bpy.types.PropertyGroup):
    render_date : bpy.props.FloatProperty(name="Last Render")
    import_date : bpy.props.FloatProperty(name="Import Date")
    mesh_list : bpy.props.CollectionProperty(type=LM_MeshFile_List)
    material_list : bpy.props.CollectionProperty(type=LM_Material_List)
    texture_list : bpy.props.CollectionProperty(type=LM_Texture_List)
    view_layer : bpy.props.StringProperty(name="View Layer")
    collection : bpy.props.PointerProperty(type=bpy.types.Collection)
    need_render : bpy.props.BoolProperty()
    rendered : bpy.props.BoolProperty()
    need_composite : bpy.props.BoolProperty()
    composited : bpy.props.BoolProperty()
    asset_path : bpy.props.StringProperty(subtype='DIR_PATH')
    render_path : bpy.props.StringProperty(subtype='DIR_PATH')
    render_camera : bpy.props.StringProperty(name="Render camera")
    asset_folder_exists : bpy.props.BoolProperty()
    
    raw_composite_filepath : bpy.props.StringProperty(subtype='FILE_PATH')
    final_composite_filepath : bpy.props.StringProperty(subtype='FILE_PATH')
    render_list : bpy.props.CollectionProperty(type=LM_Render_List)

    need_write_info : bpy.props.BoolProperty(default=False)
    info_written : bpy.props.BoolProperty(default=False)

    asset_number : bpy.props.IntProperty()
    asset_index : bpy.props.IntProperty()
    hd_status : bpy.props.IntProperty(default=-1)
    ld_status : bpy.props.IntProperty(default=-1)
    baking_status : bpy.props.IntProperty(default=-1)
    triangles : bpy.props.IntProperty()
    vertices : bpy.props.IntProperty()
    has_uv2 : bpy.props.BoolProperty(default=False)

class LM_Shaders(bpy.types.PropertyGroup):
    name: bpy.props.StringProperty()

class LM_Channels(bpy.types.PropertyGroup):
    name: bpy.props.StringProperty()
    shader: bpy.props.StringProperty()
    linear: bpy.props.BoolProperty()
    normal_map: bpy.props.BoolProperty()
    inverted: bpy.props.BoolProperty()

class LM_TextureChannels(bpy.types.PropertyGroup):
    name: bpy.props.StringProperty()
    channel : bpy.props.StringProperty()
    shader: bpy.props.StringProperty()

class LM_Keywords(bpy.types.PropertyGroup):
    name: bpy.props.StringProperty()

class LM_KeywordValues(bpy.types.PropertyGroup):
    name: bpy.props.StringProperty()
    keyword: bpy.props.StringProperty()

class LM_CamerasKeywords(bpy.types.PropertyGroup):
    keyword: bpy.props.StringProperty()
    keyword_value: bpy.props.StringProperty()

class LM_Cameras(bpy.types.PropertyGroup):
    camera: bpy.props.PointerProperty(type=bpy.types.Object)
    keywords : bpy.props.CollectionProperty(type=LM_CamerasKeywords)


# UI List

class LM_UL_Shader_UIList(bpy.types.UIList):
    bl_idname = "LM_UL_shaders"

    def draw_item(self, context, layout, data, item, icon, active_data, active_propname, index):
        row = layout.split(factor=0.7)
        row.label(text='{}'.format(item.name))

class LM_UL_Channel_UIList(bpy.types.UIList):
    bl_idname = "LM_UL_channels"

    def draw_item(self, context, layout, data, item, icon, active_data, active_propname, index):
        row = layout.split(factor=0.7)
        channel_format = ''
        if item.normal_map:
            channel_format = channel_format + ' | NormalMap'
        elif item.linear:
            channel_format = channel_format + ' | Linear'
        else:
            channel_format = ' | SRGB'
        if item.inverted:
            channel_format = channel_format + ' Inverted'
        row.label(text='{} : {} {}'.format(item.shader, item.name, channel_format))

class LM_UL_TextureSet_UIList(bpy.types.UIList):
    bl_idname = "LM_UL_texturesets"

    def draw_item(self, context, layout, data, item, icon, active_data, active_propname, index):
        row = layout.split(factor=0.7)
        row.label(text='{} - {} : {}'.format(item.shader, item.channel, item.name))

class LM_UL_Keywords_UIList(bpy.types.UIList):
    bl_idname = "LM_UL_keywords"

    def draw_item(self, context, layout, data, item, icon, active_data, active_propname, index):
        row = layout.split(factor=0.7)
        row.label(text='{}'.format(item.name))

class LM_UL_KeywordValues_UIList(bpy.types.UIList):
    bl_idname = "LM_UL_keyword_values"

    def draw_item(self, context, layout, data, item, icon, active_data, active_propname, index):
        row = layout.split(factor=0.7)
        row.label(text='{} : {}'.format(item.keyword, item.name))

class LM_UL_Cameras_UIList(bpy.types.UIList):
    bl_idname = "LM_UL_cameras"

    def draw_item(self, context, layout, data, item, icon, active_data, active_propname, index):
        row = layout.split(factor=0.7)
        text = ''
        for i,keyword in enumerate(item.keywords):
            text += '"{}" = "{}"'.format(keyword.keyword, keyword.keyword_value)
            if i < len(item.keywords) - 1:
                text += ' and '
        row.label(text='"{}" : {}'.format(item.camera.name, text))

class LM_UL_AssetList_UIList(bpy.types.UIList):
    bl_idname = "LM_UL_asset_list"

    def draw_item(self, context, layout, data, item, icon, active_data, active_propname, index):
        self.use_filter_sort_alpha = True
        
        scn = context.scene

        col = layout.column_flow(columns=3, align=True)

        row = col.row(align=True)
        row.alignment = 'LEFT'
        if context.window.view_layer.name == item.name:
            eye_icon = 'HIDE_ON'
            row.operator('scene.lm_show_asset', text='', icon=eye_icon).asset_name = context.scene.lm_initial_view_layer
        else:
            eye_icon = 'HIDE_OFF'
            row.operator('scene.lm_show_asset', text='', icon=eye_icon).asset_name = item.name
        

        row.label(text='{}'.format(item.name))
        # row.label(text='              ')

        row = col.row(align=True)
        row.alignment = 'LEFT'
        row.label(text='{}'.format(item.render_camera), icon='CAMERA_DATA')
        
        row = col.row(align=True)
        row.alignment = 'RIGHT'

        if scn.lm_asset_list[item.name].rendered:
            row.operator('scene.lm_open_render_folder', text='', icon='RENDER_RESULT').asset_name = item.name
        else:
            self.separator_iter(row, 3)
        
        if scn.lm_asset_list[item.name].asset_folder_exists:
            row.operator('scene.lm_open_asset_folder', text='', icon='SNAP_VOLUME').asset_name = item.name
        else:
            self.separator_iter(row, 3)
        
        export = row.operator('scene.lm_export_asset', text='', icon='EXPORT')
        export.asset_name = item.name
        export.mode = 'ASSET'

        op = row.operator('scene.lm_importassets', text='', icon='IMPORT')
        op.asset_name = item.name
        op.mode = "ASSET"
        row.operator('scene.lm_refresh_asset_status', text='', icon='FILE_REFRESH').asset_name = item.name
        
        row.separator()
        row.operator('scene.lm_add_asset_to_render_queue', text='', icon='SORT_ASC').asset_name = item.name
        row.operator('scene.lm_remove_asset', text='', icon='X').asset_name = item.name

        
    def separator_iter(self, ui, iter) :
        for i in range(iter):
            ui.separator()

class LM_UL_AssetListRQ_UIList(bpy.types.UIList):
    bl_idname = "LM_UL_asset_list_RenderQueue"

    def draw_item(self, context, layout, data, item, icon, active_data, active_propname, index):
        scn = context.scene

        col = layout.column_flow(columns=3, align=True)
        text = item.name

        row = col.row(align=True)
        row.alignment = 'LEFT'
        if context.window.view_layer.name == item.name:
            eye_icon = 'HIDE_ON'
            row.operator('scene.lm_show_asset', text='', icon=eye_icon).asset_name = context.scene.lm_initial_view_layer
        else:
            eye_icon = 'HIDE_OFF'
            row.operator('scene.lm_show_asset', text='', icon=eye_icon).asset_name = item.name
            
        c = col.row(align=True)
        c.alignment='LEFT'
        row.label(text='{}'.format(item.name))

        row = col.row(align=True)
        row.alignment = 'LEFT'
        row.label(text='{}'.format(item.render_camera), icon='CAMERA_DATA')


        row = col.row(align=True)
        row.alignment = 'RIGHT'

        if scn.lm_asset_list[item.name].rendered:
            row.operator('scene.lm_open_render_folder', text='', icon='RENDER_RESULT').asset_name = item.name
        else:
            self.separator_iter(row, 3)
        
        if scn.lm_asset_list[item.name].asset_folder_exists:
            row.operator('scene.lm_open_asset_folder', text='', icon='SNAP_VOLUME').asset_name = item.name
        else:
            self.separator_iter(row, 3)


        export = row.operator('scene.lm_export_asset', text='', icon='EXPORT')
        export.asset_name = item.name
        export.mode = 'ASSET'
        
        op = row.operator('scene.lm_importassets', text='', icon='IMPORT')
        op.asset_name = item.name
        op.mode = "ASSET"
        row.operator('scene.lm_refresh_asset_status', text='', icon='FILE_REFRESH').asset_name = item.name
        
        row.separator()
        row.operator('scene.lm_remove_asset_to_render', text='', icon='X').asset_name = item.name
        

        
    def separator_iter(self, ui, iter) :
        for i in range(iter):
            ui.separator()