import os
import unittest

from gltf_formatter.model import GLTF2, RuleType

# pylint: disable=wildcard-import,unused-wildcard-import
from gltf_formatter.rules.avatar import *

DIR_PATH = os.path.dirname(os.path.realpath(__file__))
TEST_GLTF_DIR = f"{DIR_PATH}/gltf"


def load_test_gltf(cls: RuleType) -> GLTF2:
    return GLTF2.load(f"{DIR_PATH}/gltf/test_{cls.name()}.gltf")


def patched_gltf(cls: RuleType) -> GLTF2:
    return cls.apply(load_test_gltf(cls))


class TestAvatarRules(unittest.TestCase):
    def test_RegisterShapeKeyInfoToExtraRule(self):
        # not implemented yet
        pass
