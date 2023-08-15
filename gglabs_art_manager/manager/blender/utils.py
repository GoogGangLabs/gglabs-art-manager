from typing import List

import bpy
from blender_validator import TaskType
from blender_validator.utils import (
    is_armature_collection,
    is_common_collection,
    is_main_collection,
    is_same_strkey,
    main_collection,
    set_visibility_of_collection,
    set_visibility_of_object,
    strkey,
)


def control_visibilities_for_tasktype(task_type: str, shapekey_categories: List[str]):
    shapekey_category_strkeys = [strkey(category) for category in shapekey_categories]

    # 0. Turn off rendering options for the objects directly dangled to the scene collection.
    for obj in bpy.context.scene.collection.objects:
        set_visibility_of_object(obj, False)

    # 1.1 Turn off all collections but main > common
    for collection in bpy.context.scene.collection.children:
        if is_main_collection(collection):
            for subcol in collection.children:
                if is_common_collection(subcol):
                    set_visibility_of_collection(
                        subcol, True, with_layer_collection=True
                    )
                else:
                    set_visibility_of_collection(
                        subcol, False, with_layer_collection=True
                    )
        else:
            set_visibility_of_collection(collection, False, with_layer_collection=True)

    # 3.1. Face Rigging; Facial Meshes w/ blendshape keys
    if task_type in [TaskType.FACE_RIGGING.name]:
        for collection in main_collection().children:
            # Hide Armature Collection
            if is_common_collection(collection):
                for subcol in collection.children:
                    if is_armature_collection(subcol):
                        set_visibility_of_collection(
                            collection, False, with_layer_collection=True
                        )

            # Show Shapekey Meshes
            elif strkey(collection) in shapekey_category_strkeys:
                set_visibility_of_collection(
                    collection, True, with_layer_collection=True
                )

                if is_same_strkey(collection, "type"):
                    for obj in list(collection.all_objects):
                        if obj.type == "MESH" and strkey(obj).startswith("body_"):
                            set_visibility_of_object(obj, False)

            else:
                set_visibility_of_collection(
                    collection, False, with_layer_collection=True
                )

    # 3.2. Animating; Facial Meshes & Armature w/ Action data & blendshape keys (No NLA Tracks)
    elif task_type in [TaskType.ANIMATING.name]:
        for collection in main_collection().children:
            if is_common_collection(collection):
                pass

            elif strkey(collection) in shapekey_category_strkeys:
                set_visibility_of_collection(
                    collection, True, with_layer_collection=True
                )

                if is_same_strkey(collection, "type"):
                    for obj in list(collection.all_objects):
                        if obj.type == "MESH" and strkey(obj).startswith("body_"):
                            obj.hide_render = True
            else:
                set_visibility_of_collection(
                    collection, False, with_layer_collection=True
                )
