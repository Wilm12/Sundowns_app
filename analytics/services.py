from django.db.models import Count, Q, Sum, Value
from django.db.models.functions import Coalesce

from points.models import PointsAccount, PointsTransaction
from points.services import get_tier_distribution
from rewards.models import Reward, RewardRedemption
from membership.models import Membership


def get_analytics_loyalty_metrics(limit=10):
    """Return loyalty analytics metrics for the admin analytics dashboard."""
    total_supporters = PointsAccount.objects.count()
    total_points_awarded = PointsTransaction.objects.filter(
        points__gt=0
    ).aggregate(total=Coalesce(Sum('points'), Value(0)))['total']
    total_points_redeemed = PointsTransaction.objects.filter(
        points__lt=0
    ).aggregate(total=Coalesce(Sum('points'), Value(0)))['total']

    tier_distribution = get_tier_distribution()

    top_supporters = (
        PointsAccount.objects
        .annotate(computed_balance=Coalesce(Sum('transactions__points'), Value(0)))
        .select_related('user')
        .order_by('-computed_balance', 'user__username')
        [:limit]
    )

    top_supporters_data = [
        {
            'username': account.user.username,
            'balance': account.computed_balance,
        }
        for account in top_supporters
    ]

    return {
        'total_supporters': total_supporters,
        'total_points_awarded': total_points_awarded,
        'total_points_redeemed': abs(total_points_redeemed),
        'tier_distribution': tier_distribution,
        'top_supporters': top_supporters_data,
    }


def get_analytics_reward_metrics(limit=5):
    """Return reward analytics metrics for the admin analytics dashboard."""
    total_rewards = Reward.objects.count()
    total_reward_redemptions = RewardRedemption.objects.count()

    rewards_with_counts = Reward.objects.annotate(
        redemption_count=Coalesce(Count('redemptions'), Value(0))
    )

    most_redeemed = list(
        rewards_with_counts.order_by('-redemption_count', 'name')[:limit].values(
            'id', 'name', 'redemption_count'
        )
    )
    least_redeemed = list(
        rewards_with_counts.order_by('redemption_count', 'name')[:limit].values(
            'id', 'name', 'redemption_count'
        )
    )

    return {
        'total_rewards': total_rewards,
        'total_reward_redemptions': total_reward_redemptions,
        'most_redeemed_rewards': most_redeemed,
        'least_redeemed_rewards': least_redeemed,
        # workflow counts
        'redemptions_by_status': {
            'pending': RewardRedemption.objects.filter(status=RewardRedemption.Status.PENDING).count(),
            'approved': RewardRedemption.objects.filter(status=RewardRedemption.Status.APPROVED).count(),
            'ready_for_collection': RewardRedemption.objects.filter(status=RewardRedemption.Status.READY_FOR_COLLECTION).count(),
            'collected': RewardRedemption.objects.filter(status=RewardRedemption.Status.COLLECTED).count(),
            'completed': RewardRedemption.objects.filter(status=RewardRedemption.Status.COMPLETED).count(),
            'rejected': RewardRedemption.objects.filter(status=RewardRedemption.Status.REJECTED).count(),
            'cancelled': RewardRedemption.objects.filter(status=RewardRedemption.Status.CANCELLED).count(),
        },
    }


def get_analytics_membership_metrics():
    """Return membership status analytics metrics for the admin analytics dashboard."""
    active_memberships = Membership.objects.filter(status='active').count()
    expired_memberships = Membership.objects.filter(status='expired').count()

    return {
        'active_memberships': active_memberships,
        'expired_memberships': expired_memberships,
    }
