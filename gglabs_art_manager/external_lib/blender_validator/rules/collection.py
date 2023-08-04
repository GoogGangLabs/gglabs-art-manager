from typing import Iterable, List, Tuple

import bpy
import idprop

from blender_validator.exception import BlenderValidateError
from blender_validator.model import BaseLogger, Rule, RuleConstants, Severity, TaskType
from blender_validator.rules.utils import (
    iterate_category_collections,
    iterate_category_mesh_objects,
    iterate_collections,
    main_collection,
    norm_str,
)

"""
Rules for the Collection and Object structure
"""

class NoMainCollectionRule(Rule):
    description = "Check if the main collection exists"
    description_kr: str = "검사의 대상이 될 메인 컬렉션이 있는지 확인합니다."
    in_use = True
    severity = Severity.ERROR

    @classmethod
    def validate(cls, constants: RuleConstants, task_type: TaskType, logger: BaseLogger) -> bool:
        main_collection()
        return True


class ObjectsWithoutParentCollectionRule(Rule):
    description = "Check if there are any objects not having a parent collection."
    description_kr: str = "상위 컬렉션없이 메인 컬렉션에 바로 속하는 object가 있는지 확인합니다."
    in_use = True
    severity = Severity.WARNING

    @classmethod
    def validate(cls, constants: RuleConstants, task_type: TaskType, logger: BaseLogger) -> bool:
        dangling_obj_names = [obj.name for obj in main_collection().objects]

        if len(dangling_obj_names) > 0:
            message = (
                "별도의 상위 컬렉션에 속하지 않은 object들이 있습니다."
                f" :: ({','.join(dangling_obj_names)})"
                "\n이미 있는 컬렉션으로 이동시키거나 새로운 컬렉션을 만들어 옮겨주세요."
            )
            raise BlenderValidateError(message)

        return True


class InvalidCollectionNameRule(Rule):
    description = "Validate all collection names"
    description_kr: str = "모든 컬렉션 이름이 유효한지 확인합니다. 공백처럼 눈으로 안보이는 문자를 체크하게 됩니다."
    in_use = True
    severity = Severity.WARNING

    @classmethod
    def patch_name(cls, name: str) -> bool:
        return name.strip()

    @classmethod
    def validate(cls, constants: RuleConstants, task_type: TaskType, logger: BaseLogger) -> bool:
        for col in iterate_collections():
            if col.name != cls.patch_name(col.name):
                return False

        return True

    @classmethod
    def fix(cls, constants: RuleConstants, task_type: TaskType, logger: BaseLogger) -> bool:
        for col in iterate_collections():
            original_name = col.name
            col.name = cls.patch_name(col.name)

            if original_name != col.name:
                logger.log(f"Collection renamed :: {original_name} -> {col.name}")

        return True


class MissingMandatoryHeadCollectionRule(Rule):
    description = "Check if any mandatory head collection is missing."
    description_kr: str = "꼭 필요한 헤드 파츠 컬렉션이 빠져있는지 확인합니다."
    in_use = True
    severity = Severity.ERROR

    @classmethod
    def validate(cls, constants: RuleConstants, task_type: TaskType, logger: BaseLogger) -> bool:
        norm_to_collection = {
            norm_str(category_name): category_col
            for category_name, category_col in iterate_category_collections(
                constants.mandatory_head_categories
            )
        }

        for col in constants.mandatory_head_categories:
            norm_col = norm_str(col)

            if norm_col not in norm_to_collection:
                raise BlenderValidateError(
                    (
                        f"Head 파츠용 컬렉션 {col}이 View Layer에 없습니다.\n메인 collection 하위에 컬렉션을 만든 뒤 메쉬데이터를"
                        " 추가해주세요."
                    ),
                )

            actual_col = norm_to_collection[norm_col]
            objs = [obj for obj in actual_col.all_objects if obj.type == "MESH"]
            if len(objs) == 0:
                raise BlenderValidateError(f"Head 파츠용 컬렉션[{actual_col.name}]에 메쉬데이터가 없습니다.")

        return True


class MissingMandatoryPartsCollectionRule(Rule):
    description = "Check if any mandatory collection is missing."
    description_kr: str = "꼭 필요한 파츠 컬렉션이 빠져있는지 확인합니다."
    in_use = True
    severity = Severity.ERROR

    @classmethod
    def validate(cls, constants: RuleConstants, task_type: TaskType, logger: BaseLogger) -> bool:
        norm_to_collection = {
            norm_str(category_name): category_col
            for category_name, category_col in iterate_category_collections(
                constants.mandatory_parts_categories
            )
        }

        for col in constants.mandatory_parts_categories:
            norm_col = norm_str(col)

            if norm_col not in norm_to_collection:
                raise BlenderValidateError(
                    f"Body 파츠용 컬렉션 {col}이 View Layer에 없습니다.\n메인 collection 하위에 만든 뒤 메쉬데이터를 넣어주세요.",
                )

            actual_col = norm_to_collection[norm_col]
            objs = [obj for obj in actual_col.all_objects if obj.type == "MESH"]
            if len(objs) == 0:
                raise BlenderValidateError(f"Body 파츠용 컬렉션 {norm_col}에 메쉬데이터가 없습니다.")

        return True


