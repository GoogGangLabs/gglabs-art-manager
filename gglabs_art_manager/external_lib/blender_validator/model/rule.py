from abc import ABC, abstractmethod
from dataclasses import dataclass
from enum import Enum
from typing import List, Set

from blender_validator.model.report import BaseLogger
from blender_validator.model.task import TaskType


# Reusing the code system of glTF-Validator for the sake of consistency.
# https://github.com/KhronosGroup/glTF-Validator/blob/main/lib/src/errors.dart#L23
class Severity(Enum):
    ERROR = 0
    WARNING = 1
    INFORMATION = 2
    HINT = 3


@dataclass
class RuleConstants:
    shapekeys: List[str]
    shapekey_categories: List[str]
    mandatory_head_categories: List[str]
    mandatory_parts_categories: List[str]
    parts_categories: List[str]


class Rule(ABC):
    description: str = ""
    description_kr: str = ""
    in_use: bool = True
    task_types: Set[TaskType] = {TaskType.ANY}
    severity: Severity = Severity.INFORMATION

    @classmethod
    def name(cls) -> str:
        return cls.__name__

    # Raises BlenderValidateError on failure
    @classmethod
    @abstractmethod
    def validate(cls, constants: RuleConstants, task_type: TaskType, logger: BaseLogger) -> bool:
        return True

    @classmethod
    def fix(cls, constants: RuleConstants, task_type: TaskType, logger: BaseLogger) -> bool:
        return True
