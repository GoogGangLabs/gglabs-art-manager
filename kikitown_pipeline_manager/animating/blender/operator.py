import bpy

from kikitown_pipeline_manager.animating.blender.property_group import KPM_PGT_Animating


class KPM_OT_Animating(bpy.types.Operator):
    bl_idname = "kikitown_pipeline_manager.animating"
    bl_label = "Do something automating for animating work"
    # TODO: Write description in korean
    bl_description = "--"
    bl_options = {"REGISTER", "UNDO"}

    def execute(self, context):
        accessor = KPM_PGT_Animating
        accessor.setattr("sample_str", "")

        return {"FINISHED"}

    def invoke(self, context, event):
        return context.window_manager.invoke_confirm(self, event)
