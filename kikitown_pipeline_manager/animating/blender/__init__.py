import bpy

from kikitown_pipeline_manager.animating.blender.operator import KPM_OT_Animating
from kikitown_pipeline_manager.animating.blender.panel import KPM_PT_Animating
from kikitown_pipeline_manager.animating.blender.property_group import KPM_PGT_Animating

__all__ = [
    "register",
    "unregister",
]

_KPM_CLASSES = (
    # Property Groups
    KPM_OT_Animating,
    # Operators
    KPM_PGT_Animating,
    # Panels
    KPM_PT_Animating,
)


def register():
    for cls in _KPM_CLASSES:
        bpy.utils.register_class(cls)

    KPM_PGT_Animating.register_property_group()


def unregister():
    for cls in reversed(_KPM_CLASSES):
        try:
            bpy.utils.unregister_class(cls)
        except RuntimeError:
            pass

    KPM_PGT_Animating.unregister_property_group()
