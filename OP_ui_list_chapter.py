import bpy, re
from . import logger as L

def add_keyword(context, naming_convention, keyword):
    if len(naming_convention):
        return '{}{}{}{}{}'.format(naming_convention, context.scene.lm_separator, '<', keyword,   '>')
    else:
        return '{}{}{}{}'.format(naming_convention, '<', keyword, '>')

def slice_keyword(context, convention):
    keyword_pattern = re.compile(r'[{0}]?(<[a-zA-Z0-9^?^!]+>|[a-zA-Z0-9]+)[{0}]?'.format(context.scene.lm_separator), re.IGNORECASE)
    return keyword_pattern.findall(convention)

def remove_keyword(context, convention):
    scn = context.scene
    keyword = slice_keyword(context, convention)
        
    new_keyword = ''
    
    length = len(keyword)
    for i,k in enumerate(keyword):
        if i < length - 1:
            new_keyword = new_keyword + k
        if i < length - 2:
            new_keyword = new_keyword + scn.lm_separator

    return new_keyword

class LM_UI_AddChapterKeyword(bpy.types.Operator):
    bl_idname = "scene.lm_add_chapter_keyword"
    bl_label = "Add Keyword to the current chapter"
    bl_options = {'REGISTER', 'UNDO'}

    keyword: bpy.props.StringProperty(default='')


    def execute(self, context):
        if self.keyword == '':
            keyword = context.scene.lm_keywords[context.scene.lm_keyword_idx]

        context.scene.lm_chapter_naming_convention = add_keyword(context, context.scene.lm_chapter_naming_convention, keyword.name.upper())

        return {'FINISHED'}


class LM_UI_RemoveChapterKeyword(bpy.types.Operator):
    bl_idname = "scene.lm_remove_chapter_keyword"
    bl_label = "Clear Chapter keyword"
    bl_options = {'REGISTER', 'UNDO'}
    bl_description = "Remove last Chapter keyword."

    def execute(self, context):
        scn = context.scene

        scn.lm_chapter_naming_convention = remove_keyword(context, scn.lm_chapter_naming_convention)

        return {'FINISHED'}