import bpy

from kikitown_pipeline_manager.exporter.blender.operator import KPM_OT_Exporter
from kikitown_pipeline_manager.exporter.blender.property_group import KPM_PGT_Exporter

__all__ = [
    "register",
    "unregister",
]

_KPM_CLASSES = (
    # Property Groups
    KPM_PGT_Exporter,
    # Operators
    KPM_OT_Exporter,
)


def menu_func(self, context):
    self.layout.operator(KPM_OT_Exporter.bl_idname, text=KPM_OT_Exporter.bl_label)


def register():
    for cls in _KPM_CLASSES:
        bpy.utils.register_class(cls)

    bpy.types.TOPBAR_MT_file_export.append(menu_func)
    KPM_PGT_Exporter.register_property_group()


def unregister():
    for cls in reversed(_KPM_CLASSES):
        try:
            bpy.utils.unregister_class(cls)
        except RuntimeError:
            pass

    bpy.types.TOPBAR_MT_file_export.remove(menu_func)
    KPM_PGT_Exporter.unregister_property_group()
