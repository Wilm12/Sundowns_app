"""Membership models describing tiers, pricing, and status tracking."""

from django.db import models
from django.conf import settings

from .tier_rules import TIER_RULES, get_tier_rules


class Membership(models.Model):
    """Represents a user's membership tier and lifecycle state."""
    TIER_CHOICES = tuple((tier, rule.display_name) for tier, rule in TIER_RULES.items())

    STATUS_CHOICES = (
        ('pending', 'Pending'),
        ('active', 'Active'),
        ('expired', 'Expired'),
        ('suspended', 'Suspended'),
    )

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='memberships'
    )
    tier = models.CharField(max_length=10, choices=TIER_CHOICES, default='basic')
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='pending')
    start_date = models.DateField(null=True, blank=True)
    expiry_date = models.DateField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    @property
    def tier_rules(self):
        """Return the centralized benefit rule set for this membership tier."""
        return get_tier_rules(self.tier)

    def expected_price(self):
        """Return the expected price for the selected membership tier."""
        return self.tier_rules.price

    def get_merchandise_discount(self):
        """Return the merchandise discount percentage for this tier."""
        return self.tier_rules.merchandise_discount

    def get_transport_eligibility(self):
        """Return the transport eligibility setting for this tier."""
        return self.tier_rules.transport_eligibility

    def allows_transport(self):
        """Return whether this membership tier is allowed to book transport."""
        return self.tier_rules.allows_transport

    def get_promotion_categories(self):
        """Return the promotion categories available to this tier."""
        return list(self.tier_rules.promotion_categories)

    def allows_children_under_16(self):
        """Return whether children under 16 are supported by this tier."""
        return self.tier_rules.children_under_16_allowed

    def __str__(self):
        return f"{self.user} - {self.tier} - {self.status}"
