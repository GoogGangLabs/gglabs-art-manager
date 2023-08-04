import inspect
from types import ModuleType
from typing import Dict, Iterable, Iterator, List, Optional, Set, Union

from gltf_formatter.exception import RuleValidateError
from gltf_formatter.model import Rule, RuleType, TargetResourceType
from gltf_formatter.rules import animation, avatar, common, face


def _is_rule_type_class(cls) -> bool:
    return inspect.isclass(cls) and (not inspect.isabstract(cls)) and issubclass(cls, Rule)


def _load_rules_from_module(module: ModuleType) -> List[RuleType]:
    return [cls for _, cls in inspect.getmembers(module) if _is_rule_type_class(cls)]


_default_rules = {
    TargetResourceType.ANY: _load_rules_from_module(common),
    TargetResourceType.AVATAR: _load_rules_from_module(avatar),
    TargetResourceType.ANIMATION: _load_rules_from_module(animation),
    TargetResourceType.FACE: _load_rules_from_module(face),
}


class RuleProvider:
    def __init__(
        self,
        resource_type: TargetResourceType,
        custom_rules: Optional[Union[ModuleType, Iterable[RuleType], Iterable[ModuleType]]] = None,
        contain_default_rules: bool = True,
    ):
        self.rules: List[RuleType] = []
        self.resource_type: TargetResourceType = resource_type

        target_rules: List[RuleType] = []
        if contain_default_rules:
            target_rules = list(_default_rules[TargetResourceType.ANY])
            if resource_type != TargetResourceType.ANY:
                target_rules.extend(_default_rules[resource_type])

        if isinstance(custom_rules, ModuleType):
            target_rules.extend(_load_rules_from_module(custom_rules))
        elif isinstance(custom_rules, Iterable):
            for rule in custom_rules:
                if isinstance(rule, ModuleType):
                    target_rules.extend(_load_rules_from_module(rule))
                elif _is_rule_type_class(rule):
                    target_rules.append(rule)

        self.load_rules(target_rules)

    @property
    def name(self) -> str:
        return self.resource_type.value

    def validate_no_cycle(self) -> bool:
        def dfs(rule_name: Rule, visited: Set[str], visiting: Set[str]):
            visiting.add(rule_name)
            for upstream in upstream_dict.get(rule, []):
                if upstream in visiting:
                    cycle_expr = " -> ".join(list(visiting) + [upstream])
                    raise RuleValidateError(f"Cycle detected :: {cycle_expr}")
                if upstream not in visited:
                    dfs(upstream, visited, visiting)
            visiting.remove(rule_name)
            visited.add(rule_name)

        visited: Set[str] = set()
        visiting: Set[str] = set()
        upstream_dict: Dict[str, Rule] = {rule.name(): rule.upstreams for rule in self.rules}

        for rule in self.rules:
            rule_name = rule.name()
            if rule_name not in visited:
                dfs(rule_name, visited, visiting)

        return True

    def validate_no_danglings(self) -> bool:
        upstream_dict = {rule.name(): rule.upstreams for rule in self.rules}

        # Check for dangling rules
        all_upstreams = set(
            upstream.name()
            for upstream_list in upstream_dict.values()
            for upstream in upstream_list
        )
        dangling_rules = all_upstreams - set(upstream_dict.keys())

        if dangling_rules:
            dangling_rules_expr = ", ".join(dangling_rules)
            raise RuleValidateError(f"Dangling upstreams found :: {dangling_rules_expr}")

        return True

    def validate_resource_type(self) -> bool:
        wrong_resource_type_rules = [
            rule.name()
            for rule in self.rules
            if rule.resource_type not in [self.resource_type, TargetResourceType.ANY]
        ]

        if wrong_resource_type_rules:
            wrong_resource_type_rules_expr = ", ".join(wrong_resource_type_rules)
            raise RuleValidateError(
                f"Wrong resource type package :: {wrong_resource_type_rules_expr}"
            )

        return True

    def validate(self) -> bool:
        ret = True

        ret &= self.validate_no_cycle()
        ret &= self.validate_no_danglings()
        ret &= self.validate_resource_type()

        return ret

    def arrange(self) -> bool:
        name_to_rule = {rule.name(): rule for rule in self.rules}

        # Create a dictionary to store the upstream rules for each rule
        upstream_dict = {rule.name(): rule.upstreams for rule in self.rules}
        rule_names: List[RuleType] = []

        # Create a set to track the visited rules during depth-first search
        visited: Set[str] = set()

        def arrange_rules(rule_name: str):
            if rule_name not in visited:
                visited.add(rule_name)
                for upstream in upstream_dict.get(rule_name, []):
                    arrange_rules(upstream.name())
                rule_names.append(rule_name)

        for rule_name in upstream_dict.keys():
            arrange_rules(rule_name)

        self.rules = [name_to_rule[r] for r in rule_names]

        return True

    def check_arranged(self) -> bool:
        order_idx = {rule.name(): idx for idx, rule in enumerate(self.rules)}

        for rule in self.rules:
            for upstream in rule.upstreams:
                if order_idx[upstream.name()] > order_idx[rule.name()]:
                    return False

        return True

    def load_rules(self, rules: List[RuleType]) -> "RuleProvider":
        self.rules = [rule for rule in rules if rule.in_use]
        self.validate()
        self.arrange()

        return self

    def __iter__(self) -> Iterator[Rule]:
        for rule in self.rules:
            yield rule
