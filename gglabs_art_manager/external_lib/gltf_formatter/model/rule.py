from abc import ABC, abstractmethod
from enum import Enum
from typing import List, Type

from gltf_formatter.model.gltf import GLTF2
from gltf_formatter.model.report import BaseLogger


class Principle(Enum):
    UNCLASSIFIED = 0
    SINGULARITY = 1
    VALIDITY = 2
    COMPLETENESS = 3
    READABILITY = 4
    CONSISTENCY = 5
    PURITY = 6


class TargetResourceType(Enum):
    ANY = "any"
    AVATAR = "avatar"
    FACE = "face"
    ANIMATION = "animation"
    PARTS = "parts"


class Rule(ABC):
    description: str = ""
    description_kr: str = ""
    in_use: bool = True
    principle: Principle = Principle.UNCLASSIFIED
    resource_type: TargetResourceType = TargetResourceType.ANY
    upstreams: "List[Type[Rule]]" = []

    @classmethod
    def name(cls) -> str:
        return cls.__name__

    @classmethod
    def poll(cls, gltf: GLTF2, logger: BaseLogger) -> bool:
        return True

    # Raises RuleApplyError on failure
    @classmethod
    @abstractmethod
    def apply(cls, gltf: GLTF2, logger: BaseLogger) -> GLTF2:
        pass
