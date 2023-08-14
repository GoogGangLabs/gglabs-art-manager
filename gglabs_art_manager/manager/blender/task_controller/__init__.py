from typing import Dict, List, Union

from blender_validator.model import TaskType

from gglabs_art_manager.blender import TaskControlView
from gglabs_art_manager.manager.blender.task_controller.shapekey import (
    ShapekeyControlPanel,
)

_TaskTypeToViewControllers: Dict[TaskType, List[TaskControlView]] = {
    TaskType.FACE_MODELING: [],
    TaskType.FACE_RIGGING: [ShapekeyControlPanel],
    TaskType.BODY_MODELING: [],
    TaskType.BODY_RIGGING: [],
    TaskType.ANIMATING: [ShapekeyControlPanel],
    TaskType.MASTERING: [ShapekeyControlPanel],
}

TaskTypeToViewControllers: Dict[Union[TaskType, str], List[TaskControlView]] = {
    **_TaskTypeToViewControllers,
    **{k.name: v for k, v in _TaskTypeToViewControllers.items()},
}


def reset_task_controllers():
    controllers = {
        control_view.__str__: control_view
        for control_views in _TaskTypeToViewControllers.values()
        for control_view in control_views
    }.values()

    for cv in controllers:
        cv.reset()


__all__ = ["TaskTypeToViewControllers", "reset_task_controllers"]
