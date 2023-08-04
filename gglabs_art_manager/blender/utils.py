import unicodedata
from typing import Any, Dict, Optional, Union

import bpy

MAIN_COLLECTION = "Main"
COMMON_COLLECTION = "Common"
ARMATURE_COLLECTION = "Armature"
BACKGROUND_COLLECTION = "bg"


def main_collection() -> bpy.types.Collection:
    res = None

    for sub_col in bpy.context.scene.collection.children:
        if sub_col.name.lower() == MAIN_COLLECTION.lower():
            res = sub_col
            break

    if res is None:
        raise ValueError("현재 Main 컬렉션이 없습니다.\nScene collection 하위에 하나 만들어서 모든 파츠 데이터들을 옮겨주세요.")

    return res


def is_same_collection(
    col1: Union[bpy.types.Collection, bpy.types.LayerCollection, str],
    col2: Union[bpy.types.Collection, bpy.types.LayerCollection, str],
) -> bool:
    colname1 = (
        col1.name if isinstance(col1, (bpy.types.Collection, bpy.types.LayerCollection)) else col1
    )
    colname2 = (
        col2.name if isinstance(col2, (bpy.types.Collection, bpy.types.LayerCollection)) else col2
    )

    return colname1.lower() == colname2.lower()


def is_main_collection(col: bpy.types.Collection) -> bool:
    return is_same_collection(col, MAIN_COLLECTION)


def is_common_collection(col: bpy.types.Collection) -> bool:
    return is_same_collection(col, COMMON_COLLECTION)


def is_armature_collection(col: bpy.types.Collection) -> bool:
    return is_same_collection(col, ARMATURE_COLLECTION)


def is_background_collection(col: bpy.types.Collection) -> bool:
    return is_same_collection(col, BACKGROUND_COLLECTION)


def main_layer_collection() -> bpy.types.LayerCollection:
    res = None

    for sub_col in bpy.context.scene.view_layers[0].layer_collection.children:
        if sub_col.name.lower() == MAIN_COLLECTION.lower():
            res = sub_col
            break

    if res is None:
        raise ValueError("현재 Main 컬렉션이 없습니다.\nScene collection 하위에 하나 만들어서 모든 파츠 데이터들을 옮겨주세요.")

    return res


def remove_control_characters(s):
    return "".join(ch for ch in s if unicodedata.category(ch)[0] != "C")


def set_visibility_of_layer_collection(
    col: bpy.types.LayerCollection,
    is_shown: bool,
    with_children: bool = True,
    _is_first_call=True,
):
    col.hide_viewport = not is_shown

    if col.name == BACKGROUND_COLLECTION:
        col.hide_viewport = True

    if with_children:
        if _is_first_call:
            for obj in list(col.collection.all_objects):
                try:
                    obj.hide_set(not is_shown)
                except RuntimeError:
                    # NOTE: This happens when this comes to excluded objects
                    # There's no way to check states without catching exceptions.
                    pass

        for subcol in col.children:
            set_visibility_of_layer_collection(subcol, is_shown, with_children, False)


def set_visibility_of_collection(
    col: bpy.types.Collection,
    is_shown: bool,
    with_children: bool = True,
    with_layer_collection: bool = False,
    _is_first_call=True,
):
    # print(f"set_visibility_of_collection :: {col.name} -> {is_shown}")

    col.hide_render = not is_shown
    col.hide_viewport = not is_shown

    # ------------ NoT WORKING !!! NOT SHOWING !!!! ----------------------------1932

    # Heads-up: Iterating from `col.all_objects` directly causes an segmentation error.
    # Consider with_object option so as not to unnecessary run below codes recursively
    if with_children:
        if _is_first_call:
            for obj in list(col.all_objects):
                obj.hide_render = not is_shown
                obj.hide_viewport = not is_shown

        for subcol in col.children:
            set_visibility_of_collection(subcol, is_shown, with_children, False)

    if with_layer_collection:
        if _is_first_call:
            layer_collections = construct_layer_collections()
            set_visibility_of_layer_collection(layer_collections[col.name], is_shown, with_children)


