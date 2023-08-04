from typing import Optional

import bpy

from gglabs_art_manager.manager.blender.operator import (
    GAM_OT_ExportGLB,
    GAM_OT_Reset,
    GAM_OT_ValidateBlender,
)
from gglabs_art_manager.manager.blender.property_group import GAM_PGT_Main


class GAM_PT_Main(bpy.types.Panel):
    bl_label = "GGLabs Art Manager"
    bl_idname = "GAM_PT_Main"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_category = "GGLabs"

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
        params = GAM_PGT_Main.getprops()

        layout.row().separator()
        layout.operator(
            GAM_OT_Reset.bl_idname,
            icon="CANCEL",
            text="입력 데이터 초기화",
        )

        layout.row()
        self.draw_filepath_row(layout, params, "작업 프로젝트", "project_type", icon_only=False)
        self.draw_filepath_row(layout, params, "작업 단계", "task_type", icon_only=False)

        layout.row().separator()

        box = layout.box()
        self.draw_filepath_row(
            box,
            params,
            "유효성 검사 설정 파일",
            "validate_config_filepath",
            "validate_config_loaded_message",
        )
        box.operator(
            GAM_OT_ValidateBlender.bl_idname,
            icon="TRACKING_FORWARDS",
            text="Blender 파일 유효성 검사 및 보정하기",
        )
        validate_message: str = getattr(params, "blender_validated_message")
        for line in validate_message.split("\n"):
            box.label(text=line.rstrip())
        layout.row().separator()

        self.draw_filepath_row(
            layout,
            params,
            "GLB 생성 경로",
            "output_dirpath",
        )
        layout.row().separator()

        is_ready: bool = getattr(params, "is_blender_validated")
        if is_ready:
            layout.row().separator()
            layout.operator(
                GAM_OT_ExportGLB.bl_idname,
                icon="RENDER_STILL",
                text="GLB 생성하기",
            )

        layout.row()
