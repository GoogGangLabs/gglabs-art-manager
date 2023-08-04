from typing import Dict, Iterable, List, Tuple

import bpy

from blender_validator.exception import BlenderValidateError
from blender_validator.model import ShapekeyChangeDetail, ShapekeyChangeReport, ShapekeyChangeType

MAIN_COLLECTION = "Main"


def norm_str(s: str) -> str:
    return "".join(s.lower().split("_"))


def main_collection(use_scene_collection: bool = False) -> bpy.types.Collection:
    res = None

    if use_scene_collection:
        res = bpy.context.scene.collection
    else:
        for sub_col in bpy.context.scene.collection.children:
            if sub_col.name.lower() == MAIN_COLLECTION.lower():
                res = sub_col
                break

    if res is None:
        raise BlenderValidateError(
            "Main 컬렉션이 View Layer에 없습니다.\nScene collection 하위에 하나 만들어서 모든 파츠 데이터들을 옮겨주세요."
        )

    return res


def main_layer_collection(
    use_scene_collection: bool = False,
) -> bpy.types.LayerCollection:
    res = None

    if use_scene_collection:
        res = bpy.context.scene.view_layers[0].layer_collection
    else:
        for sub_col in bpy.context.scene.view_layers[0].layer_collection.children:
            if sub_col.name.lower() == MAIN_COLLECTION.lower():
                res = sub_col
                break

    if res is None:
        raise BlenderValidateError(
            "현재 Main 컬렉션이 View Layer에 없습니다.\nScene collection 하위에 하나 만들어서 모든 파츠 데이터들을 옮겨주세요."
        )

    return res


def set_visibility_of_collection(
    col: bpy.types.Collection,
    is_shown: bool,
    with_children: bool = True,
    _is_first_call=True,
):
    col.hide_render = not is_shown
    col.hide_viewport = not is_shown

    # Heads-up: Iterating from `col.all_objects` directly causes an segmentation error.
    # Consider with_object option so as not to unnecessary run below codes recursively
    if with_children:
        if _is_first_call:
            for obj in list(col.all_objects):
                obj.hide_render = not is_shown
                obj.hide_viewport = not is_shown

        for subcol in col.children:
            set_visibility_of_collection(subcol, is_shown, with_children, False)


def set_visibility_of_layer_collection(
    col: bpy.types.LayerCollection,
    is_shown: bool,
    with_children: bool = True,
    _is_first_call=True,
):
    # TODO: Make compliance for this
    col.exclude = False
    col.hide_viewport = not is_shown

    if with_children:
        if _is_first_call:
            for obj in list(col.collection.all_objects):
                obj.hide_set(not is_shown)

        for subcol in col.children:
            set_visibility_of_layer_collection(subcol, is_shown, with_children, False)


def construct_collection_view_included_map() -> Dict[str, bool]:
    ret = {}

    queue = list(main_layer_collection().children)
    while len(queue) > 0:
        col = queue.pop()
        ret[col.name] = not col.exclude

        for subcol in col.children:
            queue.append(subcol)

    return ret


def construct_layer_collections() -> Dict[str, bpy.types.LayerCollection]:
    ret = {}

    queue = list(main_layer_collection().children)
    while len(queue) > 0:
        col = queue.pop()
        ret[col.name] = col
        ret[col.name.lower()] = col

        for subcol in col.children:
            queue.append(subcol)

    return ret


def iterate_collections() -> Iterable[bpy.types.Collection]:
    colname_included = construct_collection_view_included_map()

    queue = list(main_collection().children)
    while len(queue) > 0:
        col = queue.pop()

        if colname_included[col.name]:
            yield col

        for subcol in col.children:
            queue.append(subcol)


def iterate_category_collections(
    category_names: List[str],
) -> Iterable[Tuple[str, bpy.types.Collection]]:
    colname_included = construct_collection_view_included_map()

    cols = [c for c in main_collection().children if colname_included[c.name]]
    actual_norm_cols = {norm_str(c.name): c for c in cols}

    for category_name in category_names:
        norm_category_name = norm_str(category_name)

        if norm_category_name in actual_norm_cols:
            yield (category_name, actual_norm_cols[norm_category_name])


def iterate_armature_objects() -> Iterable[Tuple[str, bpy.types.Collection, bpy.types.Object]]:
    for category_name, category_col in iterate_category_collections(["common"]):
        for obj in category_col.all_objects:
            if obj.type == "ARMATURE" and obj.visible_get():
                yield (category_name, category_col, obj)


def iterate_category_mesh_objects(
    category_names: List[str], has_parts_collection: bool = True
) -> Iterable[Tuple[str, bpy.types.Collection, bpy.types.Object]]:
    for category_name, category_col in iterate_category_collections(category_names):
        if has_parts_collection:
            for parts_col in category_col.children:
                for obj in parts_col.all_objects:
                    if obj.type == "MESH" and obj.visible_get():
                        yield (f"{category_name} > {parts_col.name}", category_col, obj)
        else:
            for obj in category_col.all_objects:
                if obj.type == "MESH" and obj.visible_get():
                    yield (category_name, category_col, obj)


