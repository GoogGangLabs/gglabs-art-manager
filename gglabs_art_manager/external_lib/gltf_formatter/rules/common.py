import json
from abc import ABC
from collections import Counter, defaultdict

from gltf_formatter.exception import RuleApplyError
from gltf_formatter.model import GLTF2, BaseLogger, Principle, Rule, TargetResourceType
from gltf_formatter.rules.utils import (
    accessor_reference_counter,
    bufferview_reference_counter,
    remove_accessor,
    remove_bufferview,
)


class CommonRule(Rule, ABC):
    resource_type = TargetResourceType.ANY


class ReplaceMeshNamesWithColNamesRule(CommonRule):
    EXTRA_KEY_BLENDER = "blender"
    EXTRA_KEY_COLLECTION = "collection_name"

    description = "Replace mesh names with corresponding collection names."
    description_kr: str = (
        f"메쉬 이름을 사용자가 직접 지정한 extra 영역의 '{EXTRA_KEY_BLENDER}.{EXTRA_KEY_COLLECTION}' 값으로"
        " 대체합니다. GLB의 동일 카테고리에 대응되는 메쉬 이름을 하나의 값으로 유지하기 위한 작업입니다. 대신 node.extra 영역에"
        " overwrite 되어지는 기존 Mesh 이름 정보를 추가합니다."
    )
    in_use = True
    principle = Principle.CONSISTENCY

    @classmethod
    def poll(cls, gltf: GLTF2, logger: BaseLogger) -> bool:
        # TODO: Each collection should contain only one single mesh.
        for node in gltf.nodes:
            if not hasattr(node, "mesh") or node.mesh is None:
                continue
            if cls.EXTRA_KEY_COLLECTION not in node.extras.get(cls.EXTRA_KEY_BLENDER, {}):
                logger.log(f"{node.name} has no {cls.EXTRA_KEY_COLLECTION}")
                return False
        
        return True

    @classmethod
    def apply(cls, gltf: GLTF2, logger: BaseLogger) -> GLTF2:
        node_name_cnt = Counter()

        for node in gltf.nodes:
            if not hasattr(node, "mesh") or node.mesh is None:
                continue

            mesh_idx = node.mesh
            blender_extras = node.extras.get(cls.EXTRA_KEY_BLENDER, {})
            blender_extras["mesh_name"] = gltf.meshes[mesh_idx].name
            blender_extras["object_name"] = node.name
            node_name = blender_extras.get(cls.EXTRA_KEY_COLLECTION, node.name)

            cidx = node_name_cnt[node_name]
            suffix = "" if cidx == 0 else f"_{cidx}"
            node.name = f"{node_name}{suffix}"
            node_name_cnt[node_name] += 1

        return gltf


class CleanupUnusedExtraRule(CommonRule):
    ALLOWED_GLTF_EXTRA_PREFIXES = [
        "targetNames",
        "morph_target_num",
        "blender",
        "beergangs",
    ]

    description = "Purge all unnecessary entries in the extra fields across all GLTF properties."
    description_kr: str = "extra 영역에서 사용되지 않는 정보들을 일괄 삭제합니다."
    in_use = True
    principle = Principle.PURITY

    @classmethod
    def apply(cls, gltf: GLTF2, logger: BaseLogger) -> GLTF2:
        def is_allowed_key(key: str) -> bool:
            return any(key.startswith(prefix) for prefix in cls.ALLOWED_GLTF_EXTRA_PREFIXES)

        for scene in gltf.scenes:
            scene.extras = {}
        for node in gltf.nodes:
            node.extras = {k: v for k, v in node.extras.items() if is_allowed_key(k)}
        for mesh in gltf.meshes:
            mesh.extras = {k: v for k, v in mesh.extras.items() if is_allowed_key(k)}
        for materials in gltf.materials:
            materials.extras = {k: v for k, v in materials.extras.items() if is_allowed_key(k)}

        return gltf


