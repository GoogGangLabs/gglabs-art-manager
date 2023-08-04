import os
import unittest

from gltf_formatter.model import GLTF2, Rule

DIR_PATH = os.path.dirname(os.path.realpath(__file__))
TEST_GLTF_FILE = f"{DIR_PATH}/test_DummyRule.gltf"


class DummyRule(Rule):
    @classmethod
    def apply(cls, gltf: GLTF2) -> GLTF2:
        gltf.meshes[0].name = "Dummy"
        return gltf


class DownstreamDummyRule(Rule):
    upstreams = [DummyRule]

    @classmethod
    def apply(cls, gltf: GLTF2) -> GLTF2:
        return gltf


class TestRuleAttributes(unittest.TestCase):
    def test_rule_name(self):
        self.assertEqual(DummyRule.name(), "DummyRule")

    def test_upstream_rule_name(self):
        self.assertEqual(DownstreamDummyRule.upstreams[0].name(), "DummyRule")


class TestRuleFormat(unittest.TestCase):
    def setUp(self):
        self.gltf = GLTF2.load(TEST_GLTF_FILE)

    def test_apply(self):
        self.assertEqual("Dummy", DummyRule.apply(self.gltf).meshes[0].name)
