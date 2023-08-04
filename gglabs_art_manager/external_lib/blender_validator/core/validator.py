from types import ModuleType
from typing import Any, Dict, Iterable, Optional, Union

import bpy

from blender_validator.core.rule_provider import RuleProvider
from blender_validator.exception import BlenderValidateError
from blender_validator.model import BaseLogger, RuleConstants, RuleType, TaskType
from blender_validator.rules.utils import construct_layer_collections, main_collection


class BlenderValidator:
    def __init__(
        self,
        task_type: TaskType,
        rule_constants: RuleConstants,
        custom_rules: Optional[Union[ModuleType, Iterable[RuleType], Iterable[ModuleType]]] = None,
        use_default_rules: bool = True,
        exclude_rules: Optional[Iterable[RuleType]] = None,
        strict_mode: bool = False,
        logger: Optional[BaseLogger] = None,
    ):
        self.rules = RuleProvider(
            task_type,
            custom_rules=custom_rules,
            contain_default_rules=use_default_rules,
            exclude_rules=exclude_rules,
        )
        self.strict_mode = strict_mode
        self.rule_constants = rule_constants
        self.task_type = task_type
        self.logger = logger or BaseLogger()

        self.context: Dict[str, Any] = {}

    def init_context(self):
        active_object = bpy.context.active_object
        self.context = {
            "active_object": active_object,
            "selected_objects": bpy.context.selected_objects,
            "active_shape_key_index": active_object.active_shape_key_index
            if active_object is not None
            else None,
            "active_material_index": active_object.active_material_index
            if active_object is not None
            else None,
        }

        # deactivate object
        bpy.context.view_layer.objects.active = None

        # deselected objects
        for obj in bpy.context.selectable_objects:
            obj.select_set(False)

        # Objects hidden
        visible_map = {}
        for obj in list(main_collection().all_objects):
            visible_map[obj.name] = obj.hide_get()
            try:
                obj.hide_set(False)
            except RuntimeError:
                pass
        self.context["objects_hide_get"] = visible_map

        # Objects hide_viewport
        visible_map = {}
        for obj in list(main_collection().all_objects):
            visible_map[obj.name] = obj.hide_viewport
            obj.hide_viewport = False
        self.context["objects_hide_viewport"] = visible_map

        # Collections hide_viewport
        visible_map = {}
        for col in bpy.data.collections:
            visible_map[col.name] = col.hide_viewport
            col.hide_viewport = False
        self.context["collections_hide_viewport"] = visible_map

        # LayerCollections hide_viewport
        visible_map = {}
        for colname, col in construct_layer_collections().items():
            visible_map[colname] = col.hide_viewport
            col.hide_viewport = False
        self.context["layer_collections_hide_viewport"] = visible_map

        return True

    def rollback_context(self):
        original_object: bpy.types.Object = self.context["active_object"]

        # re-activate object
        bpy.context.view_layer.objects.active = original_object

        # re-select objects
        for obj in self.context["selected_objects"]:
            obj.select_set(True)

        # activate object indexes
        if original_object is not None:
            original_object.active_material_index = self.context["active_material_index"]
            original_object.active_shape_key_index = self.context["active_shape_key_index"]

        # LayerCollections hide_viewport
        layer_collections = construct_layer_collections()
        for colname, is_hide_viewport in self.context["layer_collections_hide_viewport"].items():
            layer_collections[colname].hide_viewport = is_hide_viewport

        # Collections hide_viewport
        for colname, is_hide_viewport in self.context["collections_hide_viewport"].items():
            bpy.data.collections[colname].hide_viewport = is_hide_viewport

        # Objects hide_viewport
        for objname, is_hide_viewport in self.context["objects_hide_viewport"].items():
            bpy.data.objects[objname].hide_viewport = is_hide_viewport

        # Objects hidden
        for objname, is_hidden in self.context["objects_hide_get"].items():
            try:
                bpy.data.objects[objname].hide_set(is_hidden)
            except RuntimeError:
                pass

        return True

    def validate(self) -> bool:
        res = True

        for rule in self.rules:
            self.init_context()
            try:
                res &= rule.validate(self.rule_constants, self.task_type, self.logger)
            except BlenderValidateError as e:
                message = f"--- [{rule.name()}] Report ---\n{str(e)}"
                raise BlenderValidateError(message) from e
            finally:
                self.rollback_context()

        return res

    def validate_and_fix(self) -> bool:
        res = True

        for rule in self.rules:
            self.init_context()
            try:
                is_valid = rule.validate(self.rule_constants, self.task_type, self.logger)
            except BlenderValidateError as e:
                message = f"--- [{rule.name()}] Error Report ---\n{str(e)}"
                self.logger.log(message)
                self.rollback_context()
                raise BlenderValidateError(message) from e

            if not is_valid:
                self.logger.log(f"--- [{rule.name()}] Fix Report ---")
                res &= rule.fix(self.rule_constants, self.task_type, self.logger)

            self.rollback_context()

        return res