def construct_layer_collections() -> Dict[str, bpy.types.LayerCollection]:
    ret = {}

    queue = list(bpy.context.scene.view_layers[0].layer_collection.children)
    while len(queue) > 0:
        col = queue.pop()
        ret[col.name] = col
        ret[col.name.lower()] = col

        for subcol in col.children:
            queue.append(subcol)

    return ret


def is_collection_included_to_viewlayer(
    col: Union[str, bpy.types.Collection, bpy.types.LayerCollection],
    layer_collections: Optional[Dict[str, bpy.types.LayerCollection]] = None,
) -> bool:
    if isinstance(col, bpy.types.ID):
        col_name = col.name
    else:
        col_name = col

    layer_collections = layer_collections or construct_layer_collections()

    assert col_name in layer_collections
    lc = layer_collections[col_name]
    ret = not lc.exclude

    queue = list(lc.children)
    while len(queue) > 0:
        col = queue.pop()
        ret &= not col.exclude

        for subcol in col.children:
            queue.append(subcol)

    return ret


# TODO: Introduce a data structure for the context
def save_bpy_context() -> Dict[str, Any]:
    active_object = bpy.context.active_object
    context = {
        "active_object": active_object,
        "selected_objects": bpy.context.selected_objects,
        "active_shape_key_index": active_object.active_shape_key_index
        if active_object is not None
        else None,
        "active_material_index": active_object.active_material_index
        if active_object is not None
        else None,
    }

    # deactivate object
    bpy.context.view_layer.objects.active = None

    # deselected objects
    for obj in bpy.context.selectable_objects:
        obj.select_set(False)

    # Objects hidden
    visible_map = {}
    for obj in list(main_collection().all_objects):
        visible_map[obj.name] = obj.hide_get()
        try:
            obj.hide_set(False)
        except RuntimeError:
            pass
    context["objects_hide_get"] = visible_map

    # Objects hide_viewport
    visible_map = {}
    for obj in list(main_collection().all_objects):
        visible_map[obj.name] = obj.hide_viewport
        obj.hide_viewport = False
    context["objects_hide_viewport"] = visible_map

    # Collections hide_viewport
    visible_map = {}
    for col in bpy.data.collections:
        visible_map[col.name] = col.hide_viewport
        col.hide_viewport = False
    context["collections_hide_viewport"] = visible_map

    # LayerCollections hide_viewport
    visible_map = {}
    for colname, col in construct_layer_collections().items():
        visible_map[colname] = col.hide_viewport
        col.hide_viewport = False
    context["layer_collections_hide_viewport"] = visible_map

    return context


def load_bpy_context(context: Dict[str, Any]) -> bool:
    original_object: bpy.types.Object = context["active_object"]

    # re-activate object
    bpy.context.view_layer.objects.active = original_object

    # re-select objects
    for obj in context["selected_objects"]:
        obj.select_set(True)

    # activate object indexes
    if original_object is not None:
        original_object.active_material_index = context["active_material_index"]
        original_object.active_shape_key_index = context["active_shape_key_index"]

    # LayerCollections hide_viewport
    layer_collections = construct_layer_collections()
    for colname, is_hide_viewport in context["layer_collections_hide_viewport"].items():
        layer_collections[colname].hide_viewport = is_hide_viewport

    # Collections hide_viewport
    for colname, is_hide_viewport in context["collections_hide_viewport"].items():
        bpy.data.collections[colname].hide_viewport = is_hide_viewport

    # Objects hide_viewport
    for objname, is_hide_viewport in context["objects_hide_viewport"].items():
        bpy.data.objects[objname].hide_viewport = is_hide_viewport

    # Objects hidden
    for objname, is_hidden in context["objects_hide_get"].items():
        try:
            bpy.data.objects[objname].hide_set(is_hidden)
        except RuntimeError:
            pass

    return True
