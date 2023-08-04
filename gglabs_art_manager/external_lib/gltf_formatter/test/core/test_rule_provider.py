import unittest

import pytest

from gltf_formatter.core import RuleProvider
from gltf_formatter.exception import RuleValidateError
from gltf_formatter.model import GLTF2, Rule, TargetResourceType
from gltf_formatter.rules import common


class DummyRule(Rule):
    @classmethod
    def apply(cls, gltf: GLTF2) -> GLTF2:
        return gltf


class Dummy1stRule(DummyRule):
    upstreams = []


class Dummy2ndRule(DummyRule):
    upstreams = [Dummy1stRule]


class Dummy3rdRule(DummyRule):
    upstreams = [Dummy2ndRule]


class Dummy4thRule(DummyRule):
    upstreams = [Dummy3rdRule, Dummy2ndRule]


class Dummy5thRule(DummyRule):
    upstreams = [Dummy4thRule, Dummy3rdRule]


class DownstreamToCommonRule(DummyRule):
    upstreams = [common.ReplaceMeshNamesWithColNamesRule, Dummy1stRule]


class TestRuleProvider(unittest.TestCase):
    def test_rule_arrangement(self):
        # Shuffling intentionally
        rule_classes = [
            Dummy2ndRule,
            Dummy5thRule,
            Dummy4thRule,
            Dummy3rdRule,
            Dummy1stRule,
        ]

        rp = RuleProvider(
            TargetResourceType.ANY,
            custom_rules=rule_classes,
            contain_default_rules=False,
        )

        self.assertListEqual(
            [Dummy1stRule, Dummy2ndRule, Dummy3rdRule, Dummy4thRule, Dummy5thRule],
            list(rp),
        )
        self.assertTrue(rp.check_arranged())

    def test_dangling_upstream(self):
        with pytest.raises(RuleValidateError):
            rule_classes = [
                Dummy1stRule,
                Dummy3rdRule,
            ]
            _ = RuleProvider(
                TargetResourceType.ANY,
                custom_rules=rule_classes,
                contain_default_rules=False,
            )

    def test_custom_rules_with_default_rules(self):
        rule_classes = [Dummy1stRule, DownstreamToCommonRule]

        rp = RuleProvider(
            TargetResourceType.ANY,
            custom_rules=rule_classes,
            contain_default_rules=True,
        )

        rule_order = {rule.name(): idx for idx, rule in enumerate(rp)}

        def order(r: Rule) -> int:
            return rule_order[r.name()]

        self.assertLess(order(common.CleanupUnusedExtraRule), order(DownstreamToCommonRule))
        self.assertLess(order(Dummy1stRule), order(DownstreamToCommonRule))
        self.assertTrue(rp.check_arranged())
