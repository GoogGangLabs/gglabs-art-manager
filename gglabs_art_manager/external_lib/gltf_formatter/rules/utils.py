import json
from collections import Counter
from typing import Counter as CounterType
from typing import Union

from pygltflib import Accessor, AccessorSparseIndices, AccessorSparseValues, Image

from gltf_formatter.model import GLTF2

BufferViewable = Union[Accessor, AccessorSparseIndices, AccessorSparseValues, Image]


# Returns {${accessor_idx_1}: ${the number of being referenced}, ...}
def accessor_reference_counter(gltf: GLTF2) -> CounterType[int]:
    refcnt = Counter()

    # check all meshes
    for mesh in gltf.meshes:
        for prim in mesh.primitives:
            # check all mesh attributes (POSITION, NORMAL, ..)
            attrmap = json.loads(prim.attributes.to_json())
            for accessor_idx in attrmap.values():
                if accessor_idx is not None:
                    refcnt[accessor_idx] += 1

            # check all mesh indices
            if prim.indices is not None:
                refcnt[prim.indices] += 1

            # check all mesh shapekey targets
            for target in prim.targets or []:
                for accessor_idx in target.values():
                    if accessor_idx is not None:
                        refcnt[accessor_idx] += 1

    # check all animation samplers
    for animation in gltf.animations:
        for sampler in animation.samplers:
            refcnt[sampler.input] += 1
            refcnt[sampler.output] += 1

    # check all skins
    for skin in gltf.skins:
        if skin.inverseBindMatrices is not None:
            refcnt[skin.inverseBindMatrices] += 1

    return refcnt


# Returns {${bufferview_idx_1}: ${the number of being referenced}, ...}
def bufferview_reference_counter(gltf: GLTF2) -> CounterType[int]:
    refcnt = Counter()

    # check all accessors
    for accessor in gltf.accessors:
        if accessor.bufferView is not None:
            refcnt[accessor.bufferView] += 1
        if accessor.sparse is not None:
            refcnt[accessor.sparse.indices.bufferView] += 1
            refcnt[accessor.sparse.values.bufferView] += 1

    # check all images (for binary glTF)
    for image in gltf.images:
        if image.bufferView is not None:
            refcnt[image.bufferView] += 1

    return refcnt


# Remove the given bufferview and update all pointers to bufferviews safely.
def remove_bufferview(gltf: GLTF2, target_idx: int):
    gltf.bufferViews.pop(target_idx)

    def update_obj(obj: BufferViewable):
        if (obj is not None) and (obj.bufferView is not None):
            if obj.bufferView >= target_idx:
                obj.bufferView -= 1

    for accessor in gltf.accessors:
        update_obj(accessor)
        if (accessor is not None) and (accessor.sparse is not None):
            update_obj(accessor.sparse.indices)
            update_obj(accessor.sparse.values)

    for image in gltf.images:
        update_obj(image)


# Remove the given accessor and update all pointers to accessors safely.
def remove_accessor(gltf: GLTF2, target_idx: int):
    gltf.accessors.pop(target_idx)

    # check all meshes
    for mesh in gltf.meshes:
        for prim in mesh.primitives:
            attrmap = json.loads(prim.attributes.to_json())
            patched_attrmap = {
                attr_key: accessor_idx - 1
                if accessor_idx is not None and accessor_idx >= target_idx
                else accessor_idx
                for attr_key, accessor_idx in attrmap.items()
            }

            for key, value in patched_attrmap.items():
                setattr(prim.attributes, key, value)

            if prim.indices is not None:
                if prim.indices >= target_idx:
                    prim.indices -= 1

            for target in prim.targets or []:
                for key, accessor_idx in target.items():
                    if accessor_idx is not None and accessor_idx >= target_idx:
                        target[key] -= 1

    # check all animation samplers
    for animation in gltf.animations:
        for sampler in animation.samplers:
            if sampler.input >= target_idx:
                sampler.input -= 1
            if sampler.output >= target_idx:
                sampler.output -= 1

    # check all skins
    for skin in gltf.skins:
        if skin.inverseBindMatrices is not None:
            if skin.inverseBindMatrices >= target_idx:
                skin.inverseBindMatrices -= 1
