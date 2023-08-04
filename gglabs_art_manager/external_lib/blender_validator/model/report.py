from dataclasses import dataclass
from enum import Enum
from typing import Dict, List


class ShapekeyChangeType(Enum):
    ADDED = 0
    DELETED = 1
    INDEX_CHANGED = 2
    RENAMED = 3
    WEIGHT_RESET = 4


@dataclass
class ShapekeyChangeDetail:
    key: str
    detail: str


ShapekeyChangeReport = Dict[ShapekeyChangeType, List[ShapekeyChangeDetail]]


class BaseLogger:
    def open(self):
        pass

    def log(self, s: str):
        pass

    def close(self):
        pass


class StdoutLogger(BaseLogger):
    def log(self, s: str):
        print(s)
