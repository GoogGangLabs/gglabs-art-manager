from typing import Dict, List

import bpy
from blender_validator import TaskType

from gglabs_art_manager.blender.utils import (
    construct_layer_collections,
    is_armature_collection,
    is_collection_included_to_viewlayer,
    is_common_collection,
    is_main_collection,
    main_collection,
    set_visibility_of_collection,
    set_visibility_of_layer_collection,
)


def construct_category_to_colname() -> Dict[str, str]:
    categories = [c.name for c in main_collection().children if c.name.lower() != "common"]
    return {c.lower(): c for c in categories}


def construct_pid_to_colname() -> Dict[str, str]:
    pids = [
        pid_col.name
        for category_col in bpy.context.scene.collection.children
        if category_col.name.lower() != "common"
        for pid_col in category_col.children
    ]
    return {p.lower(): p for p in pids}


def construct_nstring_to_collection() -> Dict[str, bpy.types.Collection]:
    return {
        **{category_col.name.lower(): category_col for category_col in main_collection().children},
        **{
            parts_col.name.lower(): parts_col
            for category_col in main_collection().children
            for parts_col in category_col.children
        },
    }


def control_visibilities_for_tasktype(task_type: str, shapekey_categories: List[str]):
    shapekey_categories_norm = [category.lower() for category in shapekey_categories]
    layer_collections = construct_layer_collections()

    # 1.1 Turn off all collections but main > common
    for collection in bpy.context.scene.collection.children:
        if is_main_collection(collection):
            for subcol in collection.children:
                if is_common_collection(subcol):
                    set_visibility_of_collection(subcol, True, with_layer_collection=True)
                else:
                    set_visibility_of_collection(subcol, False, with_layer_collection=True)
        else:
            set_visibility_of_collection(collection, False, with_layer_collection=True)

    # 3.1. Face Rigging; Facial Meshes w/ blendshape keys
    if task_type in [TaskType.FACE_RIGGING.name]:
        for collection in main_collection().children:
            if not is_collection_included_to_viewlayer(collection, layer_collections):
                set_visibility_of_collection(collection, False)

            # Hide Armature Collection
            elif is_common_collection(collection):
                for subcol in collection.children:
                    if is_armature_collection(subcol):
                        set_visibility_of_collection(collection, False, with_layer_collection=True)

            # Show Shapekey Meshes
            elif collection.name.lower() in shapekey_categories_norm:
                set_visibility_of_collection(collection, True, with_layer_collection=True)

                if collection.name.lower() == "type":
                    for obj in collection.all_objects:
                        if obj.type == "MESH" and obj.name.lower().startswith("body_"):
                            obj.hide_render = True

            else:
                set_visibility_of_collection(collection, False, with_layer_collection=True)

    # 3.2. Animating; Facial Meshes & Armature w/ Action data & blendshape keys (No NLA Tracks)
    elif task_type in [TaskType.ANIMATING.name]:
        for collection in main_collection().children:
            if not is_collection_included_to_viewlayer(collection, layer_collections):
                set_visibility_of_collection(collection, False)

            elif collection.name.lower() in shapekey_categories_norm:
                set_visibility_of_collection(collection, True, with_layer_collection=True)

                if collection.name.lower() == "type":
                    for obj in collection.all_objects:
                        if obj.type == "MESH" and obj.name.lower().startswith("body_"):
                            obj.hide_render = True
            else:
                set_visibility_of_collection(collection, False, with_layer_collection=True)
