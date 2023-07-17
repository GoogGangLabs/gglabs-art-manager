import bpy
from blender_validator import BlenderValidator, ConfigLoader, TaskType
from blender_validator.exception import BlenderValidateError

from kikitown_pipeline_manager.manager.blender.property_group import KPM_PGT_Main
from kikitown_pipeline_manager.manager.model import Project

TASK_TYPE_MAP = {task.name: task for task in TaskType}


class KPM_OT_ValidateBlender(bpy.types.Operator):
    bl_idname = "kikitown_pipeline_manager.validate_blender"
    bl_label = "Run validation check on the blender file"
    bl_description = "Blender 파일의 유효성 검사를 진행합니다."
    bl_options = {"REGISTER", "UNDO"}

    def execute(self, context):
        accessor = KPM_PGT_Main
        mode: str = accessor.getattr("task_type")

        config: str = accessor.getattr_abspath("config_filepath")
        validator = BlenderValidator(TASK_TYPE_MAP[mode], ConfigLoader.load(config))

        try:
            validator.validate_and_fix()
        except BlenderValidateError as e:
            message = f"⚠️ {str(e)}"
            accessor.setattr("is_blender_validated", False)
        else:
            message = "✅ Blender 파일이 유효성 검사를 마쳤습니다. 이제 GLB를 생성해도 좋습니다!"
            accessor.setattr("is_blender_validated", True)

        accessor.setattr("blender_validated_message", message)

        return {"FINISHED"}

    def invoke(self, context, event):
        return context.window_manager.invoke_confirm(self, event)


class KPM_OT_ExportGLB(bpy.types.Operator):
    bl_idname = "kikitown_pipeline_manager.export_glb"
    bl_label = "Export GLB file in the regularized format"
    bl_description = "GLB 파일을 export 합니다."
    bl_options = {"REGISTER", "UNDO"}

    def execute(self, context):
        accessor = KPM_PGT_Main
        mode: str = accessor.getattr("task_type")

        if mode == TaskType.FACE_RIGGING.name:
            accessor.setattr("blender_validated_message", "YES")

        return {"FINISHED"}

    def invoke(self, context, event):
        return context.window_manager.invoke_confirm(self, event)


class KPM_OT_Reset(bpy.types.Operator):
    bl_idname = "kikitown_pipeline_manager.reset"
    bl_label = "Reset Input Parameters of Kikitown Pipeline Manager"
    bl_description = "입력값 초기화"
    bl_options = {"REGISTER", "UNDO"}

    def execute(self, context):
        accessor = KPM_PGT_Main
        accessor.setattr("project_type", Project.BEERGANG.name)
        accessor.setattr("task_type", TaskType.FACE_RIGGING.name)
        accessor.setattr("config_filepath", "")
        accessor.setattr("is_config_loaded", False)
        accessor.setattr("config_loaded_message", "")
        accessor.setattr("is_blender_validated", False)
        accessor.setattr("blender_validated_message", "")

        return {"FINISHED"}
