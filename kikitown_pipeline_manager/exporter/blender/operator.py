import bpy
from bpy_extras.io_utils import ExportHelper

from kikitown_pipeline_manager.exporter.blender.property_group import KPM_PGT_Exporter


class KPM_OT_Exporter(bpy.types.Operator, ExportHelper):
    bl_idname = "kikitown_pipeline_manager.exporter"
    bl_label = "Export kikitown art resources"
    # TODO: Write description in korean
    bl_description = "--"
    bl_options = {"REGISTER", "UNDO"}
    filename_ext = ".qq"

    def execute(self, context):
        accessor = KPM_PGT_Exporter
        accessor.setattr("sample_str", "")

        return {"FINISHED"}
