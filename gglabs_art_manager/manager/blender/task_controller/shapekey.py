import bpy
from blender_validator import ConfigLoader
from blender_validator.utils import (
    iterate_category_mesh_objects,
    remove_prefix_from_shapekeys,
)

from gglabs_art_manager.blender import GAM_PGT_TaskControlView, TaskControlView
from gglabs_art_manager.manager.blender.property_group import GAM_PGT_Main
from gglabs_art_manager.manager.logger import logger


class GAM_PGT_ShapekeyControlPanel(GAM_PGT_TaskControlView):
    control_enabled: bpy.props.BoolProperty(
        name="Shapekey 이름 보정하기",
        description="Shapekey 이름 보정 도구를 화면에 나타냅니다.",
        default=False,
    )

    shapekey_name_prefix: bpy.props.StringProperty(
        name="삭제할 Prefix",
        description="Shapekey 이름에서 제외하고자 하는 prefix",
        default="",
    )

    result_message: bpy.props.StringProperty(
        name="Shapekey 이름 보정 결과",
        description="Shapekey 이름 보정 결과 및 에러메세지",
        default="",
    )

    @classmethod
    def reset(cls):
        cls.setattr("control_enabled", False)
        cls.setattr("shapekey_name_prefix", "")
        cls.setattr("result_message", "")


class GAM_OT_RenameShapekey(bpy.types.Operator):
    bl_idname = "gglabs_art_manager.rename_shapekey"
    bl_label = "Rename shapekeys by given conditions"
    bl_description = "Shapekey 이름을 일괄 수정합니다."
    bl_options = {"REGISTER", "UNDO"}

    def execute(self, context):
        accessor = GAM_PGT_Main
        config: str = accessor.getattr_abspath("validate_config_filepath")
        constants = ConfigLoader.load(config)

        accessor = GAM_PGT_ShapekeyControlPanel
        prefix: str = accessor.getattr_str("shapekey_name_prefix")

        if not prefix:
            return {"FINISHED"}

        modified_obj_cnt = 0
        modified_shapekey_cnt = 0

        for col_expr, _, obj in iterate_category_mesh_objects(constants.parts_categories):
            sk_report_lines = [
                f"Shapekey[{d.key}] {d.detail}"
                for details in remove_prefix_from_shapekeys(obj, prefix).values()
                for d in details
            ]

            if len(sk_report_lines) > 0:
                logger.log(f"Shapekey Fixed :: [{col_expr}] {obj.name} ({obj.data.name})")
                for line in sk_report_lines:
                    logger.log(line)
                logger.log("")

                modified_shapekey_cnt += len(sk_report_lines)
                modified_obj_cnt += 1

        if modified_obj_cnt == 0:
            message = "해당 prefix를 가진 shapekey가 없습니다!"
        else:
            message = (
                f"총 {modified_obj_cnt}건의 mesh에서 {modified_shapekey_cnt}의 shapekey들이 변경되었습니다."
                "\n자세한 변경 내용은 console log를 확인해주세요."
            )

        accessor.setattr("result_message", message)

        return {"FINISHED"}

    def invoke(self, context, event):
        return context.window_manager.invoke_confirm(self, event)


class ShapekeyControlPanel(TaskControlView):
    property_group_class = GAM_PGT_ShapekeyControlPanel
    operator_classes = [GAM_OT_RenameShapekey]

    @classmethod
    def draw_control_view(cls, layout: bpy.types.UILayout):
        params = cls.getprops()

        layout.prop(params, "shapekey_name_prefix")
        layout.operator(
            GAM_OT_RenameShapekey.bl_idname,
            icon="SYNTAX_OFF",
            text="Shapekey Prefix 제거하기",
        )

        message: str = getattr(params, "result_message")
        for line in message.split("\n"):
            if line.rstrip():
                layout.label(text=line.rstrip())
