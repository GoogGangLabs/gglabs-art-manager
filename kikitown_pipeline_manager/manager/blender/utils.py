import unicodedata
from typing import Dict, List

import bpy
from blender_validator import TaskType

COMMON_COLLECTION = "common"
BACKGROUND_COLLECTION = "bg"
ALLOWED_GLTF_EXTRA_KEYS = [
    "targetNames",
    "beergangs_parts_category",
    "beergangs_parts_id",
    "beergangs_parts_name",
    "beergangs_parts_rarity",
    "morph_target_num",
    "blender_mesh",
    "blender_object",
]


def construct_bpy_category_collection() -> Dict[str, str]:
    categories = [
        c.name for c in bpy.context.scene.collection.children if c.name.lower() != "common"
    ]
    return {c.lower(): c for c in categories}


def construct_bpy_pid_collection() -> Dict[str, str]:
    pids = [
        pid_col.name
        for category_col in bpy.context.scene.collection.children
        if category_col.name.lower() != "common"
        for pid_col in category_col.children
    ]
    return {p.lower(): p for p in pids}


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
                obj.hide_set(not is_shown)
                print(f"layer {'show' if is_shown else 'hide'} :: {obj.name}")

        for subcol in col.children:
            set_visibility_of_layer_collection(subcol, is_shown, with_children, False)


def set_visibility_of_collection(
    col: bpy.types.Collection,
    is_shown: bool,
    with_children: bool = True,
    _is_first_call=True,
):
    print(f"set_visibility_of_collection :: {col.name} -> {is_shown}")

    col.hide_render = not is_shown
    # col.hide_viewport = not is_shown

    # Heads-up: Iterating from `col.all_objects` directly causes an segmentation error.
    # Consider with_object option so as not to unnecessary run below codes recursively
    if with_children:
        if _is_first_call:
            for obj in list(col.all_objects):
                obj.hide_render = not is_shown
                # obj.hide_viewport = not is_shown
                print(f"object {'show' if is_shown else 'hide'} :: {obj.name}")

        for subcol in col.children:
            set_visibility_of_collection(subcol, is_shown, with_children, False)


def control_visibilities_for_tasktype(task_type: str, shapekey_categories: List[str]):
    shapekey_categories_norm = [category.lower() for category in shapekey_categories]

    # 1. Turn off all existing collections but `common`
    for collection in bpy.context.scene.collection.children:
        if collection.name.lower() == COMMON_COLLECTION:
            set_visibility_of_collection(collection, True)
        else:
            set_visibility_of_collection(collection, False)

    # 3. Visibility control depend on task types.
    if task_type in [TaskType.FACE_MODELING.name, TaskType.FACE_RIGGING.name]:
        for collection in bpy.context.scene.collection.children:
            if collection.name.lower() in shapekey_categories_norm:
                set_visibility_of_collection(collection, True)

                if collection.name.lower() == "type":
                    for obj in collection.all_objects:
                        if obj.type == "MESH" and obj.name.lower().startswith("body_"):
                            obj.hide_render = True
            else:
                set_visibility_of_collection(collection, False)
