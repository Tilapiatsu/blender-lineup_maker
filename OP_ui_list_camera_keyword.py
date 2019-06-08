import bpy

def get_camera_keywords(context):
    idx = context.scene.lm_camera_idx
    cameras = context.scene.lm_cameras

    active = cameras[idx] if cameras else None

    return idx, cameras, active

class LM_UI_MoveCameraKeyword(bpy.types.Operator):
    bl_idname = "scene.lm_move_camera_keyword"
    bl_label = "Move Keyword"
    bl_options = {'REGISTER', 'UNDO'}
    bl_description = "Move Camera keyword Name up or down.\nThis controls the position in the Menu."

    direction: bpy.props.EnumProperty(items=[("UP", "Up", ""), ("DOWN", "Down", "")])

    def execute(self, context):
        idx, camera, _ = get_camera_keywords(context)

        if self.direction == "UP":
            nextidx = max(idx - 1, 0)
        elif self.direction == "DOWN":
            nextidx = min(idx + 1, len(camera) - 1)

        camera.move(idx, nextidx)
        context.scene.lm_camera_idx = nextidx

        return {'FINISHED'}


class LM_UI_ClearCameraKeyword(bpy.types.Operator):
    bl_idname = "scene.lm_clear_camera_keywords"
    bl_label = "Clear All Camera keyword"
    bl_options = {'REGISTER', 'UNDO'}
    bl_description = "Clear All Texture keyword Names."

    @classmethod
    def poll(cls, context):
        return context.scene.lm_cameras

    def execute(self, context):
        context.scene.lm_cameras.clear()

        return {'FINISHED'}


class LM_UI_RemoveCameraKeyword(bpy.types.Operator):
    bl_idname = "scene.lm_remove_camera_keyword"
    bl_label = "Remove Camera Keyword Name"
    bl_options = {'REGISTER', 'UNDO'}
    bl_description = "Remove selected camera keyword Name."

    @classmethod
    def poll(cls, context):
        return context.scene.lm_cameras

    def execute(self, context):
        idx, camera, _ = get_camera_keywords(context)

        camera.remove(idx)

        context.scene.lm_camera_idx = min(idx, len(context.scene.lm_cameras) - 1)

        return {'FINISHED'}
