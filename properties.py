import bpy

class LM_Material_List(bpy.types.PropertyGroup):
    material_name = bpy.props.StringProperty(name="Material Name")
    material = bpy.props.PointerProperty(name='Material', type=bpy.types.Material)

class LM_Mesh_List(bpy.types.PropertyGroup):
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
    last_update = bpy.props.FloatProperty(name="Last Update")
    mesh_list = bpy.props.CollectionProperty(type=LM_Mesh_List)
    material_list = bpy.props.CollectionProperty(type=LM_Material_List)
    texture_list = bpy.props.CollectionProperty(type=LM_Texture_List)

class LM_TextureChannels(bpy.types.PropertyGroup):
    name: bpy.props.StringProperty()


class LM_TextureSet_UIList(bpy.types.UIList):
    bl_idname = "LM_UL_append_textureset"

    def draw_item(self, context, layout, data, item, icon, active_data, active_propname, index):
        row = layout.split(factor=0.7)
        row.label(text=item.name)