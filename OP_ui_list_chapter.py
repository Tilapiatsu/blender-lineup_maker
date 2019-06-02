import bpy


class LM_UI_UseKeywordAsChapter(bpy.types.Operator):
    bl_idname = "scene.lm_use_keyword_as_chapter"
    bl_label = "Use selected keyword as chapter"
    bl_options = {'REGISTER', 'UNDO'}
    bl_description = "Use selected keyword as chapter"

    def check(self, context):
        return True

    @classmethod
    def poll(cls, context):
        return context.scene.lm_keywords


    def execute(self, context):
        context.scene.lm_chapter_name = context.scene.lm_keywords[context.scene.lm_keyword_idx].name

        return {'FINISHED'}


class LM_UI_ClearChapterKeyword(bpy.types.Operator):
    bl_idname = "scene.lm_clear_chapter_keyword"
    bl_label = "Clear Chapter keyword"
    bl_options = {'REGISTER', 'UNDO'}
    bl_description = "Clear Chapter keyword."

    @classmethod
    def poll(cls, context):
        return context.scene.lm_chapter_name

    def execute(self, context):
        context.scene.lm_chapter_name = ''
        return {'FINISHED'}
