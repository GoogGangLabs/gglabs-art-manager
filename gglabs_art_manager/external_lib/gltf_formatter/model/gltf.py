# Monkey Patching pygltflib classes
# pylint: disable=wrong-import-order
from dataclasses import dataclass, field
from typing import List, Optional

import pygltflib
from dataclasses_json import dataclass_json


@dataclass_json
@dataclass
class MonkeyMaterial(pygltflib.Material):
    alphaMode: Optional[str] = None  # OPAQUE
    alphaCutoff: Optional[float] = None  # 0.5


class MonkeyGLTF2(pygltflib.GLTF2):
    materials: List[MonkeyMaterial] = field(default_factory=list)


GLTF2 = MonkeyGLTF2

__all__ = ["GLTF2"]