class PartsCollectionWithMultipleMeshRule(Rule):
    description = "Verify all parts category collections contains only one mesh object"
    description_kr: str = "파츠 컬렉션이 하나의 mesh object만 가지고 있는지 체크합니다."
    in_use = True
    severity = Severity.ERROR

    @classmethod
    def validate(cls, constants: RuleConstants, task_type: TaskType, logger: BaseLogger) -> bool:
        for category_name, category_col in iterate_category_collections(constants.parts_categories):
            # Beergang category "type" is exceptional. Do not apply this rule for this.
            if norm_str(category_name) == "type":
                continue

            for parts_col in category_col.children:
                objs = [obj for obj in parts_col.all_objects if obj.type == "MESH"]

                if len(objs) > 1:
                    raise BlenderValidateError(
                        (
                            f"컬렉션[{category_col.name}/{parts_col.name}]에 현재"
                            f" {len(objs)}개의 mesh가 있습니다.\n각 파츠 컬렉션에는 하나의 mesh만"
                            " 허용됩니다."
                        ),
                    )

        return True


class BeergangTypeHeadAnyBodyMeshRule(Rule):
    description = "Check if Beergang Type collection only contains `head_` and `body_` meshes"
    description_kr: str = "Beergang Type 컬렉션에 `head_` 와 `body_` 외의 네이밍 규칙을 갖고 있는 mesh가 있는지 확인합니다."
    in_use = True
    severity = Severity.ERROR

    @classmethod
    def _iterate_collections_with_name(
        cls, task_type: TaskType
    ) -> Iterable[Tuple[str, bpy.types.Collection]]:
        assert task_type != TaskType.ANY

        if task_type != TaskType.MASTERING:
            for _, col in iterate_category_collections(["Type"]):
                yield (col.name, col)
        else:
            for _, category_col in iterate_category_collections(["Type"]):
                for parts_col in category_col.children:
                    yield (f"{category_col.name}/{parts_col.name}", parts_col)

    @classmethod
    def validate(cls, constants: RuleConstants, task_type: TaskType, logger: BaseLogger) -> bool:
        head_meshes: List[bpy.types.Object]
        body_meshes: List[bpy.types.Object]
        wrong_meshes: List[bpy.types.Object]

        for col_name, col in cls._iterate_collections_with_name(task_type):
            head_meshes = []
            body_meshes = []
            wrong_meshes = []

            meshes = [obj for obj in col.all_objects if obj.type == "MESH" and obj.visible_get()]

            for obj in meshes:
                if obj.name.lower().startswith("head_"):
                    head_meshes.append(obj)
                elif obj.name.lower().startswith("body_"):
                    body_meshes.append(obj)
                else:
                    wrong_meshes.append(obj)

            if len(head_meshes) > 1:
                mesh_names = ", ".join([o.name for o in head_meshes])
                raise BlenderValidateError(
                    (
                        f"컬렉션[{col_name}]에는 이름이 `head_` 로 시작하는 mesh object는 하나만 허용됩니다."
                        f"\n현재 총 {len(head_meshes)}개의 object ({mesh_names})가 있습니다."
                    ),
                )
            if len(body_meshes) > 1:
                mesh_names = ", ".join([o.name for o in body_meshes])
                raise BlenderValidateError(
                    (
                        f"컬렉션[{col_name}]에는 이름이 `body_` 로 시작하는 mesh object는 하나만 허용됩니다."
                        f"\n현재 총 {len(body_meshes)}개의 object ({mesh_names})가 있습니다."
                    ),
                )
            if len(wrong_meshes) > 0:
                mesh_names = ", ".join([o.name for o in wrong_meshes])
                raise BlenderValidateError(
                    (
                        f"컬렉션[{col_name}]에는 이름이 `head_` 혹은 `body_` 로 시작하는 mesh object만"
                        f" 허용됩니다.\n현재 총 {len(wrong_meshes)}개의 잘못된 object"
                        f" ({mesh_names})가 있습니다."
                    ),
                )

            if len(body_meshes) == 1:
                obj = body_meshes[0]
                mesh: bpy.types.Mesh = obj.data
                if mesh.shape_keys is not None and len(mesh.shape_keys.key_blocks) > 0:
                    raise BlenderValidateError(
                        (
                            f"컬렉션[{col_name}]의 `body_` 로 시작하는 mesh는 shapekey가 허용되지"
                            f" 않습니다.\n{col_name}의 {obj.name}({mesh.name})에 지정되어져 있는"
                            " shapekey를 확인하신 후 정리해주세요."
                        ),
                    )

        return True


class WriteObjectCustomPropertiesRule(Rule):
    description = "Write collection structure info to custom properties of objects"
    description_kr: str = "컬렉션 관련 정보를 object의 custom property 영역에 추가합니다."
    in_use = True
    severity = Severity.INFORMATION

    # TODO: Armature Objects

    @classmethod
    def validate(cls, constants: RuleConstants, task_type: TaskType, logger: BaseLogger) -> bool:
        for _, category_col, mesh in iterate_category_mesh_objects(constants.parts_categories):
            blender_info: idprop.types.IDPropertyGroup = mesh.get("blender")

            if blender_info is None or not isinstance(blender_info, idprop.types.IDPropertyGroup):
                return False
            if category_col.name != blender_info.get("collection_name"):
                return False

        return True

    @classmethod
    def fix(cls, constants: RuleConstants, task_type: TaskType, logger: BaseLogger) -> bool:
        for col_expr, category_col, obj in iterate_category_mesh_objects(
            constants.parts_categories
        ):
            logger.log(
                f"[{col_expr}] {obj.name} ({obj.data.name}) updated custom property [blender]"
            )
            obj["blender"] = {"collection_name": category_col.name}

        return True
