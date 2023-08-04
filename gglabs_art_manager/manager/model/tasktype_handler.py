from dataclasses import asdict, dataclass

from blender_validator.model import TaskType
from gltf_formatter.model import TargetResourceType

# filepath
# export_format
# export_nla_strips_merged_animation_name: str = "dancetime"

# pylint: disable=too-many-instance-attributes


@dataclass
class GltfOptions:
    # Include
    use_visible: bool
    use_renderable: bool

    # Mesh
    export_apply: bool
    export_texcoords: bool
    export_normals: bool
    export_tangents: bool
    export_colors: bool
    export_attributes: bool
    use_mesh_edges: bool
    use_mesh_vertices: bool
    export_original_specular: bool  # TODO: Should Check This

    # Animation
    export_animations: bool

    # Shape keys
    export_morph: bool
    export_morph_normal: bool
    export_morph_tangent: bool

    # Skinning
    export_skins: bool

    # Default Settings
    export_yup: bool = True
    check_existing: bool = False
    export_keep_originals: bool = True
    use_active_scene: bool = True
    export_extras: bool = True

    export_animation_mode: str = "ACTIVE_ACTIONS"
    export_current_frame: bool = False
    export_frame_range: bool = True
    export_frame_step: int = 1
    export_force_sampling: bool = True
    export_nla_strips: bool = True
    export_optimize_animation_size: bool = False
    export_reset_pose_bones: bool = True

    export_all_influences: bool = False
    export_def_bones: bool = False


_TaskTypeGltfOptions = {
    TaskType.FACE_RIGGING: GltfOptions(
        # Include
        use_visible=True,
        use_renderable=False,
        # Mesh
        export_apply=False,
        export_texcoords=True,
        export_normals=True,
        export_tangents=True,
        export_colors=False,
        export_attributes=True,
        use_mesh_edges=False,
        use_mesh_vertices=False,
        export_original_specular=True,  # TODO: Should Check This
        # Animation
        export_animations=False,
        # Shape keys
        export_morph=True,
        export_morph_normal=True,
        export_morph_tangent=False,
        # Skinning
        export_skins=False,
    ),
    TaskType.ANIMATING: GltfOptions(
        # Include
        use_visible=True,
        use_renderable=False,
        # Mesh
        export_apply=False,
        export_texcoords=True,
        export_normals=True,
        export_tangents=True,
        export_colors=False,
        export_attributes=True,
        use_mesh_edges=False,
        use_mesh_vertices=False,
        export_original_specular=True,  # TODO: Should Check This
        # Animation
        export_animations=True,
        export_animation_mode="ACTIVE_ACTIONS",
        export_current_frame=False,
        export_frame_range=True,
        export_frame_step=1,
        export_force_sampling=True,
        export_nla_strips=True,
        export_optimize_animation_size=False,
        export_reset_pose_bones=True,
        # Shape keys
        export_morph=True,
        export_morph_normal=True,
        export_morph_tangent=False,
        # Skinning
        export_skins=False,
        export_all_influences=False,
        export_def_bones=False,
    ),
}

TaskTypeGltfOptions = {
    **{k: asdict(v) for k, v in _TaskTypeGltfOptions.items()},
    **{k.name: asdict(v) for k, v in _TaskTypeGltfOptions.items()},
}

_TaskTypeToTargetResourceType = {
    TaskType.FACE_MODELING: TargetResourceType.FACE,
    TaskType.FACE_RIGGING: TargetResourceType.FACE,
    TaskType.BODY_MODELING: TargetResourceType.ANY,
    TaskType.BODY_RIGGING: TargetResourceType.ANY,
    TaskType.ANIMATING: TargetResourceType.ANIMATION,
    TaskType.MASTERING: TargetResourceType.AVATAR,
}

TaskTypeToTargetResourceType = {
    **_TaskTypeToTargetResourceType,
    **{k.name: v for k, v in _TaskTypeToTargetResourceType.items()},
}
