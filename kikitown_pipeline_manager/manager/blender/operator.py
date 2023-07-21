import os

import bpy
from blender_validator import BlenderValidator, ConfigLoader, TaskType
from blender_validator.exception import BlenderValidateError
from gltf_formatter import GltfFormatter, TargetResourceType

from kikitown_pipeline_manager.manager.blender.property_group import KPM_PGT_Main
from kikitown_pipeline_manager.manager.blender.utils import (
    control_visibilities_for_tasktype,
)
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

        project: str = accessor.getattr("project_type")
        if project == Project.BEERGANG.name:
            custom_rules = []
            exclude_global_rules = []
        else:
            custom_rules = []
            exclude_global_rules = []

        config: str = accessor.getattr_abspath("config_filepath")
        try:
            config_loader = ConfigLoader.load(config)
        except (ValueError, FileNotFoundError):
            message = "유효성 검사 설정 파일을 다시 확인해주세요."
            accessor.setattr("is_blender_validated", False)
            accessor.setattr("blender_validated_message", message)
            return {"FINISHED"}

        validator = BlenderValidator(
            TASK_TYPE_MAP[mode],
            config_loader,
            custom_rules=custom_rules,
            use_global_rules=True,
            exclude_global_rules=exclude_global_rules,
        )

        try:
            fix_report = validator.validate_and_fix()
        except BlenderValidateError as e:
            message = f"⚠️ {str(e)}"
            accessor.setattr("is_blender_validated", False)
        else:
            message = "✅ Blender 파일이 유효성 검사를 마쳤습니다. 이제 GLB를 생성해도 좋습니다!"
            message = f"{fix_report}\n\n{message}"
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
        config: str = accessor.getattr_abspath("config_filepath")
        constants = ConfigLoader.load(config)

        # 1. visibility control
        mode: str = accessor.getattr("task_type")

        # TODO: Make this controlled by mode and project

        control_visibilities_for_tasktype(mode, constants.shapekey_categories)

        # 2. Filepath
        output_path: str = accessor.getattr_abspath("output_dirpath")
        current_filename: str = bpy.path.basename(bpy.context.blend_data.filepath).rsplit(".", 1)[0]
        temp_filepath = os.path.join(output_path, f"temp_{current_filename}.glb")
        glb_filepath = os.path.join(output_path, f"{current_filename}.glb")

        # 8.2 Create an intermediate gltf file
        bpy.ops.export_scene.gltf(
            filepath=temp_filepath,
            check_existing=False,
            # export_format="GLTF_EMBEDDED",
            export_format="GLB",
            export_keep_originals=False,
            # Include
            # use_visible=True,
            use_renderable=True,
            use_active_scene=True,
            export_extras=True,
            # Transform
            export_yup=True,
            # Mesh
            export_apply=False,
            export_texcoords=True,
            export_normals=True,
            export_tangents=True,
            export_colors=False,
            export_attributes=True,
            use_mesh_edges=False,
            use_mesh_vertices=False,
            export_original_specular=True,  # TODO: Should Check This
            # Animation
            export_animations=False,
            # Shape keys
            export_morph=True,
            export_morph_normal=True,
            export_morph_tangent=False,
            # Skinning
            export_skins=False,
        )

        # 3. Postprocess GLB
        # 8.3 Patch the gltf file.
        # 2.2 GLTF postprocessors
        rule_formatter = GltfFormatter(
            TargetResourceType.FACE,
            strict_mode=True,
        )

        rule_formatter.format_and_save(temp_filepath, glb_filepath)
        os.remove(temp_filepath)

        self.report(
            {"INFO"},
            f"Model file created :: {glb_filepath}",
        )

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
        accessor.setattr("output_dirpath", "//")

        return {"FINISHED"}
