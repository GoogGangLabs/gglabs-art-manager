import bpy

from kikitown_pipeline_manager.manager.blender.operator import (
    KPM_OT_ExportGLB,
    KPM_OT_Reset,
    KPM_OT_ValidateBlender,
)
from kikitown_pipeline_manager.manager.blender.panel import KPM_PT_Main
from kikitown_pipeline_manager.manager.blender.property_group import KPM_PGT_Main

__all__ = [
    "register",
    "unregister",
]

_KPM_CLASSES = (
    # Property Groups
    KPM_PGT_Main,
    # Operators
    KPM_OT_ExportGLB,
    KPM_OT_ValidateBlender,
    KPM_OT_Reset,
    # Panels
    KPM_PT_Main,
)


def register():
    for cls in _KPM_CLASSES:
        bpy.utils.register_class(cls)

    KPM_PGT_Main.register_property_group()


def unregister():
    for cls in reversed(_KPM_CLASSES):
        try:
            bpy.utils.unregister_class(cls)
        except RuntimeError:
            pass

    KPM_PGT_Main.unregister_property_group()
