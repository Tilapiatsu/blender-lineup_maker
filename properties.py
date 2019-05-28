import bpy



class LM_Material_List(bpy.types.PropertyGroup):
    name = bpy.props.StringProperty(name="Material Name")
    material = bpy.props.PointerProperty(name='Material', type=bpy.types.Material)

class LM_Mesh_List(bpy.types.PropertyGroup):
    name : bpy.props.StringProperty(name="Asset Name")
    mesh_name = bpy.props.StringProperty(name="Mesh Name")
    file_path = bpy.props.StringProperty(name="File Path")
    mesh = bpy.props.PointerProperty(name='Mesh', type=bpy.types.Object)
    material_list = bpy.props.CollectionProperty(type=LM_Material_List)

class LM_Texture_List(bpy.types.PropertyGroup):
    textureset_name = bpy.props.StringProperty(name="TextureSet Name")
    albedo = bpy.props.PointerProperty(name='Albedo', type=bpy.types.Texture)
    normal = bpy.props.PointerProperty(name='Normal', type=bpy.types.Texture)
    roughness = bpy.props.PointerProperty(name='Roughness', type=bpy.types.Texture)
    metalic = bpy.props.PointerProperty(name='Metalic', type=bpy.types.Texture)

class LM_Asset_List(bpy.types.PropertyGroup):
    import_date = bpy.props.FloatProperty(name="Last Import")
    render_date = bpy.props.FloatProperty(name="Last Render")
    mesh_list = bpy.props.CollectionProperty(type=LM_Mesh_List)
    material_list = bpy.props.CollectionProperty(type=LM_Material_List)
    texture_list = bpy.props.CollectionProperty(type=LM_Texture_List)
    view_layer = bpy.props.StringProperty(name="View Layer")
    collection = bpy.props.PointerProperty(type=bpy.types.Collection)
    need_render = bpy.props.BoolProperty()
    rendered = bpy.props.BoolProperty()
    render_path = bpy.props.StringProperty()

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