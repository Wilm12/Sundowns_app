from django.db.models import Count, Q, Sum, Value
from django.db.models.functions import Coalesce
from django.utils import timezone

from analytics.models import BranchMatchSnapshot
from journeys.models import Journey, JourneyStatus
from membership.models import Membership
from matches.models import Match
from points.models import PointsAccount, PointsTransaction
from points.services import get_tier_distribution
from rewards.models import Reward, RewardRedemption
from supporters.models import StudentVerification, StudentVerificationStatus
from transport.models import Transport, TransportBooking


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


class AnalyticsSnapshotService:
    """Generate historical branch-match snapshots from current operational journeys."""

    @staticmethod
    def generate_for_match(match):
        """Persist snapshot rows for each branch associated with a match.

        The snapshot is derived from live operational data, while the journey model
        remains the source of truth. Repeated generation is idempotent because the
        model has a unique constraint on (snapshot_date, branch, match).
        """
        branch_ids = (
            Journey.objects.filter(match=match)
            .values_list('branch_id', flat=True)
            .distinct()
        )

        snapshots = []

        for branch_id in branch_ids:
            journeys = Journey.objects.filter(match=match, branch_id=branch_id)

            booked = journeys.filter(
                status__in=[
                    JourneyStatus.BOOKED,
                    JourneyStatus.TICKET_READY,
                    JourneyStatus.TICKET_COLLECTED,
                    JourneyStatus.MATCH_ATTENDED,
                ]
            ).count()

            ticket_ready = journeys.filter(
                status=JourneyStatus.TICKET_READY
            ).count()

            collected = journeys.filter(
                status__in=[
                    JourneyStatus.TICKET_COLLECTED,
                    JourneyStatus.MATCH_ATTENDED,
                ]
            ).count()

            attended = journeys.filter(
                status=JourneyStatus.MATCH_ATTENDED
            ).count()

            supporter_ids = journeys.exclude(supporter_id__isnull=True).values_list(
                'supporter_id', flat=True
            )
            verification_completed = StudentVerification.objects.filter(
                user_id__in=supporter_ids,
                status__in=[
                    StudentVerificationStatus.APPROVED,
                    StudentVerificationStatus.VERIFIED,
                ],
            ).values_list('user_id', flat=True).distinct().count()

            transport_booked = TransportBooking.objects.filter(
                transport__match=match,
                transport__branch_id=branch_id,
            ).count()

            transport_capacity = Transport.objects.filter(
                match=match,
                branch_id=branch_id,
            ).aggregate(total=Coalesce(Sum('capacity'), Value(0)))['total']

            snapshot, _ = BranchMatchSnapshot.objects.update_or_create(
                snapshot_date=timezone.now().date(),
                branch_id=branch_id,
                match=match,
                defaults={
                    'booked': booked,
                    'ticket_ready': ticket_ready,
                    'collected': collected,
                    'attended': attended,
                    'verification_completed': verification_completed,
                    'transport_booked': transport_booked,
                    'transport_capacity': transport_capacity or 0,
                },
            )

            snapshots.append(snapshot)

        return snapshots


class BranchAnalyticsService:
    """Branch-scoped performance metrics only for the approved analytics scope."""

    @staticmethod
    def _attendance_rate(attended, booked):
        if booked == 0:
            return 0
        return round((attended / booked) * 100, 2)

    @staticmethod
    def _snapshot_or_live_metrics(branch, match):
        snapshot = (
            BranchMatchSnapshot.objects.filter(branch=branch, match=match)
            .order_by('-snapshot_date')
            .first()
        )

        if snapshot is not None:
            booked = snapshot.booked
            attended = snapshot.collected
            verification_completed = snapshot.verification_completed
            return {
                'booked': booked,
                'attended': attended,
                'attendance_rate': BranchAnalyticsService._attendance_rate(attended, booked),
                'verification_completed': verification_completed,
            }

        journeys = Journey.objects.filter(branch=branch, match=match)
        booked = journeys.filter(
            status__in=[
                JourneyStatus.BOOKED,
                JourneyStatus.TICKET_READY,
                JourneyStatus.TICKET_COLLECTED,
                JourneyStatus.MATCH_ATTENDED,
            ]
        ).count()
        attended = journeys.filter(
            status__in=[
                JourneyStatus.TICKET_COLLECTED,
                JourneyStatus.MATCH_ATTENDED,
            ]
        ).count()
        verification_completed = StudentVerification.objects.filter(
            user__in=journeys.exclude(supporter_id__isnull=True).values_list('supporter_id', flat=True),
            status__in=[
                StudentVerificationStatus.APPROVED,
                StudentVerificationStatus.VERIFIED,
            ],
        ).values_list('user_id', flat=True).distinct().count()

        return {
            'booked': booked,
            'attended': attended,
            'attendance_rate': BranchAnalyticsService._attendance_rate(attended, booked),
            'verification_completed': verification_completed,
        }

    @staticmethod
    def get_branch_match_metrics(branch, match):
        metrics = BranchAnalyticsService._snapshot_or_live_metrics(branch, match)
        return {
            'match': match,
            'branch': branch,
            'booked': metrics['booked'],
            'attended': metrics['attended'],
            'attendance_rate': metrics['attendance_rate'],
            'verification_completed': metrics['verification_completed'],
        }

    @staticmethod
    def get_branch_performance(branch):
        matches = Match.objects.filter(journeys__branch=branch).order_by('-date').distinct()
        performance = []

        for match in matches:
            metrics = BranchAnalyticsService.get_branch_match_metrics(branch, match)
            performance.append({
                'match': metrics['match'],
                'booked': metrics['booked'],
                'attended': metrics['attended'],
                'attendance_rate': metrics['attendance_rate'],
                'verification_completed': metrics['verification_completed'],
            })

        return performance
