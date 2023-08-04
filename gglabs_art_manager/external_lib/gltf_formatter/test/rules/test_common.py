import os
import unittest
from typing import Dict

from gltf_formatter.model import GLTF2, RuleType

# pylint: disable=wildcard-import,unused-wildcard-import
from gltf_formatter.rules.common import *

DIR_PATH = os.path.dirname(os.path.realpath(__file__))
TEST_GLTF_DIR = f"{DIR_PATH}/gltf"


def load_test_gltf(cls: RuleType) -> GLTF2:
    return GLTF2.load(f"{DIR_PATH}/gltf/test_{cls.name()}.gltf")


def patched_gltf(cls: RuleType) -> GLTF2:
    return cls.apply(load_test_gltf(cls))


class TestCommonRules(unittest.TestCase):
    def test_ReplaceMeshNamesWithColNamesRule(self):
        patched = patched_gltf(ReplaceMeshNamesWithColNamesRule)
        node = patched.nodes[0]
        self.assertEqual("PATCHED_NODE_NAME", node.name)
        self.assertEqual("ORIGINAL_MESH_NAME", node.extras["blender"]["mesh_name"])
        self.assertEqual("ORIGINAL_NODE_NAME", node.extras["blender"]["object_name"])

    def test_CleanupUnusedExtraRule(self):
        patched = patched_gltf(CleanupUnusedExtraRule)

        self.assertEqual(0, len(patched.scenes[0].extras))
        self.assertEqual(1, len(patched.nodes[0].extras))
        self.assertTrue("blender_important_data" in patched.nodes[0].extras)
        self.assertEqual(1, len(patched.meshes[0].extras))
        self.assertTrue("blender_important_data" in patched.meshes[0].extras)

    def test_CleanupUnusedTexcoordRule(self):
        original = load_test_gltf(CleanupUnusedTexcoordRule)
        attrmap: Dict[str, int] = json.loads(original.meshes[0].primitives[0].attributes.to_json())
        uv_map_accessors = [idx for idx, acc in enumerate(original.accessors) if acc.type == "VEC2"]

        self.assertIsNotNone(attrmap.get("TEXCOORD_0"))
        self.assertIsNotNone(attrmap.get("TEXCOORD_1"))
        self.assertIsNotNone(attrmap.get("TEXCOORD_2"))
        self.assertEqual(3, len(uv_map_accessors))

        patched = patched_gltf(CleanupUnusedTexcoordRule)
        attrmap: Dict[str, int] = json.loads(patched.meshes[0].primitives[0].attributes.to_json())
        uv_map_accessors = [idx for idx, acc in enumerate(patched.accessors) if acc.type == "VEC2"]

        self.assertIsNone(attrmap.get("TEXCOORD_0"))
        self.assertIsNone(attrmap.get("TEXCOORD_1"))
        self.assertIsNone(attrmap.get("TEXCOORD_2"))
        self.assertEqual(0, len(uv_map_accessors))
        self.assertEqual(3, len(original.bufferViews) - len(patched.bufferViews))

    def test_ReplaceBeergangNameWithStandardNameRule(self):
        patched = patched_gltf(ReplaceBeergangNameWithStandardNameRule)
        self.assertEqual("Head_Brows", patched.nodes[0].name)
        self.assertEqual("Head_Brows_1", patched.nodes[1].name)
        self.assertEqual("Prop_Eyewear", patched.nodes[2].name)