def is_zero_float(v: float) -> bool:
    return abs(v) < 0.000001


def is_same_float(v1: float, v2: float) -> bool:
    return is_zero_float(v1 - v2)


def normalize_float_3d(vec: Tuple[float, float, float]) -> Tuple[float, float, float]:
    digits = 6
    return (round(vec[0], digits), round(vec[1], digits), round(vec[2], digits))


def normalize_float_4d(vec: Tuple[float, float, float, float]) -> Tuple[float, float, float, float]:
    digits = 6
    return (
        round(vec[0], digits),
        round(vec[1], digits),
        round(vec[2], digits),
        round(vec[3], digits),
    )


def arrange_shapekeys(obj: bpy.types.Object, shapekeys: List[str]) -> ShapekeyChangeReport:
    report: ShapekeyChangeReport = {
        ShapekeyChangeType.ADDED: [],
        ShapekeyChangeType.DELETED: [],
        ShapekeyChangeType.INDEX_CHANGED: [],
        ShapekeyChangeType.RENAMED: [],
        ShapekeyChangeType.WEIGHT_RESET: [],
    }

    keys = ["Basis"] + shapekeys
    mesh: bpy.types.Mesh = obj.data

    modified_keys = set()

    # 0. Add Basis key if there's no b/s keys at all
    if mesh.shape_keys is None:
        shapekey = obj.shape_key_add(name="Basis")
        shapekey.interpolation = "KEY_LINEAR"
        report[ShapekeyChangeType.ADDED].append(ShapekeyChangeDetail("Basis", "Added"))
        modified_keys.add("Basis")
    key_to_original_index = {key.name: idx for idx, key in enumerate(mesh.shape_keys.key_blocks)}

    # 1. Rename shapekey names if wrong upper/lower case
    def norm(s: str):
        s = s.rsplit(".", 1)[-1]

        t_idx = len(s) - 1
        for idx in range(t_idx, -1, -1):
            if s[idx] not in "0123456789":
                break
            t_idx -= 1

        s = s[: t_idx + 1]

        return "".join(s.lower().split("_"))

    norm_to_keyname = {norm(k): k for k in keys}

    for shapekey in mesh.shape_keys.key_blocks:
        original_key = shapekey.name
        norm_original_key = norm(shapekey.name)
        patched_key = norm_to_keyname.get(norm_original_key, shapekey.name)

        if original_key != patched_key:
            shapekey.name = patched_key
            report[ShapekeyChangeType.RENAMED].append(
                ShapekeyChangeDetail(original_key, f"Renamed to [{patched_key}]")
            )
            modified_keys.add(patched_key)

    # 2. Add missing shapekeys
    keyname_to_shapekey = {shapekey.name: shapekey for shapekey in mesh.shape_keys.key_blocks}
    current_keys = set(keyname_to_shapekey.keys())
    real_keys = set(keys)

    missing_keys = real_keys - current_keys
    unknown_keys = current_keys - real_keys

    for key in missing_keys:
        shapekey = obj.shape_key_add(name=key)
        shapekey.interpolation = "KEY_LINEAR"
        report[ShapekeyChangeType.ADDED].append(ShapekeyChangeDetail(key, "Added"))
        modified_keys.add(key)

    # 3. Delete unknown shapekeys
    for key in unknown_keys:
        obj.shape_key_remove(keyname_to_shapekey[key])
        report[ShapekeyChangeType.DELETED].append(ShapekeyChangeDetail(key, "Deleted"))
        modified_keys.add(key)

    # 4. Sort keys
    bpy.context.view_layer.objects.active = obj
    skeys = mesh.shape_keys.key_blocks

    # NOTE: This loop takes a while.
    for name in keys:
        idx = skeys.keys().index(name)
        obj.active_shape_key_index = idx
        bpy.ops.object.shape_key_move(type="BOTTOM")

    for idx, key in enumerate(mesh.shape_keys.key_blocks):
        original_idx = key_to_original_index.get(key.name, -1)
        if idx != original_idx and (not key.name in modified_keys):
            report[ShapekeyChangeType.INDEX_CHANGED].append(
                ShapekeyChangeDetail(key.name, f"Index changed [{original_idx} -> {idx}]")
            )

    # 5. Set all weights to 0
    for shapekey in mesh.shape_keys.key_blocks:
        if shapekey.value != 0:
            original_value = shapekey.value
            shapekey.value = 0
            report[ShapekeyChangeType.WEIGHT_RESET].append(
                ShapekeyChangeDetail(shapekey.name, f"Weight reset [{original_value} -> 0]")
            )

    return report
