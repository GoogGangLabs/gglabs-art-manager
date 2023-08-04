import bpy

from gglabs_art_manager.manager.blender.operator import (
    GAM_OT_ExportGLB,
    GAM_OT_Reset,
    GAM_OT_ValidateBlender,
)
from gglabs_art_manager.manager.blender.panel import GAM_PT_Main
from gglabs_art_manager.manager.blender.property_group import GAM_PGT_Main

__all__ = [
    "register",
    "unregister",
]

_GAM_CLASSES = (
    # Property Groups
    GAM_PGT_Main,
    # Operators
    GAM_OT_ExportGLB,
    GAM_OT_ValidateBlender,
    GAM_OT_Reset,
    # Panels
    GAM_PT_Main,
)


def register():
    for cls in _GAM_CLASSES:
        bpy.utils.register_class(cls)

    GAM_PGT_Main.register_property_group()


def unregister():
    for cls in reversed(_GAM_CLASSES):
        try:
            bpy.utils.unregister_class(cls)
        except RuntimeError:
            pass

    GAM_PGT_Main.unregister_property_group()
