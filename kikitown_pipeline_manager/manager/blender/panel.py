from typing import Optional

import bpy

from kikitown_pipeline_manager.manager.blender.operator import (
    KPM_OT_ExportGLB,
    KPM_OT_Reset,
    KPM_OT_ValidateBlender,
)
from kikitown_pipeline_manager.manager.blender.property_group import KPM_PGT_Main

CHARS_TO_PIXEL = {
    "abdeghknopquvxy": 12.9,
    "ckszFL": 11.8,
    "mW": 20.9,
    "wM": 17.8,
    "r": 8.9,
    "t": 7.8,
    "f": 6.8,
    "ijlIJ": 5.8,
    "OQG": 16.8,
    "DHUN": 15.8,
    "ABCRVXZ": 14.8,
    "EPSTY": 12.8,
    "_": 10.9,
    " ": 6.25,
    "0123456789K": 13.8,
}
CHAR_TO_PIXEL = {ch: v for k, v in CHARS_TO_PIXEL.items() for ch in k}
KOR_TO_PIXEL = 19.9
PADDING_PIXEL = 130  # 111


def _add_multiline_label(context: bpy.types.Context, text: str, view: bpy.types.UILayout):
    width = context.region.width

    cur_width = PADDING_PIXEL
    strbuilder = ""

    for ch in text:
        if ch == "\n" and len(strbuilder) > 0:
            view.label(text=strbuilder)
            strbuilder = ""
            cur_width = PADDING_PIXEL
        else:
            strbuilder += ch
            cur_width += CHAR_TO_PIXEL.get(ch, KOR_TO_PIXEL)

            if cur_width >= width:
                view.label(text=strbuilder)
                strbuilder = ""
                cur_width = PADDING_PIXEL

    if len(strbuilder) > 0:
        view.label(text=strbuilder)


class KPM_PT_Main(bpy.types.Panel):
    bl_label = "Kikitown Task Manager"
    bl_idname = "KPM_PT_Main"
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
        params = KPM_PGT_Main.getprops()

        layout.row().separator()
        layout.operator(
            KPM_OT_Reset.bl_idname,
            icon="CANCEL",
            text="입력 데이터 초기화",
        )
        layout.row()

        self.draw_filepath_row(layout, params, "작업 프로젝트", "project_type", icon_only=False)
        self.draw_filepath_row(layout, params, "작업 단계", "task_type", icon_only=False)
        self.draw_filepath_row(
            layout,
            params,
            "유효성 검사 설정 파일",
            "config_filepath",
            "config_loaded_message",
        )
        self.draw_filepath_row(
            layout,
            params,
            "GLB 생성 경로",
            "output_dirpath",
        )
        layout.row().separator()

        layout.operator(
            KPM_OT_ValidateBlender.bl_idname,
            icon="TRACKING_FORWARDS",
            text="Blender 파일 유효성 검사 및 보정하기",
        )

        _add_multiline_label(context, getattr(params, "blender_validated_message"), layout)

        is_ready: bool = getattr(params, "is_blender_validated")
        if is_ready:
            layout.row().separator()
            layout.operator(
                KPM_OT_ExportGLB.bl_idname,
                icon="RENDER_STILL",
                text="GLB 생성하기",
            )

        layout.row()
