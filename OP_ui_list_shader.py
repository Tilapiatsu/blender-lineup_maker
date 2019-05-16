import bpy

def get_shaders(context):
    idx = context.scene.lm_shader_idx
    shaders = context.scene.lm_shaders
    channels = context.scene.lm_channels
    textures = context.scene.lm_texture_channels

    active = shaders[idx] if shaders else None

    return idx, shaders, channels, textures, active

class LM_UI_MoveShader(bpy.types.Operator):
    bl_idname = "scene.lm_move_shader"
    bl_label = "Move shader"
    bl_options = {'REGISTER', 'UNDO'}
    bl_description = "Move Shader Name up or down.\nThis controls the position in the Menu."

    direction: bpy.props.EnumProperty(items=[("UP", "Up", ""), ("DOWN", "Down", "")])

    def execute(self, context):
        idx, shader, _, _, _ = get_shaders(context)

        if self.direction == "UP":
            nextidx = max(idx - 1, 0)
        elif self.direction == "DOWN":
            nextidx = min(idx + 1, len(shader) - 1)

        shader.move(idx, nextidx)
        context.scene.lm_shader_idx = nextidx

        return {'FINISHED'}



class LM_UI_RenameShader(bpy.types.Operator):
    bl_idname = "scene.lm_rename_shader"
    bl_label = "Rename Texture shader"
    bl_options = {'REGISTER', 'UNDO'}
    bl_description = "Rename the selected shader Name"

    new_shader_name: bpy.props.StringProperty(name="New Name")

    def check(self, context):
        return True

    @classmethod
    def poll(cls, context):
        return context.scene.lm_shaders

    def draw(self, context):
        layout = self.layout

        column = layout.column()

        # row = column.split(percentage=0.31)
        # row.label("Old Name")
        # row.label(self.active.name)

        column.prop(self, "new_shader_name")

    def invoke(self, context, event):
        _, _, _, _, self.active = get_shaders(context)

        self.new_shader_name = self.active.name

        wm = context.window_manager
        return wm.invoke_props_dialog(self)

    def execute(self, context):
        if self.new_shader_name:
            _, _, channels, textures , _ = get_shaders(context)

            for t in textures:
                if t.shader == self.active.name:
                    t.shader = self.new_shader_name
            
            for c in channels:
                if c.shader == self.active.name:
                    c.shader = self.new_shader_name

            self.active.name = self.new_shader_name

        return {'FINISHED'}


class LM_UI_ClearShader(bpy.types.Operator):
    bl_idname = "scene.lm_clear_shaders"
    bl_label = "Clear All Texture shader"
    bl_options = {'REGISTER', 'UNDO'}
    bl_description = "Clear All Texture shader Names."

    @classmethod
    def poll(cls, context):
        return context.scene.lm_shaders

    def execute(self, context):
        context.scene.lm_shaders.clear()

        return {'FINISHED'}


class LM_UI_RemoveShader(bpy.types.Operator):
    bl_idname = "scene.lm_remove_shader"
    bl_label = "Remove Material Name"
    bl_options = {'REGISTER', 'UNDO'}
    bl_description = "Remove selected Texture shader Name."

    @classmethod
    def poll(cls, context):
        return context.scene.lm_shaders

    def execute(self, context):
        idx, shader, _ = get_shaders(context)

        shader.remove(idx)

        context.scene.lm_shader_idx = min(idx, len(context.scene.lm_shaders) - 1)

        return {'FINISHED'}
