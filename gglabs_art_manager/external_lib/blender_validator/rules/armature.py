from typing import Iterable, List, Tuple

import bpy

from blender_validator.model import BaseLogger, Rule, RuleConstants, Severity, TaskType
from blender_validator.rules.mesh import MeshObjectWithTransformValueRule
from blender_validator.rules.utils import iterate_armature_objects


class ArmatureObjectWithTransformValueRule(MeshObjectWithTransformValueRule):
    description = "Find armature objects to which any transformation is applied"
    description_kr: str = "Transform/Delta Transform 이 적용되어진 armature가 있는지 확인합니다."
    in_use = True
    severity = Severity.ERROR

    @classmethod
    def object_generator(
        cls, constants: RuleConstants, task_type: TaskType
    ) -> Iterable[Tuple[str, bpy.types.Collection, bpy.types.Object]]:
        return iterate_armature_objects()

    @classmethod
    def validate(cls, constants: RuleConstants, task_type: TaskType, logger: BaseLogger):
        return cls._validate_impl(constants, task_type, logger, is_strict=True)
