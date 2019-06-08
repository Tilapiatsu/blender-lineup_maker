import bpy

class LM_Render_List(bpy.types.PropertyGroup):
    render_filepath = bpy.props.StringProperty(name="Render path", subtype='FILE_PATH')

class LM_Material_List(bpy.types.PropertyGroup):
    name = bpy.props.StringProperty(name="Material Name")
    material = bpy.props.PointerProperty(name='Material', type=bpy.types.Material)

class LM_MeshObject_List(bpy.types.PropertyGroup):
    name = bpy.props.StringProperty(name="File Name")
    mesh = bpy.props.PointerProperty(name='Mesh', type=bpy.types.Object) 
    material_list = bpy.props.CollectionProperty(type=LM_Material_List)

class LM_MeshFile_List(bpy.types.PropertyGroup):
    name = bpy.props.StringProperty(name="File Name")
    mesh_object_list = bpy.props.CollectionProperty(type=LM_MeshObject_List)
    file_path = bpy.props.StringProperty(name="File Path")
    file_size = bpy.props.FloatProperty(name="File Size")
    import_date = bpy.props.FloatProperty(name="Last Import")
    material_list = bpy.props.CollectionProperty(type=LM_Material_List)

class LM_Texture_List(bpy.types.PropertyGroup):
    file_path = bpy.props.StringProperty(name='Texture File')
    channel = bpy.props.StringProperty(name='channel')

class LM_Asset_List(bpy.types.PropertyGroup):
    render_date = bpy.props.FloatProperty(name="Last Render")
    import_date = bpy.props.FloatProperty(name="Import Date")
    mesh_list = bpy.props.CollectionProperty(type=LM_MeshFile_List)
    material_list = bpy.props.CollectionProperty(type=LM_Material_List)
    texture_list = bpy.props.CollectionProperty(type=LM_Texture_List)
    view_layer = bpy.props.StringProperty(name="View Layer")
    collection = bpy.props.PointerProperty(type=bpy.types.Collection)
    need_render = bpy.props.BoolProperty()
    rendered = bpy.props.BoolProperty()
    render_path = bpy.props.StringProperty(subtype='DIR_PATH')
    
    raw_composite_filepath = bpy.props.StringProperty(subtype='FILE_PATH')
    final_composite_filepath = bpy.props.StringProperty(subtype='FILE_PATH')
    render_list = bpy.props.CollectionProperty(type=LM_Render_List)

    need_write_info = bpy.props.BoolProperty(default=False)
    info_written = bpy.props.BoolProperty(default=False)

    asset_number = bpy.props.IntProperty()
    wip = bpy.props.BoolProperty(default=False)
    triangles = bpy.props.IntProperty()
    vertices = bpy.props.IntProperty()
    has_uv2 = bpy.props.BoolProperty(default=False)

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
    keywords = bpy.props.CollectionProperty(type=LM_CamerasKeywords)

# UI List

class LM_Shader_UIList(bpy.types.UIList):
    bl_idname = "LM_UL_shaders"

    def draw_item(self, context, layout, data, item, icon, active_data, active_propname, index):
        row = layout.split(factor=0.7)
        row.label(text='{}'.format(item.name))

class LM_Channel_UIList(bpy.types.UIList):
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

class LM_TextureSet_UIList(bpy.types.UIList):
    bl_idname = "LM_UL_texturesets"

    def draw_item(self, context, layout, data, item, icon, active_data, active_propname, index):
        row = layout.split(factor=0.7)
        row.label(text='{} - {} : {}'.format(item.shader, item.channel, item.name))

class LM_Keywords_UIList(bpy.types.UIList):
    bl_idname = "LM_UL_keywords"

    def draw_item(self, context, layout, data, item, icon, active_data, active_propname, index):
        row = layout.split(factor=0.7)
        row.label(text='{}'.format(item.name))

class LM_KeywordValues_UIList(bpy.types.UIList):
    bl_idname = "LM_UL_keyword_values"

    def draw_item(self, context, layout, data, item, icon, active_data, active_propname, index):
        row = layout.split(factor=0.7)
        row.label(text='{} : {}'.format(item.keyword, item.name))

class LM_Cameras_UIList(bpy.types.UIList):
    bl_idname = "LM_UL_cameras"

    def draw_item(self, context, layout, data, item, icon, active_data, active_propname, index):
        row = layout.split(factor=0.7)
        text = ''
        for i,keyword in enumerate(item.keywords):
            text += '"{}" = "{}"'.format(keyword.keyword, keyword.keyword_value)
            if i < len(item.keywords) - 1:
                text += ' and '
        row.label(text='"{}" : {}'.format(item.camera.name, text))

class LM_AssetList_UIList(bpy.types.UIList):
    bl_idname = "LM_UL_asset_list"

    def draw_item(self, context, layout, data, item, icon, active_data, active_propname, index):
        row = layout.split(factor=0.7)
        text = item.name
        if item.rendered:
            text += ' - Rendered'
        row.label(text='{}'.format(text))