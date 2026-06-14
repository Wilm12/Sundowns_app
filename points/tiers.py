"""Tier calculation helpers for supporter loyalty tiers."""

TIERS = [
    ('bronze', 'Bronze'),
    ('silver', 'Silver'),
    ('gold', 'Gold'),
    ('platinum', 'Platinum'),
]

TIER_THRESHOLDS = {
    'bronze': 0,
    'silver': 100,
    'gold': 500,
    'platinum': 1000,
}

TIER_ORDER = ['bronze', 'silver', 'gold', 'platinum']


def get_tier_from_points(points: int) -> str:
    """Return tier key name for given points."""
    points = points or 0
    if points >= TIER_THRESHOLDS['platinum']:
        return 'platinum'
    if points >= TIER_THRESHOLDS['gold']:
        return 'gold'
    if points >= TIER_THRESHOLDS['silver']:
        return 'silver'
    return 'bronze'


def get_next_tier(points: int):
    """Return the next tier key name or None if already at top."""
    current = get_tier_from_points(points)
    try:
        idx = TIER_ORDER.index(current)
    except ValueError:
        return None
    if idx + 1 >= len(TIER_ORDER):
        return None
    return TIER_ORDER[idx + 1]


def points_until_next_tier(points: int) -> int:
    """Return points remaining until next tier, or 0 if at top."""
    next_tier = get_next_tier(points)
    if not next_tier:
        return 0
    return max(0, TIER_THRESHOLDS[next_tier] - (points or 0))


def get_tier_rank(tier_key: str) -> int:
    """Numeric rank for comparing tiers (higher is better)."""
    try:
        return TIER_ORDER.index(tier_key)
    except ValueError:
        return 0


def get_user_tier(user) -> str:
    """Return tier key for given user based on their points account balance."""
    account = getattr(user, 'points_account', None)
    if account is None:
        return 'bronze'
    return get_tier_from_points(account.balance)
