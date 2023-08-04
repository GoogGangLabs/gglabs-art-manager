from types import ModuleType
from typing import Iterable, Optional, Union

from gltf_formatter.core.rule_provider import RuleProvider
from gltf_formatter.exception import RuleApplyError
from gltf_formatter.model import GLTF2, BaseLogger, RuleType, TargetResourceType


class GltfFormatter:
    def __init__(
        self,
        resource_type: TargetResourceType,
        custom_rules: Optional[Union[ModuleType, Iterable[RuleType], Iterable[ModuleType]]] = None,
        use_default_rules: bool = True,
        strict_mode: bool = False,
        logger: Optional[BaseLogger] = None,
    ):
        self.rules = RuleProvider(
            resource_type,
            custom_rules=custom_rules,
            contain_default_rules=use_default_rules,
        )
        self.strict_mode = strict_mode
        self.logger = logger or BaseLogger()

    def format(self, gltf: Union[GLTF2, str]) -> GLTF2:
        if isinstance(gltf, GLTF2):
            pass
        elif isinstance(gltf, str):
            gltf = GLTF2.load(gltf)

        for rule in self.rules:
            if self.strict_mode and not rule.poll(gltf, self.logger):
                message = f"--- [{rule.name()}] poll has failed ---\n"
                raise RuleApplyError(message)

            gltf = rule.apply(gltf, self.logger)

        return gltf

    def format_and_save(self, gltf: Union[GLTF2, str], output_file_path: str) -> GLTF2:
        gltf = self.format(gltf)
        gltf.save(output_file_path)

        return gltf
