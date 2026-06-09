from dataclasses import dataclass
from typing import Dict, Tuple


@dataclass(frozen=True)
class MembershipTierRule:
    tier: str
    display_name: str
    price: int
    student_price: int
    home_game_tickets: bool
    transport_eligibility: str
    merchandise_discount: int
    promotion_categories: Tuple[str, ...]
    children_under_16_allowed: bool
    vip_ticket_discount: bool

    @property
    def allows_transport(self) -> bool:
        return self.transport_eligibility in ("branch", "expanded")


TIER_RULES: Dict[str, MembershipTierRule] = {
    "basic": MembershipTierRule(
        tier="basic",
        display_name="Basic",
        price=50,
        student_price=0,
        home_game_tickets=True,
        transport_eligibility="none",
        merchandise_discount=30,
        promotion_categories=("giveaway",),
        children_under_16_allowed=False,
        vip_ticket_discount=False,
    ),
    "premium": MembershipTierRule(
        tier="premium",
        display_name="Premium",
        price=100,
        student_price=0,
        home_game_tickets=True,
        transport_eligibility="branch",
        merchandise_discount=60,
        promotion_categories=("premium",),
        children_under_16_allowed=True,
        vip_ticket_discount=False,
    ),
    "golden": MembershipTierRule(
        tier="golden",
        display_name="Golden",
        price=150,
        student_price=0,
        home_game_tickets=True,
        transport_eligibility="expanded",
        merchandise_discount=70,
        promotion_categories=("golden",),
        children_under_16_allowed=True,
        vip_ticket_discount=True,
    ),
}


def get_tier_rules(tier: str) -> MembershipTierRule:
    """Return the tier definition for a membership tier."""
    try:
        return TIER_RULES[tier]
    except KeyError as exc:
        raise ValueError(f"Unknown membership tier '{tier}'") from exc


def get_all_tiers() -> Tuple[MembershipTierRule, ...]:
    """Return all configured tier rules."""
    return tuple(TIER_RULES.values())
