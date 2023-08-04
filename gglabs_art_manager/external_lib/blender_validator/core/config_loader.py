from blender_validator.external_lib.poyo import PoyoException, parse_string
from blender_validator.model import RuleConstants

CONFIG_KEYS = [
    "shapekeys",
    "shapekey_categories",
    "mandatory_head_categories",
    "mandatory_parts_categories",
    "parts_categories",
]


class ConfigLoader:
    @classmethod
    def load(cls, fpath: str) -> RuleConstants:
        with open(fpath, encoding="utf-8") as fp:
            try:
                config = parse_string(fp.read())
            except FileNotFoundError as e:
                message = f"파일을 찾을 수 없습니다. :: {str(e)}"
                raise ValueError(message) from e
            except PoyoException as e:
                message = f"정상적인 Yaml 파일이 아닙니다. :: {str(e)}"
                raise ValueError(message) from e

            for configkey in CONFIG_KEYS:
                if configkey not in config:
                    raise ValueError(f"[{configkey}] 설정에 대한 값이 빠져있습니다.")

            if "version" in config:
                del config["version"]

            return RuleConstants(**config)
