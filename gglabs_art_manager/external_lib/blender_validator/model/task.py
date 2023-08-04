from enum import Enum


class TaskType(Enum):
    ANY = ""
    FACE_MODELING = "Face Modeling & Texturing"
    FACE_RIGGING = "Face Rigging"
    BODY_MODELING = "Body Modeling & Texturing"
    BODY_RIGGING = "Body Rigging"
    ANIMATING = "Animating"
    MASTERING = "Avatar & Parts Mastering"

    @classmethod
    def from_str(cls, s: str) -> "TaskType":
        for task_type in cls:
            if task_type.name == s:
                return task_type

        return TaskType.ANY
        