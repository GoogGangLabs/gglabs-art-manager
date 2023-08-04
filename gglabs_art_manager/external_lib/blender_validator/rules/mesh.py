from typing import Iterable, List, Tuple

import bpy

from blender_validator.exception import BlenderValidateError
from blender_validator.model import BaseLogger, Rule, RuleConstants, Severity, TaskType
from blender_validator.rules.utils import (
    iterate_category_mesh_objects,
    normalize_float_3d,
    normalize_float_4d,
)


class BSDFNodeSocketScalarValueRule(Rule):
    description = "Check if each parameter of BSDF node has valid value"
    description_kr: str = "BSDF node의 socket value들이 고정값으로 세팅된 경우, 이 값이 유효한 값인지를 검증합니다."
    in_use = True
    severity = Severity.ERROR

    BSDF_NODE_NAME = "Principled BSDF"
    ZERO_TO_ONE_RANGE_PARAMS: List[str] = [
        "Metallic",
        "Roughness",
        "Alpha",
        "Emission Strength",
    ]
    ZERO_TO_ZERO_RANGE_PARAMS: List[str] = [
        "Specular",
    ]
    COLOR_PARAMS: List[str] = ["Base Color"]

    @classmethod
    def error_message(
        cls,
        collection: str,
        mesh: str,
        material: str,
        parameter_name: str,
        current_value: any,
        desired_value_expr: str,
    ) -> bool:
        return (
            f"{collection}의 {mesh}와 연결된 {material}의 BSDF 설정값이 유효하지"
            f" 않습니다.\n{parameter_name}의 값은 {desired_value_expr}를 만족하여야 합니다. (현재값:"
            f" {current_value})"
        )

    @classmethod
    def validate(cls, constants: RuleConstants, task_type: TaskType, logger: BaseLogger) -> bool:
        if task_type in [TaskType.BODY_RIGGING, TaskType.FACE_RIGGING]:
            return True

        for col_expr, _, mesh in iterate_category_mesh_objects(constants.parts_categories):
            for ms in mesh.material_slots:
                mat = ms.material
                if mat is None or not mat.use_nodes:
                    continue

                for node in mat.node_tree.nodes:
                    if node.bl_label != cls.BSDF_NODE_NAME:
                        continue

                    for param in cls.ZERO_TO_ONE_RANGE_PARAMS:
                        socket: bpy.types.NodeSocketFloatFactor = node.inputs[param]
                        if socket.is_linked:
                            continue

                        socket_scalar = socket.default_value
                        if socket_scalar < 0 or socket_scalar > 1:
                            error = cls.error_message(
                                col_expr,
                                mesh.name,
                                mat.name,
                                param,
                                socket_scalar,
                                "(0.0 ~ 1.0)",
                            )
                            raise BlenderValidateError(error)

                    for param in cls.ZERO_TO_ZERO_RANGE_PARAMS:
                        socket: bpy.types.NodeSocketFloatFactor = node.inputs[param]
                        if socket.is_linked:
                            continue

                        socket_scalar = socket.default_value
                        if socket_scalar != 0.0:
                            error = cls.error_message(
                                col_expr,
                                mesh.name,
                                mat.name,
                                param,
                                socket_scalar,
                                "(0.0)",
                            )
                            logger.log(error)
                            return False

                    for param in cls.COLOR_PARAMS:
                        socket: bpy.types.NodeSocketColor = node.inputs[param]
                        if socket.is_linked:
                            continue

                        for socket_scalar in socket.default_value:
                            if socket_scalar < 0 or socket_scalar > 1:
                                error = cls.error_message(
                                    col_expr,
                                    mesh.name,
                                    mat.name,
                                    param,
                                    tuple(socket.default_value),
                                    "(0~1, 0~1, 0~1, 0~1)",
                                )
                                raise BlenderValidateError(error)

        return True

    @classmethod
    def fix(cls, constants: RuleConstants, task_type: TaskType, logger: BaseLogger) -> bool:
        for col_expr, _, mesh in iterate_category_mesh_objects(constants.parts_categories):
            for ms in mesh.material_slots:
                mat = ms.material
                if mat is None or not mat.use_nodes:
                    continue

                for node in mat.node_tree.nodes:
                    if node.bl_label != cls.BSDF_NODE_NAME:
                        continue

                    for param in cls.ZERO_TO_ZERO_RANGE_PARAMS:
                        socket: bpy.types.NodeSocketFloatFactor = node.inputs[param]
                        if socket.is_linked:
                            continue

                        socket_scalar = socket.default_value
                        if socket_scalar != 0.0:
                            socket.default_value = 0

                            logger.log(
                                f"[{col_expr}] {mesh.name} {mat.name} [BSDF Node - {param}] default"
                                f" value changed :: {socket_scalar} -> {socket.default_value}"
                            )

        return True


