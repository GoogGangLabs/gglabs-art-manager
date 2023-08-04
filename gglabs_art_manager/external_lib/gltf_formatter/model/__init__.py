from typing import Type

from gltf_formatter.model.gltf import GLTF2
from gltf_formatter.model.report import BaseLogger, StdoutLogger
from gltf_formatter.model.rule import Principle, Rule, TargetResourceType

RuleType = Type[Rule]

__all__ = ["Rule", "Principle", "TargetResourceType", "RuleType", "GLTF2", "BaseLogger", "StdoutLogger"]
