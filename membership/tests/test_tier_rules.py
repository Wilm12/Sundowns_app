from django.test import TestCase

from membership.models import Membership
from membership.tier_rules import get_tier_rules


class TierRulesTests(TestCase):
    def test_basic_pricing(self):
        self.assertEqual(get_tier_rules('basic').price, 50)
        self.assertEqual(Membership(tier='basic').expected_price(), 50)

    def test_premium_pricing(self):
        self.assertEqual(get_tier_rules('premium').price, 100)
        self.assertEqual(Membership(tier='premium').expected_price(), 100)

    def test_golden_pricing(self):
        self.assertEqual(get_tier_rules('golden').price, 150)
        self.assertEqual(Membership(tier='golden').expected_price(), 150)

    def test_basic_transport_eligibility(self):
        rules = get_tier_rules('basic')
        self.assertEqual(rules.transport_eligibility, 'none')
        self.assertFalse(rules.allows_transport)
        self.assertFalse(Membership(tier='basic').allows_transport())

    def test_premium_transport_eligibility(self):
        rules = get_tier_rules('premium')
        self.assertEqual(rules.transport_eligibility, 'branch')
        self.assertTrue(rules.allows_transport)
        self.assertTrue(Membership(tier='premium').allows_transport())

    def test_golden_transport_eligibility(self):
        rules = get_tier_rules('golden')
        self.assertEqual(rules.transport_eligibility, 'expanded')
        self.assertTrue(rules.allows_transport)
        self.assertTrue(Membership(tier='golden').allows_transport())
