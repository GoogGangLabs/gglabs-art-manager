from typing import Optional

import bpy

from kikitown_pipeline_manager.animating.blender.operator import KPM_OT_Animating
from kikitown_pipeline_manager.animating.blender.property_group import KPM_PGT_Animating


class KPM_PT_Animating(bpy.types.Panel):
    bl_label = "Animating Task"
    bl_idname = "KPM_PT_Animating"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_category = "Kikitown Pipeline Manager"

    def draw_filepath_row(
        self,
        layout: bpy.types.UILayout,
        params: bpy.types.PropertyGroup,
        text: str,
        prop: str,
        message_prop: Optional[str] = None,
        icon_only: bool = True,
    ):
        row = layout.row()

        split = row.split(factor=0.4)
        left = split.column(align=True)
        left.alignment = "RIGHT"
        left.label(text=f"{text}:")

        right = split.column()
        right.prop(params, prop, icon_only=icon_only)

        if message_prop and getattr(params, message_prop):
            row = layout.row()
            split = row.split(factor=1.0)
            col = split.column(align=True)
            col.alignment = "RIGHT"
            col.label(text=getattr(params, message_prop))

    def draw(self, context):
        layout = self.layout
        params = KPM_PGT_Animating.getprops()

        layout.row().separator()
        box = layout.box()
        box.row().prop(params, "sample_str")
        box.row().prop(params, "sample_bool")

        layout.row().label(text="Hello")

        self.draw_filepath_row(box, params, "Your Choice", "sample_choice", icon_only=False)

        layout.row().separator()
        layout.operator(
            KPM_OT_Animating.bl_idname,
            icon="META_DATA",
            text="Go!",
        )

        layout.row()
