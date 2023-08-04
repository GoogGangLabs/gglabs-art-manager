import os

import bpy
from blender_validator import BlenderValidator, ConfigLoader, TaskType
from blender_validator.exception import BlenderValidateError
from gltf_formatter import GltfFormatter
from gltf_formatter.exception import RuleApplyError

from gglabs_art_manager.blender.utils import load_bpy_context, save_bpy_context
from gglabs_art_manager.manager.blender.property_group import GAM_PGT_Main
from gglabs_art_manager.manager.blender.utils import control_visibilities_for_tasktype
from gglabs_art_manager.manager.logger import logger
from gglabs_art_manager.manager.model import (
    Project,
    TaskTypeGltfOptions,
    TaskTypeToTargetResourceType,
)

TASK_TYPE_MAP = {task.name: task for task in TaskType}


class GAM_OT_ValidateBlender(bpy.types.Operator):
    bl_idname = "gglabs_art_manager.validate_blender"
    bl_label = "Run validation check on the blender file"
    bl_description = "Blender 파일의 유효성 검사를 진행합니다."
    bl_options = {"REGISTER", "UNDO"}

    def execute(self, context):
        accessor = GAM_PGT_Main

        project: str = accessor.getattr("project_type")
        mode: str = accessor.getattr("task_type")

        config: str = accessor.getattr_abspath("validate_config_filepath")

        try:
            rule_constants = ConfigLoader.load(config)
        except (ValueError, FileNotFoundError):
            message = "유효성 검사 설정 파일을 다시 확인해주세요."
            accessor.setattr("is_blender_validated", False)
            accessor.setattr("blender_validated_message", message)
            return {"FINISHED"}

        validator = BlenderValidator(
            TASK_TYPE_MAP[mode],
            rule_constants,
            use_default_rules=True,
            custom_rules=[],
            exclude_rules=[],
            logger=logger,
        )

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


class GAM_OT_ExportGLB(bpy.types.Operator):
    bl_idname = "gglabs_art_manager.export_glb"
    bl_label = "Export GLB file in the regularized format"
    bl_description = "GLB 파일을 export 합니다."
    bl_options = {"REGISTER", "UNDO"}

    def execute(self, context):
        accessor = GAM_PGT_Main
        config: str = accessor.getattr_abspath("validate_config_filepath")
        constants = ConfigLoader.load(config)

        # 1. visibility control
        task_type: str = accessor.getattr("task_type")

        # TODO: Make this controlled by mode and project
        # context = save_bpy_context()
        control_visibilities_for_tasktype(task_type, constants.shapekey_categories)
        # load_bpy_context(context)

        # 2. Filepath
        output_path: str = accessor.getattr_abspath("output_dirpath")
        current_filename: str = bpy.path.basename(bpy.context.blend_data.filepath).rsplit(".", 1)[0]
        temp_filepath = os.path.join(output_path, f"temp_{current_filename}.glb")
        glb_filepath = os.path.join(output_path, f"{current_filename}.glb")

        # 3. Create an intermediate gltf file
        bpy.ops.export_scene.gltf(
            filepath=temp_filepath, export_format="GLB", **TaskTypeGltfOptions[task_type]
        )

        # 4. Postprocess GLB
        rule_formatter = GltfFormatter(
            TaskTypeToTargetResourceType[task_type],
            strict_mode=True,
        )
        try:
            rule_formatter.format_and_save(temp_filepath, glb_filepath)
        except RuleApplyError as e:
            logger.log(e)
            return {"CANCELLED"}

        # os.remove(temp_filepath)

        self.report(
            {"INFO"},
            f"Model file created :: {glb_filepath}",
        )

        return {"FINISHED"}

    def invoke(self, context, event):
        return context.window_manager.invoke_confirm(self, event)


class GAM_OT_Reset(bpy.types.Operator):
    bl_idname = "gglabs_art_manager.reset"
    bl_label = "Reset Input Parameters of Kikitown Pipeline Manager"
    bl_description = "입력값 초기화"
    bl_options = {"REGISTER", "UNDO"}

    def execute(self, context):
        accessor = GAM_PGT_Main
        accessor.setattr("project_type", Project.BEERGANG.name)
        accessor.setattr("task_type", TaskType.FACE_RIGGING.name)
        accessor.setattr("validate_config_filepath", "")
        accessor.setattr("is_validate_config_loaded", False)
        accessor.setattr("validate_config_loaded_message", "")
        accessor.setattr("is_blender_validated", False)
        accessor.setattr("blender_validated_message", "")
        accessor.setattr("output_dirpath", "//")

        return {"FINISHED"}
