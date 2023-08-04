from abc import ABC

from gltf_formatter.model import GLTF2, BaseLogger, Principle, Rule, TargetResourceType


class AvatarRule(Rule, ABC):
    resource_type = TargetResourceType.AVATAR


class RegisterShapeKeyInfoToExtraRule(AvatarRule):
    description = "Register blend shape key related information into mesh node extra."
    description_kr: str = "blend shape key에 관련된 정보를 mesh node의 extra 영역에 추가합니다."
    in_use = True
    principle = Principle.CONSISTENCY

    @classmethod
    def poll(cls, gltf: GLTF2, logger: BaseLogger) -> bool:
        return len(gltf.meshes) > 0

    @classmethod
    def apply(cls, gltf: GLTF2, logger: BaseLogger) -> GLTF2:
        for node in gltf.nodes:
            if not hasattr(node, "mesh") or node.mesh is None:
                continue

            mesh_idx = node.mesh

            morph_targets = gltf.meshes[mesh_idx].primitives[0].targets
            node.extras["morph_target_num"] = len(morph_targets)

        return gltf


# TODO: Cleanup Animation but 1