class CleanupUnusedTexcoordRule(CommonRule):
    """
    Resolves: {
        "code": "UNUSED_OBJECT",
        "message": "This object may be unused.",
        "severity": 2,
        "pointer": "/meshes/0/primitives/0/attributes/TEXCOORD_0"
    }
    """

    description = "Purge all unused uv maps in mesh data along with texcoord attributes"
    description_kr: str = "사용되지 않는 UV Map 데이터 및 TEXCOORD attribute을 삭제합니다."
    in_use = False
    principle = Principle.PURITY

    @classmethod
    def apply(cls, gltf: GLTF2, logger: BaseLogger) -> GLTF2:
        accessor_refcnt = accessor_reference_counter(gltf)
        accessor_obsolete_refcnt = Counter()
        bufferview_refcnt = bufferview_reference_counter(gltf)
        bufferview_obsolete_refcnt = Counter()
        meshprim_to_unused_texcoord_idxes = defaultdict(set)

        for mesh_idx, mesh in enumerate(gltf.meshes):
            for prim_idx, prim in enumerate(mesh.primitives):
                texcoord_idx_to_accessor = {}
                mesh_texcoord_idxes = set()

                # 1. Gather uv map indicators for the mesh
                attrmap = json.loads(prim.attributes.to_json())
                for attrkey, attrval in attrmap.items():
                    if "TEXCOORD_" in attrkey:
                        texcoord_idx = int(attrkey.split("_")[-1])
                        mesh_texcoord_idxes.add(texcoord_idx)
                        texcoord_idx_to_accessor[texcoord_idx] = attrval
                has_uv = len(mesh_texcoord_idxes) > 0

                # 2. Mesh doesn't have uv map
                if not has_uv:
                    continue

                # 3. Mesh has uv map but no material data
                elif prim.material is None:
                    for texcoord_idx, accessor_idx in texcoord_idx_to_accessor.items():
                        meshprim_to_unused_texcoord_idxes[(mesh_idx, prim_idx)].add(texcoord_idx)

                # 4. Mesh's material textures
                else:
                    material = gltf.materials[prim.material]
                    material_textures = [
                        material.normalTexture,
                        material.occlusionTexture,
                        material.emissiveTexture,
                        material.pbrMetallicRoughness.baseColorTexture
                        if material.pbrMetallicRoughness is not None
                        else None,
                        material.pbrMetallicRoughness.metallicRoughnessTexture
                        if material.pbrMetallicRoughness is not None
                        else None,
                    ]

                    # 4.1 Collect all texcoord idxes being used by material textures.
                    material_texcoord_idxes = set()
                    for material_texture in material_textures:
                        if material_texture is not None:
                            material_texcoord_idxes.add(material_texture.texCoord or 0)

                    # 4.2 Mesh's texcoord idxes not being used by material textures.
                    unused_texcoord_idxes = mesh_texcoord_idxes - material_texcoord_idxes
                    for texcoord_idx in unused_texcoord_idxes:
                        meshprim_to_unused_texcoord_idxes[(mesh_idx, prim_idx)].add(texcoord_idx)

                # 5. Count obsolete references for accessors of TEXCOORD_N to be removed
                for texcoord_idx in meshprim_to_unused_texcoord_idxes[(mesh_idx, prim_idx)]:
                    accessor_idx = texcoord_idx_to_accessor[texcoord_idx]
                    if accessor_idx is not None:
                        # print(f"meshes[{mesh_idx}].prims[{prim_idx}].TEXCOORD_{texcoord_idx} -> {accessor_idx}")
                        accessor_obsolete_refcnt[accessor_idx] += 1

        # 8.1 Determine obsolete accessors by calculating remaining reference counter
        accessor_idx_to_be_deleted = set()
        for accessor_idx, obsolete_refcnt in accessor_obsolete_refcnt.items():
            if obsolete_refcnt >= accessor_refcnt[accessor_idx]:
                accessor_idx_to_be_deleted.add(accessor_idx)
                bufferview_idx = gltf.accessors[accessor_idx].bufferView
                if bufferview_idx is not None:
                    bufferview_obsolete_refcnt[bufferview_idx] += 1

        # 8.2 Determine obsolete bufferviews by calculating remaining reference counter
        bufferview_idx_to_be_deleted = set()
        for bufferview_idx, obsolete_refcnt in bufferview_obsolete_refcnt.items():
            if obsolete_refcnt >= bufferview_refcnt[bufferview_idx]:
                bufferview_idx_to_be_deleted.add(bufferview_idx)

        # 9. Cleanup
        # 9.1 Cleanup obsolete bufferviews
        for loop_idx, bufferview_idx in enumerate(bufferview_idx_to_be_deleted):
            remove_bufferview(gltf, bufferview_idx - loop_idx)

        # 9.2 Cleanup obsolete accessors
        for loop_idx, accessor_idx in enumerate(accessor_idx_to_be_deleted):
            print(f"accessor[{accessor_idx}] going to be deleted")
            remove_accessor(gltf, accessor_idx - loop_idx)

        # 9.3 Mesh texcoord attributes
        for (
            mesh_idx,
            prim_idx,
        ), texcoord_idxes in meshprim_to_unused_texcoord_idxes.items():
            attr = gltf.meshes[mesh_idx].primitives[prim_idx].attributes
            for texcoord_idx in texcoord_idxes:
                delattr(attr, f"TEXCOORD_{texcoord_idx}")

        return gltf


