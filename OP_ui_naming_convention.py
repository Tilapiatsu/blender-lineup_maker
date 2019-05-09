import bpy

def get_keyword(context):
    idx = context.scene.lm_keyword_idx
    keywords = context.scene.lm_keywords

    active = keywords[idx] if keywords else None

    return idx, keywords, active

def add_keyword(context, naming_convention, keyword, optionnal):
    if len(naming_convention):
        return '{}{}{}{}{}{}'.format(naming_convention, context.scene.lm_separator, '<', keyword,('?' if optionnal else '' ),  '>')
    else:
        return '{}{}{}{}{}'.format(naming_convention, '<', keyword, ('?' if optionnal else '' ),  '>')

class LM_UI_AddAssetKeyword(bpy.types.Operator):
    bl_idname = "scene.lm_add_asset_keyword"
    bl_label = "Add Keyword to the current naming convention"
    bl_options = {'REGISTER', 'UNDO'}

    keyword: bpy.props.StringProperty(default='')

    def execute(self, context):
        if self.keyword == '':
            idx, channel, keyword = get_keyword(context)

        context.scene.lm_asset_naming_convention = add_keyword(context, context.scene.lm_asset_naming_convention, keyword.name.upper(), context.scene.lm_optionnal_asset_keyword)

        return {'FINISHED'}
