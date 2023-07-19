import bpy
from blender_validator.exception import BlenderValidateError
from blender_validator.model import Rule, RuleConstants, Severity
from blender_validator.rules.utils import arrange_shapekeys, norm_str


class BeergangShapeKeyArrangementRule(Rule):
    description = "Check if all face meshes contains complete shapekey list"
    description_kr: str = "shapekey를 가진 mesh가 정해진 shapekey 목록을 전부 포함하는지 여부를 체크합니다."
    in_use = True
    severity = Severity.ERROR

    @classmethod
    def validate(cls, constants: RuleConstants) -> bool:
        return True

    @classmethod
    def fix(cls, constants: RuleConstants) -> str:
        report_lines = []
        norm_categories = [norm_str(c) for c in constants.shapekey_categories]

        # 0. Get target mesh
        for col in bpy.context.scene.collection.children:
            norm_col = norm_str(col.name)
            if norm_col in norm_categories:
                meshes = [
                    obj
                    for obj in col.all_objects
                    if obj.type == "MESH" and not obj.name.lower().startswith("body_")
                ]

                for mesh in meshes:
                    sk_report_lines = [
                        f"Shapekey[{d.key}] {d.detail}"
                        for details in arrange_shapekeys(mesh, constants.shapekeys).values()
                        for d in details
                    ]
                    if len(sk_report_lines) > 0:
                        report_lines.append(
                            f"!! Shapekey Fixed [{col.name}] {mesh.name} ({mesh.data.name}) !!"
                        )
                        report_lines.extend(sk_report_lines)
                        report_lines.append("")

        return "\n".join(report_lines)


class BeergangBodyWithShapeKeyedMeshRule(Rule):
    description = "Verify that the shape key is present in the body mesh"
    description_kr: str = "type category의 body mesh에 shapekey가 있는 경우를 확인합니다."
    in_use = True
    severity = Severity.ERROR

    @classmethod
    def validate(cls, constants: RuleConstants) -> bool:
        # 0. Get target mesh
        for col in bpy.context.scene.collection.children:
            norm_col = norm_str(col.name)

            if norm_col == "type":
                meshes = [
                    obj
                    for obj in col.all_objects
                    if obj.type == "MESH" and obj.name.lower().startswith("body_")
                ]
                for obj in meshes:
                    mesh: bpy.types.Mesh = obj.data
                    if mesh.shape_keys is not None and len(mesh.shape_keys.key_blocks) > 0:
                        raise BlenderValidateError(
                            f"{col.name} 파츠의 body type mesh는 shapekey가 허용되지 않습니다."
                            f"\n{col.name}의 {obj.name}({mesh.name})에 지정되어져 있는 shapekey를 확인하신 후 정리해주세요."
                        )

        return True
