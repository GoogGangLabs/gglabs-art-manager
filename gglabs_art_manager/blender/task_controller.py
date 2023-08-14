from abc import ABC, abstractmethod
from typing import Iterable, Type

import bpy

from gglabs_art_manager.blender.property_group import GAM_PGT_Base


class GAM_PGT_TaskControlView(GAM_PGT_Base):
    control_enabled: bpy.types.BoolProperty


class TaskControlView(ABC):
    flag_property_key = "control_enabled"

    property_group_class: Type[GAM_PGT_TaskControlView]
    operator_classes: Iterable[Type[bpy.types.Operator]]

    @classmethod
    def getprops(cls):
        return cls.property_group_class.getprops()

    @classmethod
    def draw(cls, layout: bpy.types.UILayout):
        params = cls.property_group_class.getprops()
        layout.prop(params, cls.flag_property_key)

        is_enabled: bool = getattr(params, cls.flag_property_key)
        if is_enabled:
            cls.draw_control_view(layout)

    @classmethod
    @abstractmethod
    def draw_control_view(cls, layout: bpy.types.UILayout):
        pass

    @classmethod
    def register(cls):
        bpy.utils.register_class(cls.property_group_class)
        cls.property_group_class.register_property_group()
        for op in cls.operator_classes:
            bpy.utils.register_class(op)

    @classmethod
    def unregister(cls):
        for op in reversed(cls.operator_classes):
            try:
                bpy.utils.unregister_class(op)
            except RuntimeError:
                pass

        cls.property_group_class.unregister_property_group()
