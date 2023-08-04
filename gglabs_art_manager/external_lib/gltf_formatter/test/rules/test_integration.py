import unittest

from gltf_formatter.core import RuleProvider
from gltf_formatter.model import TargetResourceType


class TestRuleIntegration(unittest.TestCase):
    def setUp(self):
        self.rule_providers = [
            RuleProvider(TargetResourceType.AVATAR),
            RuleProvider(TargetResourceType.ANIMATION),
            RuleProvider(TargetResourceType.FACE),
        ]

        return super().setUp()

    def test_no_cycle(self):
        for rule_provider in self.rule_providers:
            self.assertTrue(rule_provider.validate_no_cycle())

    def test_no_dangling_rules(self):
        for rule_provider in self.rule_providers:
            self.assertTrue(rule_provider.validate_no_danglings())

    def test_no_wrong_package(self):
        for rule_provider in self.rule_providers:
            self.assertTrue(rule_provider.validate_resource_type())
