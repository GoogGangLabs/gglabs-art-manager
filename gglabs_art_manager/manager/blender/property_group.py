import bpy
from blender_validator import BlenderValidator, ConfigLoader, TaskType

from gglabs_art_manager.blender import GAM_PGT_Base
from gglabs_art_manager.manager.logger import logger
from gglabs_art_manager.manager.model import Project

__all__ = ["GAM_PGT_Main"]


class GAM_PGT_Main(GAM_PGT_Base):
    def check_validity_on_validate_config(self, context):
        if self.validate_config_filepath == "":
            self.validate_config_loaded_message = ""
            self.is_validate_config_loaded = False
            return

        fpath = bpy.path.abspath(self.validate_config_filepath)
        try:
            rule_constants = ConfigLoader.load(fpath)
        except ValueError as e:
            self.validate_config_loaded_message = str(e)
            self.is_validate_config_loaded = False
        else:
            self.validate_config_loaded_message = "유효성 검사 설정 파일이 정상적으로 로드되어졌습니다!"
            self.is_validate_config_loaded = True

        validator = BlenderValidator(
            TaskType.from_str(self.task_type),
            rule_constants,
            use_default_rules=True,
            exclude_rules=[],
        )

        logger.log("RuleProvider :: Loaded Rule List")
        for rule in validator.rules:
            logger.log(f"{rule.name()}: {rule.description_kr}")

    project_type: bpy.props.EnumProperty(
        name="",
        description="작업 프로젝트를 지정합니다.",
        items=[
            (
                Project.BEERGANG.name,
                Project.BEERGANG.value,
                Project.BEERGANG.value,
            ),
            (
                Project.KIKITOWN.name,
                Project.KIKITOWN.value,
                Project.KIKITOWN.value,
            ),
        ],
        default=Project.BEERGANG.name,
    )

    task_type: bpy.props.EnumProperty(
        name="",
        description="현재 blender 파일에 해당되는 작업 단계를 지정합니다.",
        items=[
            (
                TaskType.FACE_MODELING.name,
                TaskType.FACE_MODELING.value,
                TaskType.FACE_MODELING.value,
            ),
            (TaskType.FACE_RIGGING.name, TaskType.FACE_RIGGING.value, TaskType.FACE_RIGGING.value),
            (
                TaskType.BODY_MODELING.name,
                TaskType.BODY_MODELING.value,
                TaskType.BODY_MODELING.value,
            ),
            (TaskType.BODY_RIGGING.name, TaskType.BODY_RIGGING.value, TaskType.BODY_RIGGING.value),
            (TaskType.ANIMATING.name, TaskType.ANIMATING.value, TaskType.ANIMATING.value),
            (TaskType.MASTERING.name, TaskType.MASTERING.value, TaskType.MASTERING.value),
        ],
        default=TaskType.FACE_RIGGING.name,
    )

    validate_config_filepath: bpy.props.StringProperty(
        name="Blender 유효성 검사 설정 파일",
        description="Blender 유효성 검사 설정 파일을 입력합니다. (configurations.yaml)",
        maxlen=1024,
        update=check_validity_on_validate_config,
        subtype="FILE_PATH",
    )

    is_validate_config_loaded: bpy.props.BoolProperty(
        name="Blender 유효성 검사 파일 로딩 완료",
        description="Blender 유효성 검사 파일이 로딩이 정상 완료되었는지 여부",
        default=False,
    )

    validate_config_loaded_message: bpy.props.StringProperty(
        name="Blender 유효성 검사 파일 로딩 상태",
        description="Blender 유효성 검사 파일의 로딩 상태 및 에러메세지",
        default="",
    )

    is_blender_validated: bpy.props.BoolProperty(
        name="blender 파일 유효성 여부",
        description="blender 파일이 유효한지에 대한 여부",
        default=False,
    )

    blender_validated_message: bpy.props.StringProperty(
        name="",
        description="blender 파일 유효성 검사 메세지",
        default="",
    )

    output_dirpath: bpy.props.StringProperty(
        name="GLB 파일 생성 경로",
        description="GLB 파일을 생성할 경로를 입력합니다.",
        default="//",
        maxlen=1024,
        subtype="DIR_PATH",
    )
