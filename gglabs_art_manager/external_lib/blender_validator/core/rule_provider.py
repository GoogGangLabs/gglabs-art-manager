import inspect
from types import ModuleType
from typing import Iterable, Iterator, List, Optional, Set, Union

from blender_validator.model import Rule, RuleType, TaskType
from blender_validator.rules import animation, armature, collection, mesh, shapekey


def _is_rule_type_class(cls) -> bool:
    return inspect.isclass(cls) and (not inspect.isabstract(cls)) and issubclass(cls, Rule)


def _load_rules_from_module(*modules: ModuleType) -> Set[RuleType]:
    return {
        cls
        for module in modules
        for _, cls in inspect.getmembers(module)
        if _is_rule_type_class(cls)
    }


_default_rules = {
    TaskType.FACE_MODELING: _load_rules_from_module(collection, mesh),
    TaskType.FACE_RIGGING: _load_rules_from_module(collection, mesh, shapekey),
    TaskType.BODY_MODELING: _load_rules_from_module(collection, mesh),
    TaskType.BODY_RIGGING: _load_rules_from_module(collection, mesh, shapekey),
    TaskType.ANIMATING: _load_rules_from_module(animation),
    TaskType.MASTERING: _load_rules_from_module(collection, mesh, shapekey, armature),
}

class RuleProvider:
    def __init__(
        self,
        task_type: TaskType,
        custom_rules: Optional[Union[ModuleType, Iterable[RuleType], Iterable[ModuleType]]] = None,
        contain_default_rules: bool = True,
        exclude_rules: Optional[Iterable[RuleType]] = None,
    ):
        self.rules: List[RuleType] = []
        self.task_type: TaskType = task_type

        target_rules: List[RuleType] = []
        if contain_default_rules:
            target_rules.extend(_default_rules[task_type])
            target_rules = [rule for rule in target_rules if rule not in (exclude_rules or [])]

        if isinstance(custom_rules, ModuleType):
            target_rules.extend(_load_rules_from_module(custom_rules))
        elif isinstance(custom_rules, Iterable):
            for rule in custom_rules:
                if isinstance(rule, ModuleType):
                    target_rules.extend(_load_rules_from_module(rule))
                elif _is_rule_type_class(rule):
                    target_rules.append(rule)

        target_rules = [
            rule
            for rule in target_rules
            if (TaskType.ANY in rule.task_types) or (task_type in rule.task_types)
        ]

        self.load_rules(target_rules)

    @property
    def name(self) -> str:
        return self.task_type.value

    def load_rules(self, rules: List[RuleType]) -> "RuleProvider":
        self.rules = [rule for rule in rules if rule.in_use]

        return self

    def __iter__(self) -> Iterator[Rule]:
        for rule in self.rules:
            yield rule