class EmptyMaterialSlotRule(Rule):
    description = "Check if there are any empty material slots in mesh objects"
    description_kr: str = "비어있는 material slot을 가지고 있는 mesh object들이 있는지 확인합니다."
    in_use = True
    severity = Severity.ERROR

    @classmethod
    def validate(cls, constants: RuleConstants, task_type: TaskType, logger: BaseLogger) -> bool:
        for _, _, obj in iterate_category_mesh_objects(constants.parts_categories):
            empty_material_slots = [ms for ms in obj.material_slots if ms.material is None]

            if len(empty_material_slots) > 0:
                # logger.log(f"[{col_expr}] {obj.name} contains empty material slots")
                return False

        return True

    @classmethod
    def fix(cls, constants: RuleConstants, task_type: TaskType, logger: BaseLogger) -> bool:
        for col_expr, _, obj in iterate_category_mesh_objects(constants.parts_categories):
            empty_material_slots: List[bpy.types.MaterialSlot] = [
                ms for ms in obj.material_slots if ms.material is None
            ]

            original_material_slot_count = len(obj.material_slots)
            empty_material_slot_count = len(empty_material_slots)

            if empty_material_slot_count > 0:
                bpy.context.view_layer.objects.active = obj
                bpy.ops.object.mode_set(mode="OBJECT")
                obj.select_set(True)

                # NOTE: When there're only empty slots, material_slot_remove_unused doesn't work properly.
                if len(obj.material_slots) == empty_material_slot_count:
                    bpy.ops.object.material_slot_remove()
                else:
                    bpy.ops.object.material_slot_remove_unused()

                logger.log(
                    f"[{col_expr}] {obj.name} Material Slots {original_material_slot_count} ->"
                    f" {len(obj.material_slots)} ({empty_material_slot_count} removed)"
                )
                obj.select_set(False)

        return True


