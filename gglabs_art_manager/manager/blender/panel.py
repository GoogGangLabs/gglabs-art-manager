from typing import Optional

import bpy

from gglabs_art_manager.manager.blender.operator import (
    GAM_OT_ExportGLB,
    GAM_OT_Reset,
    GAM_OT_ValidateBlender,
)
from gglabs_art_manager.manager.blender.property_group import GAM_PGT_Main
from gglabs_art_manager.manager.blender.task_controller import TaskTypeToViewControllers
from gglabs_art_manager.version import __version__


class GAM_PT_Main(bpy.types.Panel):
    bl_label = f"GGLabs Art Manager (v{__version__})"
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

        # 1. Basic Configurations
        layout.row()
        self.draw_filepath_row(
            layout, params, "작업 프로젝트", "project_type", icon_only=False
        )
        self.draw_filepath_row(layout, params, "작업 단계", "task_type", icon_only=False)
        self.draw_filepath_row(
            layout,
            params,
            "설정 파일",
            "validate_config_filepath",
            "validate_config_loaded_message",
        )

        # 2. Additional Tools For the specific Task Type
        task_type: str = getattr(params, "task_type")
        for task_control_view in TaskTypeToViewControllers[task_type]:
            task_control_view.draw(layout.box())

        # 3. Blender Validator
        box = layout.box()
        box.operator(
            GAM_OT_ValidateBlender.bl_idname,
            icon="TRACKING_FORWARDS",
            text="Blender 파일 유효성 검사 및 보정하기",
        )
        validate_message: str = getattr(params, "blender_validated_message")
        for line in validate_message.split("\n"):
            if line.rstrip():
                box.label(text=line.rstrip())
        layout.row().separator()

        # 4. Render Options
        box = layout.box()
        self.draw_filepath_row(
            box,
            params,
            "GLB 생성 경로",
            "output_dirpath",
        )
        self.draw_filepath_row(box, params, "GLB 파일 포맷", "glb_type", icon_only=False)
        layout.row().separator()

        is_ready: bool = getattr(params, "is_validate_config_loaded")
        if is_ready:
            layout.row().separator()
            layout.operator(
                GAM_OT_ExportGLB.bl_idname,
                icon="RENDER_STILL",
                text="GLB 생성하기",
            )
        else:
            layout.label(text="GLB를 생성하기 위해서는 먼저 설정 파일이 정상적으로 로드되어야 합니다!")

        layout.row()