class CleanupUnusedTangentRule(CommonRule):
    """
    Resolves: {
        "code": "UNUSED_MESH_TANGENT",
        "message": "Tangents are not used because the material has no normal texture.",
        "severity": 2,
        "pointer": "/meshes/0/primitives/0/attributes/TANGENT"
    }
    """

    description = "Clean up unused tangent data in mesh data"
    description_kr: str = "사용되지 않는 mesh tangent 데이터를 삭제합니다."
    in_use = False
    principle = Principle.PURITY

    @classmethod
    def apply(cls, gltf: GLTF2, logger: BaseLogger) -> GLTF2:
        accessor_refcnt = accessor_reference_counter(gltf)
        accessor_obsolete_refcnt = Counter()
        bufferview_refcnt = bufferview_reference_counter(gltf)
        bufferview_obsolete_refcnt = Counter()

        meshprim_to_delete_tangent = set()

        for mesh_idx, mesh in enumerate(gltf.meshes):
            for prim_idx, prim in enumerate(mesh.primitives):
                tangent_accessor_idx = prim.attributes.TANGENT
                has_tangent = tangent_accessor_idx is not None

                # 1. Mesh doesn't have tangent vectors
                if not has_tangent:
                    continue

                # 2. Mesh has tangent but no material data
                elif prim.material is None:
                    accessor_obsolete_refcnt[tangent_accessor_idx] += 1
                    meshprim_to_delete_tangent.add((mesh_idx, prim_idx))

                # 3. Mesh's material has no normal texture
                elif gltf.materials[prim.material].normalTexture is None:
                    accessor_obsolete_refcnt[tangent_accessor_idx] += 1
                    meshprim_to_delete_tangent.add((mesh_idx, prim_idx))

        # 8. Determine obsolete accessor/bufferviews by calculating reference counter
        accessor_idx_to_be_deleted = set()
        for accessor_idx, obsolete_refcnt in accessor_obsolete_refcnt.items():
            if obsolete_refcnt >= accessor_refcnt[accessor_idx]:
                accessor_idx_to_be_deleted.add(accessor_idx)
                bufferview_idx = gltf.accessors[accessor_idx].bufferView
                if bufferview_idx is not None:
                    bufferview_obsolete_refcnt[bufferview_idx] += 1

        bufferview_idx_to_be_deleted = set()
        for bufferview_idx, obsolete_refcnt in bufferview_obsolete_refcnt.items():
            if obsolete_refcnt >= bufferview_refcnt[bufferview_idx]:
                bufferview_idx_to_be_deleted.add(bufferview_idx)

        # 9. Cleanup in order
        bufferview_idx_to_be_deleted = sorted(list(bufferview_idx_to_be_deleted))
        accessor_idx_to_be_deleted = sorted(list(accessor_idx_to_be_deleted))

        # 9.1 Cleanup obsolete bufferviews
        for loop_idx, bufferview_idx in enumerate(bufferview_idx_to_be_deleted):
            remove_bufferview(gltf, bufferview_idx - loop_idx)

        # 9.2 Cleanup obsolete accessors
        for loop_idx, accessor_idx in enumerate(accessor_idx_to_be_deleted):
            remove_accessor(gltf, accessor_idx - loop_idx)

        # 9.3 Clenaup Mesh tangent attribute
        for mesh_idx, prim_idx in meshprim_to_delete_tangent:
            attr = gltf.meshes[mesh_idx].primitives[prim_idx].attributes
            delattr(attr, "TANGENT")

        return gltf


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
    def apply(cls, gltf: GLTF2, logger: BaseLogger) -> GLTF2:
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
                        "Type mesh name should start with either 'body' or 'head'"
                    )
            else:
                new_name = cls.PARTS_NAME_MAP.get(name, name)
                new_name = f"{new_name}{suffix}"

            node.name = new_name

        return gltf