class MeshObjectWithTransformValueRule(Rule):
    description = "Find mesh objects to which any transformation is applied"
    description_kr: str = "Transform/Delta Transform 이 적용되어진 mesh object가 있는지 확인합니다."
    in_use = True
    severity = Severity.ERROR

    @classmethod
    def object_generator(
        cls, constants: RuleConstants, task_type: TaskType
    ) -> Iterable[Tuple[str, bpy.types.Collection, bpy.types.Object]]:
        return iterate_category_mesh_objects(constants.parts_categories)

    @classmethod
    def _raise_when_strict(cls, e: BlenderValidateError, is_strict: bool) -> bool:
        if is_strict:
            raise e

        return False

    @classmethod
    def _validate_impl(
        cls, constants: RuleConstants, task_type: TaskType, logger: BaseLogger, is_strict: bool
    ) -> bool:
        res = True

        for col_expr, _, mesh in cls.object_generator(constants, task_type):
            euler = normalize_float_3d(tuple(mesh.rotation_euler))
            if euler != (0, 0, 0):
                res &= cls._raise_when_strict(
                    BlenderValidateError(
                        (
                            f"{col_expr}의 {mesh.name}의 rotation값이 (0, 0, 0)이 아닙니다. (현재값:"
                            f" {euler})\nobject의 상태를 확인한 뒤 transform 값을 직접 조정하거나\nobject >"
                            " apply 기능을 통해 현재 transform 상태를 object의 데이터값으로 적용해주세요."
                        ),
                    ),
                    is_strict,
                )

            quaternion = normalize_float_4d(tuple(mesh.rotation_quaternion))
            if quaternion != (1, 0, 0, 0):
                res &= cls._raise_when_strict(
                    BlenderValidateError(
                        (
                            f"{col_expr}의 {mesh.name}의 rotation값이 (1, 0, 0, 0)이 아닙니다. (현재값:"
                            f" {quaternion})\nobject의 상태를 확인한 뒤 transform 값을 직접 조정하거나\nobject"
                            " > apply 기능을 통해 현재 transform 상태를 object의 데이터값으로 적용해주세요."
                        ),
                    ),
                    is_strict,
                )

            scale = normalize_float_3d(tuple(mesh.scale))
            if scale != (1, 1, 1):
                res &= cls._raise_when_strict(
                    BlenderValidateError(
                        (
                            f"{col_expr}의 {mesh.name}의 scale값이 (1, 1, 1)이 아닙니다. (현재값:"
                            f" {scale})\nobject의 상태를 확인한 뒤 transform 값을 직접 조정하거나\nobject >"
                            " apply 기능을 통해 현재 transform 상태를 object의 데이터값으로 적용해주세요."
                        ),
                    ),
                    is_strict,
                )

            euler = normalize_float_3d(tuple(mesh.delta_rotation_euler))
            if euler != (0, 0, 0):
                res &= cls._raise_when_strict(
                    BlenderValidateError(
                        (
                            f"{col_expr}의 {mesh.name}의 delta rotation값이 (0, 0, 0)이 아닙니다."
                            f" (현재값: {euler})\nmesh의 상태를 확인한 뒤 transform 값을 직접"
                            " 조정하거나\nobject > apply 기능을 통해 현재 transform 상태를 object의 데이터값으로"
                            " 적용해주세요."
                        ),
                    ),
                    is_strict,
                )

            quaternion = normalize_float_4d(tuple(mesh.delta_rotation_quaternion))
            if quaternion != (1, 0, 0, 0):
                res &= cls._raise_when_strict(
                    BlenderValidateError(
                        (
                            f"{col_expr}의 {mesh.name}의 delta rotation값이 (1, 0, 0, 0)이 아닙니다."
                            f" (현재값: {quaternion})\nmesh의 상태를 확인한 뒤 transform 값을 직접"
                            " 조정하거나\nobject > apply 기능을 통해 현재 transform 상태를 mesh의 데이터값으로"
                            " 적용해주세요."
                        ),
                    ),
                    is_strict,
                )

            scale = normalize_float_3d(tuple(mesh.delta_scale))
            if scale != (1, 1, 1):
                res &= cls._raise_when_strict(
                    BlenderValidateError(
                        (
                            f"{col_expr}의 {mesh.name}의 delta scale값이 (1, 1, 1)이 아닙니다. (현재값:"
                            f" {scale})\nobject의 상태를 확인한 뒤 transform 값을 직접 조정하거나\nobject >"
                            " apply 기능을 통해 현재 transform 상태를 object의 데이터값으로 적용해주세요."
                        ),
                    ),
                    is_strict,
                )

            if not res:
                break

        return res

    @classmethod
    def validate(cls, constants: RuleConstants, task_type: TaskType, logger: BaseLogger):
        return cls._validate_impl(constants, task_type, logger, is_strict=False)

    @classmethod
    def fix(cls, constants: RuleConstants, task_type: TaskType, logger: BaseLogger) -> bool:
        for col_expr, _, obj in cls.object_generator(constants, task_type):
            before_scale = normalize_float_3d(tuple(obj.scale))
            before_rotation_euler = normalize_float_3d(tuple(obj.rotation_euler))
            before_rotation_quaternion = normalize_float_4d(tuple(obj.rotation_quaternion))
            before_delta_scale = normalize_float_3d(tuple(obj.delta_scale))
            before_delta_rotation_euler = normalize_float_3d(tuple(obj.delta_rotation_euler))
            before_delta_rotation_quaternion = normalize_float_4d(
                tuple(obj.delta_rotation_quaternion)
            )

            should_passes = [
                before_scale == (1, 1, 1),
                before_rotation_euler == (0, 0, 0),
                before_rotation_quaternion == (1, 0, 0, 0),
                before_delta_scale == (1, 1, 1),
                before_delta_rotation_euler == (0, 0, 0),
                before_delta_rotation_quaternion == (1, 0, 0, 0),
            ]

            if all(should_passes):
                continue

            # Apply delta scale to transform scale
            obj.scale.x *= obj.delta_scale.x
            obj.scale.y *= obj.delta_scale.y
            obj.scale.z *= obj.delta_scale.z
            obj.delta_scale = (1, 1, 1)

            # Call transform_apply
            bpy.context.view_layer.objects.active = obj
            bpy.ops.object.mode_set(mode="OBJECT")
            obj.select_set(True)
            bpy.ops.object.transform_apply()
            obj.select_set(False)

            after_scale = normalize_float_3d(tuple(obj.scale))
            after_rotation_euler = normalize_float_3d(tuple(obj.rotation_euler))
            after_rotation_quaternion = normalize_float_4d(tuple(obj.rotation_quaternion))
            after_delta_scale = normalize_float_3d(tuple(obj.delta_scale))
            after_delta_rotation_euler = normalize_float_3d(tuple(obj.delta_rotation_euler))
            after_delta_rotation_quaternion = normalize_float_4d(
                tuple(obj.delta_rotation_quaternion)
            )

            logger.log(f"[{col_expr}] {obj.name} Transform Applied")
            if not should_passes[0]:
                logger.log(f" Scale: {before_scale} -> {after_scale}")
            if not should_passes[1]:
                logger.log(f" Rotation Euler: {before_rotation_euler} -> {after_rotation_euler}")
            if not should_passes[2]:
                logger.log(
                    f" Rotation Quaternion: {before_rotation_quaternion} ->"
                    f" {after_rotation_quaternion}"
                )
            if not should_passes[3]:
                logger.log(f" Delta Scale: {before_delta_scale} -> {after_delta_scale}")
            if not should_passes[4]:
                logger.log(
                    f" Delta Rotation Euler: {before_delta_rotation_euler} ->"
                    f" {after_delta_rotation_euler}"
                )
            if not should_passes[5]:
                logger.log(
                    f" Delta Rotation Quaternion: {before_delta_rotation_quaternion} ->"
                    f" {after_delta_rotation_quaternion}"
                )

        return True


