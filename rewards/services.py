"""Services for reward redemption and related business logic."""

from django.db import transaction
from django.db.models import F

from .models import Reward, RewardRedemption
from points.models import PointsTransaction


def redeem_reward(user, reward):
    """Redeem a reward for a user using points.

    Args:
        user: The supporter redeeming the reward.
        reward: The Reward instance to redeem.

    Returns:
        RewardRedemption: The created redemption record.

    Raises:
        ValueError: When the reward is inactive, out of stock, or the user lacks sufficient points.
    """
    account = getattr(user, 'points_account', None)
    if account is None:
        raise ValueError('User must have a points account before redeeming rewards.')

    if not reward.is_active:
        raise ValueError('Reward is not active.')

    if reward.quantity_available <= 0:
        raise ValueError('Reward is out of stock.')

    if account.balance < reward.points_cost:
        raise ValueError('Insufficient points balance to redeem reward.')

    with transaction.atomic():
        reward_locked = Reward.objects.select_for_update().get(pk=reward.pk)

        if not reward_locked.is_active:
            raise ValueError('Reward is not active.')

        if reward_locked.quantity_available <= 0:
            raise ValueError('Reward is out of stock.')

        if account.balance < reward_locked.points_cost:
            raise ValueError('Insufficient points balance to redeem reward.')

        redemption = RewardRedemption.objects.create(
            user=user,
            reward=reward_locked,
            points_spent=reward_locked.points_cost,
        )

        PointsTransaction.objects.create(
            account=account,
            transaction_type=PointsTransaction.TransactionType.REWARD_REDEMPTION,
            points=-reward_locked.points_cost,
            description='reward redemption',
            reference_id=f'reward_redemption:{redemption.pk}',
        )

        reward_locked.quantity_available = F('quantity_available') - 1
        reward_locked.save(update_fields=['quantity_available'])

    return redemption
