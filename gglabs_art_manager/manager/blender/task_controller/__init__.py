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

__all__ = ["TaskTypeToViewControllers"]
