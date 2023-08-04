from typing import List, Optional

import bpy

from blender_validator.exception import BlenderValidateError
from blender_validator.model import BaseLogger, Rule, RuleConstants, Severity, TaskType
from blender_validator.rules.utils import arrange_shapekeys, iterate_category_mesh_objects


class ShapeKeyArrangementRule(Rule):
    description = "Check if all face meshes contains complete shapekey list"
    description_kr: str = "shapekey용 mesh가 정해진 shapekey 목록을 전부 포함하는지 여부를 체크합니다."
    in_use = True
    severity = Severity.ERROR

    @classmethod
    def _check_mesh_has_complete_shapekeys(
        cls,
        col_expr: str,
        obj: bpy.types.Object,
        shapekey_names: List[str],
        logger: Optional[BaseLogger] = None,
    ) -> bool:
        mesh: bpy.types.Mesh = obj.data
        shape_keys = mesh.shape_keys

        correct_shapekey_names = ["Basis"] + shapekey_names

        # 1. Invalid when no shapekeys at all
        if not shape_keys:
            if logger is not None:
                logger.log(f"[{col_expr}] {obj.name} ({mesh.name}) has no shapekeys at all")
            return False

        # 2. Invalid when the number of shapekeys is not the same as expected
        if len(shape_keys.key_blocks) != len(correct_shapekey_names):
            if logger is not None:
                logger.log(f"[{col_expr}] {obj.name} ({mesh.name}) has not enough shapekeys")
            return False

        # 3. Invalid when names or indices of shapekey list is not the same as expected
        actural_shapekey_names = [sk.name for sk in mesh.shape_keys.key_blocks]
        is_match = all(
            correct_shapekey_names[idx] == actural_shapekey_names[idx]
            for idx in range(len(correct_shapekey_names))
        )
        if not is_match:
            if logger is not None:
                logger.log(
                    f"[{col_expr}] {obj.name} ({mesh.name}) shapekey list differs from"
                    " what it should be"
                )

            return False

        return True

    @classmethod
    def validate(cls, constants: RuleConstants, task_type: TaskType, logger: BaseLogger) -> bool:
        for col_expr, category_col, obj in iterate_category_mesh_objects(
            constants.shapekey_categories
        ):
            # For Beergang Type Category
            if category_col.name.lower() == "type" and not obj.name.lower().startswith("head_"):
                continue

            if not cls._check_mesh_has_complete_shapekeys(
                col_expr, obj, constants.shapekeys, logger
            ):
                return False

        # 9. All shapekeys are properly arranged.
        return True

    @classmethod
    def fix(cls, constants: RuleConstants, task_type: TaskType, logger: BaseLogger) -> bool:
        for col_expr, category_col, obj in iterate_category_mesh_objects(
            constants.shapekey_categories
        ):
            # Handling Beergang Type Category
            if category_col.name.lower() == "type" and not obj.name.lower().startswith("head_"):
                continue

            # Skip the procedure for the mesh with proper shapekey list
            if cls._check_mesh_has_complete_shapekeys(col_expr, obj, constants.shapekeys):
                continue

            sk_report_lines = [
                f"Shapekey[{d.key}] {d.detail}"
                for details in arrange_shapekeys(obj, constants.shapekeys).values()
                for d in details
            ]

            if len(sk_report_lines) > 0:
                logger.log(f"Shapekey Fixed :: [{col_expr}] {obj.name} ({obj.data.name})")
                for line in sk_report_lines:
                    logger.log(line)
                logger.log("")

        return True


class WrongShapeKeyedMeshRule(Rule):
    description = "Verify that the shape key is present in the mesh that is not allowed."
    description_kr: str = "shapekey가 없어야 할 mesh에 shapekey가 있는 경우를 확인합니다."
    in_use = True
    severity = Severity.ERROR

    @classmethod
    def validate(cls, constants: RuleConstants, task_type: TaskType, logger: BaseLogger) -> bool:
        non_shapekey_categories = [
            c for c in constants.parts_categories if not c in constants.shapekey_categories
        ]

        for col_expr, _, obj in iterate_category_mesh_objects(non_shapekey_categories):
            mesh: bpy.types.Mesh = obj.data
            if mesh.shape_keys is not None and len(mesh.shape_keys.key_blocks) > 0:
                raise BlenderValidateError(
                    (
                        f"{col_expr} 파츠의 mesh는 shapekey가 허용되지 않습니다.\n{col_expr}의"
                        f" {obj.name}({mesh.name})에 지정되어져 있는 shapekey를 확인하신 후 정리해주세요."
                    ),
                )

        return True


class ShapeKeyAnimationDataCleanupRule(Rule):
    description = "Clean up unintended animation data in shapekeys in meshes if exists."
    description_kr: str = "Facial Rigging 과정에서 shapekey에 애니메이션 데이터가 있는 경우 삭제합니다."
    in_use = True
    severity = Severity.ERROR

    @classmethod
    def validate(cls, constants: RuleConstants, task_type: TaskType, logger: BaseLogger) -> bool:
        # This should be undone when the task is to build animations.
        if task_type in [TaskType.ANIMATING, TaskType.MASTERING]:
            return True

        for col_expr, _, obj in iterate_category_mesh_objects(constants.parts_categories):
            mesh: bpy.types.Mesh = obj.data
            if mesh.shape_keys is not None:
                if mesh.shape_keys.animation_data is not None:
                    logger.log(
                        f"[{col_expr}] {obj.name} ({mesh.name}) has unnecessary animation data"
                    )
                    return False

        return True

    @classmethod
    def fix(cls, constants: RuleConstants, task_type: TaskType, logger: BaseLogger) -> bool:
        # This should be undone when the task is to build animations.
        if task_type in [TaskType.ANIMATING, TaskType.MASTERING]:
            return True

        # 0. Get target mesh
        for col_expr, _, obj in iterate_category_mesh_objects(constants.parts_categories):
            mesh: bpy.types.Mesh = obj.data
            if mesh.shape_keys is not None:
                anim_data = mesh.shape_keys.animation_data
                if anim_data is not None:
                    anim_name = anim_data.action.name

                    shapekey_channels = set()
                    for fcurve in anim_data.action.fcurves:
                        # key_blocks["LOOKRIGHT"].value
                        shapekey_channel_expr = fcurve.data_path
                        if shapekey_channel_expr.startswith(
                            'key_blocks["'
                        ) and shapekey_channel_expr.endswith('"].value'):
                            shapekey_channels.add(shapekey_channel_expr.split('"')[1])

                    shapekey_channels_expr = ", ".join(shapekey_channels)
                    logger.log(
                        f"[{col_expr}] {obj.name} ({obj.data.name})의 shapekey animation"
                        f" 데이터를 삭제했습니다.\n animation track: {anim_name}\n shapekey 채널:"
                        f" ({shapekey_channels_expr})"
                    )
                    mesh.shape_keys.animation_data_clear()

        return True
