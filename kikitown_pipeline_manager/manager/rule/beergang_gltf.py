from gltf_formatter.exception import RuleApplyError
from gltf_formatter.model import Principle, Rule, TargetResourceType
from gltf_formatter.rules.common import ReplaceMeshNamesWithColNamesRule
from pygltflib import GLTF2


class ReplaceBeergangNameWithStandardNameRule(Rule):
    PARTS_NAME_MAP = {
        "Eyebrow": "Head_Brows",
        "Eyes": "Head_Eyes",
        "Teeth": "Head_Teeth",
        "Hair": "Prop_Hair",
        "Hat": "Prop_Headwear",
        "Helmet": "Prop_Helmet",
        "Eyewear": "Prop_Eyewear",
        "MouthProp": "Prop_Facewear",
        "Jewelry": "Prop_FacialJewelry",
        "Clothing": "Prop_Top",
        "Accessory": "Prop_Accessory",
        "Bag": "Prop_Bag",
        "BackAttachment": "Prop_Back",
        "Bottom": "Prop_Bottom",
        "Shoes": "Prop_Footwear",
    }
    PARTS_NAME_FACE = "Head_Face"
    PARTS_NAME_BODY = "Body_Full"

    description = "Replace BeerGang parts category name with company's standard parts name."
    description_kr: str = "BeerGang 카테고리 이름을 전사 파츠 규격에 맞는 이름으로 치환합니다."
    in_use = True
    resource_type = TargetResourceType.ANY
    principle = Principle.CONSISTENCY
    upstreams = [ReplaceMeshNamesWithColNamesRule]

    @classmethod
    def apply(cls, gltf: GLTF2) -> GLTF2:
        for node in gltf.nodes:
            if not hasattr(node, "mesh") or node.mesh is None:
                continue

            name: str = node.name

            name_ts = name.rsplit("_", 1)
            name = name_ts[0]
            suffix = f"_{name_ts[1]}" if len(name_ts) == 2 else ""

            if name.lower() == "type":
                blender_object_name = node.extras["blender"]["object_name"]
                type_parts = blender_object_name.split("_")[0].lower()
                if type_parts == "body":
                    new_name = cls.PARTS_NAME_BODY
                elif type_parts == "head":
                    new_name = cls.PARTS_NAME_FACE
                else:
                    raise RuleApplyError(
                        cls.name,
                        "Type mesh name should start with either 'body' or 'head'",
                    )
            else:
                new_name = cls.PARTS_NAME_MAP.get(name, name)
                new_name = f"{new_name}{suffix}"

            node.name = new_name

        return gltf