class MultipleMaterialsInMeshRule(Rule):
    description = "Check if there are mesh objects having multiple materials"
    description_kr: str = "2개 이상의 material을 가지고 있는 mesh object가 있는지 확인합니다."
    in_use = True
    severity = Severity.ERROR

    @classmethod
    def validate(cls, constants: RuleConstants, task_type: TaskType, logger: BaseLogger) -> bool:
        if task_type in [TaskType.BODY_RIGGING, TaskType.FACE_RIGGING]:
            return True

        for col_expr, _, mesh in iterate_category_mesh_objects(constants.parts_categories):
            material_slots = [ms for ms in mesh.material_slots if ms.material is not None]

            if len(material_slots) >= 2:
                raise BlenderValidateError(
                    f"{col_expr}의 {mesh.name}에 2개 이상의 material이 설정되어져 있습니다. 하나만 남기고 지워주세요.",
                )

        return True


class MeshAnimationDataCleanupRule(Rule):
    description = "Clean up unintended animation data in mesh objects if exists."
    description_kr: str = "Facial Rigging 과정에서 mesh object primitives에 애니메이션 데이터가 있는 경우 삭제합니다."
    in_use = True
    severity = Severity.ERROR

    @classmethod
    def validate(cls, constants: RuleConstants, task_type: TaskType, logger: BaseLogger) -> bool:
        if task_type in [TaskType.ANIMATING, TaskType.MASTERING]:
            return True

        # 0. Get target mesh
        for col_expr, _, obj in iterate_category_mesh_objects(constants.parts_categories):
            if obj.animation_data is not None:
                logger.log(f"[{col_expr}] {obj.name} has unnecessary animation data")
                return False

        return True

    @classmethod
    def fix(cls, constants: RuleConstants, task_type: TaskType, logger: BaseLogger) -> bool:
        for col_expr, _, obj in iterate_category_mesh_objects(constants.parts_categories):
            anim_data = obj.animation_data
            if anim_data is not None:
                anim_name = anim_data.action.name

                obj_channels = set()
                for fcurve in anim_data.action.fcurves:
                    # scale, rotation_euler, ..
                    obj_channels.add(fcurve.data_path)

                obj_channels_expr = ", ".join(obj_channels)
                logger.log(
                    f"[{col_expr}] {obj.name} 의 animation 데이터를 삭제했습니다."
                    f"\n animation track: {anim_name}"
                    f"\n mesh 채널: ({obj_channels_expr})"
                )
                obj.animation_data_clear()

        return True
