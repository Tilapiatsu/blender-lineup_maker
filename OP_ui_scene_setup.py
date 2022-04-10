import bpy

class LM_UI_SetLineupScene(bpy.types.Operator):
    bl_idname = "scene.lm_set_as_lineup_scene"
    bl_label = "Set as lineup scene"
    bl_options = {'REGISTER', 'UNDO'}
    bl_description = "Set current scene to Lineup."

    value : bpy.props.BoolProperty()

    def execute(self, context):
        context.scene.lm_is_lineup_scene = self.value
        return {'FINISHED'}

    
class LM_UI_SetCatalogScene(bpy.types.Operator):
    bl_idname = "scene.lm_set_as_catalog_scene"
    bl_label = "Set as catalog scene"
    bl_options = {'REGISTER', 'UNDO'}
    bl_description = "Set current scene to Catalog."

    value : bpy.props.BoolProperty()

    def execute(self, context):
        context.scene.lm_is_catalog_scene = self.value
        return {'FINISHED'}