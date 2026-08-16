from django.test import TestCase
from django.contrib.auth import get_user_model
from django.utils import timezone

from analytics.models import BranchMatchSnapshot
from analytics.services import (
    AnalyticsSnapshotService,
    BranchAnalyticsService,
    get_analytics_loyalty_metrics,
    get_analytics_reward_metrics,
    get_analytics_membership_metrics,
)
from branches.models import Branch
from journeys.models import Journey, JourneyStatus
from matches.models import Match
from membership.models import Membership
from points.models import PointsTransaction
from points.services import get_tier_distribution
from rewards.models import Reward, RewardRedemption
from supporters.models import StudentVerification, StudentVerificationStatus
from ticketing.models import Ticket
from transport.models import Transport, TransportBooking

User = get_user_model()


class AnalyticsServiceTests(TestCase):
    def setUp(self):
        self.user1 = User.objects.create_user(
            username='supporter1',
            email='s1@example.com',
            password='pass123'
        )
        self.user2 = User.objects.create_user(
            username='supporter2',
            email='s2@example.com',
            password='pass123'
        )
        self.user3 = User.objects.create_user(
            username='supporter3',
            email='s3@example.com',
            password='pass123'
        )

        PointsTransaction.objects.create(
            account=self.user1.points_account,
            transaction_type=PointsTransaction.TransactionType.MEMBERSHIP_PAYMENT,
            points=150,
            description='Award for signup'
        )
        PointsTransaction.objects.create(
            account=self.user1.points_account,
            transaction_type=PointsTransaction.TransactionType.REWARD_REDEMPTION,
            points=-50,
            description='Redemption'
        )
        PointsTransaction.objects.create(
            account=self.user2.points_account,
            transaction_type=PointsTransaction.TransactionType.MEMBERSHIP_PAYMENT,
            points=500,
            description='Award for loyalty'
        )
        PointsTransaction.objects.create(
            account=self.user3.points_account,
            transaction_type=PointsTransaction.TransactionType.MEMBERSHIP_PAYMENT,
            points=25,
            description='Award for action'
        )
        self.reward1 = Reward.objects.create(
            name='Free Match Ticket',
            description='Redeem for a free ticket',
            points_cost=200,
            quantity_available=10,
            is_active=True
        )
        self.reward2 = Reward.objects.create(
            name='Club Scarf',
            description='Redeem for a scarf',
            points_cost=100,
            quantity_available=3,
            is_active=True
        )
        RewardRedemption.objects.create(
            user=self.user1,
            reward=self.reward1,
            points_spent=200,
            status=RewardRedemption.Status.APPROVED
        )
        RewardRedemption.objects.create(
            user=self.user2,
            reward=self.reward1,
            points_spent=200,
            status=RewardRedemption.Status.COMPLETED
        )
        RewardRedemption.objects.create(
            user=self.user3,
            reward=self.reward2,
            points_spent=100,
            status=RewardRedemption.Status.APPROVED
        )

        Membership.objects.create(
            user=self.user1,
            tier='bronze',
            status='active'
        )
        Membership.objects.create(
            user=self.user2,
            tier='silver',
            status='expired'
        )
        Membership.objects.create(
            user=self.user3,
            tier='gold',
            status='active'
        )

    def test_tier_distribution_calculation(self):
        distribution = get_tier_distribution()

        self.assertEqual(distribution['bronze'], 1)
        self.assertEqual(distribution['silver'], 1)
        self.assertEqual(distribution['gold'], 1)
        self.assertEqual(distribution['platinum'], 0)

    def test_top_supporters_query(self):
        metrics = get_analytics_loyalty_metrics(limit=3)

        self.assertEqual(metrics['top_supporters'][0]['username'], 'supporter2')
        self.assertEqual(metrics['top_supporters'][0]['balance'], 500)
        self.assertEqual(metrics['top_supporters'][1]['username'], 'supporter1')
        self.assertEqual(metrics['top_supporters'][1]['balance'], 100)
        self.assertEqual(metrics['top_supporters'][2]['username'], 'supporter3')
        self.assertEqual(metrics['top_supporters'][2]['balance'], 25)

    def test_reward_analytics_counts(self):
        reward_metrics = get_analytics_reward_metrics()

        self.assertEqual(reward_metrics['total_rewards'], 2)
        self.assertEqual(reward_metrics['total_reward_redemptions'], 3)
        self.assertEqual(reward_metrics['most_redeemed_rewards'][0]['name'], 'Free Match Ticket')
        self.assertEqual(reward_metrics['most_redeemed_rewards'][0]['redemption_count'], 2)
        self.assertEqual(reward_metrics['least_redeemed_rewards'][0]['name'], 'Club Scarf')
        self.assertEqual(reward_metrics['least_redeemed_rewards'][0]['redemption_count'], 1)

    def test_membership_analytics_counts(self):
        membership_metrics = get_analytics_membership_metrics()

        self.assertEqual(membership_metrics['active_memberships'], 2)
        self.assertEqual(membership_metrics['expired_memberships'], 1)

    def test_snapshot_service_generates_branch_scoped_idempotent_history(self):
        branch_one = Branch.objects.create(name='Mamelodi East', branch_code='ME', category='COMMUNITY')
        branch_two = Branch.objects.create(name='Tuks', branch_code='TUKS', category='INSTITUTIONAL')
        match = Match.objects.create(
            date=timezone.now(),
            location='Loftus Versfeld',
            opponent='Kaizer Chiefs',
            published=True,
        )

        supporter_a = User.objects.create_user(username='snapshot_a', email='a@example.com', password='pass123')
        supporter_b = User.objects.create_user(username='snapshot_b', email='b@example.com', password='pass123')
        supporter_c = User.objects.create_user(username='snapshot_c', email='c@example.com', password='pass123')
        supporter_d = User.objects.create_user(username='snapshot_d', email='d@example.com', password='pass123')
        supporter_e = User.objects.create_user(username='snapshot_e', email='e@example.com', password='pass123')

        StudentVerification.objects.create(
            user=supporter_a,
            student_number='A1001',
            university='UP',
            status=StudentVerificationStatus.VERIFIED,
        )
        StudentVerification.objects.create(
            user=supporter_b,
            student_number='B1002',
            university='UP',
            status=StudentVerificationStatus.APPROVED,
        )
        StudentVerification.objects.create(
            user=supporter_c,
            student_number='C1003',
            university='Wits',
            status=StudentVerificationStatus.VERIFIED,
        )
        StudentVerification.objects.create(
            user=supporter_d,
            student_number='D1004',
            university='UJ',
            status=StudentVerificationStatus.APPROVED,
        )
        StudentVerification.objects.create(
            user=supporter_e,
            student_number='E1005',
            university='UCT',
            status=StudentVerificationStatus.VERIFIED,
        )

        journey_a = Journey.objects.create(
            supporter=supporter_a,
            branch=branch_one,
            match=match,
            status=JourneyStatus.BOOKED,
        )
        journey_b = Journey.objects.create(
            supporter=supporter_b,
            branch=branch_one,
            match=match,
            status=JourneyStatus.TICKET_READY,
        )
        journey_c = Journey.objects.create(
            supporter=supporter_c,
            branch=branch_one,
            match=match,
            status=JourneyStatus.MATCH_ATTENDED,
        )
        journey_d = Journey.objects.create(
            supporter=supporter_d,
            branch=branch_one,
            match=match,
            status=JourneyStatus.TICKET_COLLECTED,
        )
        Journey.objects.create(
            supporter=supporter_e,
            branch=branch_two,
            match=match,
            status=JourneyStatus.BOOKED,
        )

        transport = Transport.objects.create(
            branch=branch_one,
            match=match,
            owner_id=1,
            capacity=5,
            status='active',
        )
        ticket = Ticket.objects.create(
            user=supporter_a,
            match=match,
            status='booked',
        )
        TransportBooking.objects.create(
            ticket=ticket,
            transport=transport,
            status='booked',
        )

        first_snapshots = AnalyticsSnapshotService.generate_for_match(match)

        self.assertEqual(len(first_snapshots), 2)
        self.assertEqual(BranchMatchSnapshot.objects.filter(match=match).count(), 2)

        branch_one_snapshot = BranchMatchSnapshot.objects.get(match=match, branch=branch_one)
        self.assertEqual(branch_one_snapshot.match, match)
        self.assertEqual(branch_one_snapshot.branch, branch_one)
        self.assertEqual(branch_one_snapshot.booked, 4)
        self.assertEqual(branch_one_snapshot.ticket_ready, 1)
        self.assertEqual(branch_one_snapshot.collected, 2)
        self.assertEqual(branch_one_snapshot.attended, 1)
        self.assertEqual(branch_one_snapshot.verification_completed, 4)
        self.assertEqual(branch_one_snapshot.transport_booked, 1)
        self.assertEqual(branch_one_snapshot.transport_capacity, 5)

        branch_two_snapshot = BranchMatchSnapshot.objects.get(match=match, branch=branch_two)
        self.assertEqual(branch_two_snapshot.booked, 1)
        self.assertEqual(branch_two_snapshot.ticket_ready, 0)
        self.assertEqual(branch_two_snapshot.collected, 0)
        self.assertEqual(branch_two_snapshot.attended, 0)
        self.assertEqual(branch_two_snapshot.verification_completed, 1)
        self.assertEqual(branch_two_snapshot.transport_booked, 0)
        self.assertEqual(branch_two_snapshot.transport_capacity, 0)

        second_snapshots = AnalyticsSnapshotService.generate_for_match(match)

        self.assertEqual(len(second_snapshots), 2)
        self.assertEqual(BranchMatchSnapshot.objects.filter(match=match).count(), 2)

        journey_b.status = JourneyStatus.MATCH_ATTENDED
        journey_b.save(update_fields=['status', 'updated_at'])

        AnalyticsSnapshotService.generate_for_match(match)

        branch_one_snapshot.refresh_from_db()
        self.assertEqual(branch_one_snapshot.ticket_ready, 0)
        self.assertEqual(branch_one_snapshot.collected, 3)
        self.assertEqual(branch_one_snapshot.attended, 2)
        self.assertEqual(branch_one_snapshot.booked, 4)

        self.assertEqual(BranchMatchSnapshot.objects.filter(match=match, branch=branch_one).count(), 1)
        self.assertEqual(BranchMatchSnapshot.objects.filter(match=match, branch=branch_two).count(), 1)

        self.assertNotEqual(journey_a.branch, branch_two)
        self.assertNotEqual(journey_b.branch, branch_two)
        self.assertNotEqual(journey_c.branch, branch_two)
        self.assertNotEqual(journey_d.branch, branch_two)

    def test_branch_analytics_scopes_bookings_to_branch(self):
        branch_a = Branch.objects.create(name='Mamelodi East', branch_code='ME', category='COMMUNITY')
        branch_b = Branch.objects.create(name='Tuks', branch_code='TUKS', category='INSTITUTIONAL')
        match = Match.objects.create(date=timezone.now(), location='Loftus', opponent='Orlando Pirates', published=True)

        for idx in range(2):
            supporter = User.objects.create_user(username=f'branch_a_{idx}', email=f'a{idx}@example.com', password='pass123')
            Journey.objects.create(supporter=supporter, branch=branch_a, match=match, status=JourneyStatus.BOOKED)

        supporter = User.objects.create_user(username='branch_b_only', email='b@example.com', password='pass123')
        Journey.objects.create(supporter=supporter, branch=branch_b, match=match, status=JourneyStatus.BOOKED)

        metrics = BranchAnalyticsService.get_branch_match_metrics(branch=branch_a, match=match)

        self.assertEqual(metrics['booked'], 2)
        self.assertEqual(metrics['attendance_rate'], 0)

    def test_branch_analytics_counts_ticket_collection_as_attendance(self):
        branch = Branch.objects.create(name='Mamelodi East', branch_code='ME', category='COMMUNITY')
        match = Match.objects.create(date=timezone.now(), location='Loftus', opponent='Kaizer Chiefs', published=True)

        for status in [JourneyStatus.BOOKED, JourneyStatus.TICKET_READY, JourneyStatus.TICKET_COLLECTED, JourneyStatus.MATCH_ATTENDED]:
            supporter = User.objects.create_user(username=f'attend_{status}', email=f'{status}@example.com', password='pass123')
            Journey.objects.create(supporter=supporter, branch=branch, match=match, status=status)

        metrics = BranchAnalyticsService.get_branch_match_metrics(branch=branch, match=match)

        self.assertEqual(metrics['booked'], 4)
        self.assertEqual(metrics['attended'], 2)
        self.assertEqual(metrics['attendance_rate'], 50.0)

    def test_branch_analytics_handles_zero_booking_case(self):
        branch = Branch.objects.create(name='Mamelodi East', branch_code='ME', category='COMMUNITY')
        match = Match.objects.create(date=timezone.now(), location='Loftus', opponent='Cape Town City', published=True)

        metrics = BranchAnalyticsService.get_branch_match_metrics(branch=branch, match=match)

        self.assertEqual(metrics['booked'], 0)
        self.assertEqual(metrics['attended'], 0)
        self.assertEqual(metrics['attendance_rate'], 0)

    def test_branch_analytics_counts_only_completed_verification(self):
        branch = Branch.objects.create(name='Mamelodi East', branch_code='ME', category='COMMUNITY')
        match = Match.objects.create(date=timezone.now(), location='Loftus', opponent='Maritzburg', published=True)

        approved = User.objects.create_user(username='verified_ok', email='v1@example.com', password='pass123')
        verified = User.objects.create_user(username='verified_yes', email='v2@example.com', password='pass123')
        pending = User.objects.create_user(username='verified_pending', email='v3@example.com', password='pass123')
        rejected = User.objects.create_user(username='verified_rejected', email='v4@example.com', password='pass123')

        for supporter in [approved, verified, pending, rejected]:
            Journey.objects.create(supporter=supporter, branch=branch, match=match, status=JourneyStatus.BOOKED)

        StudentVerification.objects.create(user=approved, student_number='S1', university='UP', status=StudentVerificationStatus.APPROVED)
        StudentVerification.objects.create(user=verified, student_number='S2', university='UP', status=StudentVerificationStatus.VERIFIED)
        StudentVerification.objects.create(user=pending, student_number='S3', university='UP', status=StudentVerificationStatus.PENDING)
        StudentVerification.objects.create(user=rejected, student_number='S4', university='UP', status=StudentVerificationStatus.REJECTED)

        metrics = BranchAnalyticsService.get_branch_match_metrics(branch=branch, match=match)

        self.assertEqual(metrics['verification_completed'], 2)

    def test_branch_analytics_historical_performance_across_matches(self):
        branch = Branch.objects.create(name='Mamelodi East', branch_code='ME', category='COMMUNITY')
        first_match = Match.objects.create(date=timezone.now(), location='Loftus', opponent='Sundowns vs Chiefs', published=True)
        second_match = Match.objects.create(date=timezone.now() + timezone.timedelta(days=7), location='Loftus', opponent='Sundowns vs Pirates', published=True)

        supporter_one = User.objects.create_user(username='hist_one', email='h1@example.com', password='pass123')
        supporter_two = User.objects.create_user(username='hist_two', email='h2@example.com', password='pass123')
        supporter_three = User.objects.create_user(username='hist_three', email='h3@example.com', password='pass123')
        supporter_four = User.objects.create_user(username='hist_four', email='h4@example.com', password='pass123')

        Journey.objects.create(supporter=supporter_one, branch=branch, match=first_match, status=JourneyStatus.BOOKED)
        Journey.objects.create(supporter=supporter_two, branch=branch, match=first_match, status=JourneyStatus.TICKET_COLLECTED)
        Journey.objects.create(supporter=supporter_three, branch=branch, match=second_match, status=JourneyStatus.BOOKED)
        Journey.objects.create(supporter=supporter_four, branch=branch, match=second_match, status=JourneyStatus.MATCH_ATTENDED)

        StudentVerification.objects.create(user=supporter_one, student_number='H1', university='UP', status=StudentVerificationStatus.VERIFIED)
        StudentVerification.objects.create(user=supporter_two, student_number='H2', university='Wits', status=StudentVerificationStatus.VERIFIED)
        StudentVerification.objects.create(user=supporter_three, student_number='H3', university='UJ', status=StudentVerificationStatus.APPROVED)
        StudentVerification.objects.create(user=supporter_four, student_number='H4', university='UCT', status=StudentVerificationStatus.APPROVED)

        performance = BranchAnalyticsService.get_branch_performance(branch)

        self.assertEqual(len(performance), 2)
        self.assertEqual(performance[0]['match'], second_match)
        self.assertEqual(performance[0]['booked'], 2)
        self.assertEqual(performance[0]['attended'], 1)
        self.assertEqual(performance[0]['attendance_rate'], 50.0)
        self.assertEqual(performance[0]['verification_completed'], 2)

    def test_branch_analytics_avoids_cross_branch_contamination(self):
        branch_a = Branch.objects.create(name='Mamelodi East', branch_code='ME', category='COMMUNITY')
        branch_b = Branch.objects.create(name='Tuks', branch_code='TUKS', category='INSTITUTIONAL')
        match = Match.objects.create(date=timezone.now(), location='Loftus', opponent='Stellenbosch', published=True)

        for idx in range(3):
            supporter = User.objects.create_user(username=f'isolated_a_{idx}', email=f'ia{idx}@example.com', password='pass123')
            Journey.objects.create(supporter=supporter, branch=branch_a, match=match, status=JourneyStatus.BOOKED)
        supporter = User.objects.create_user(username='isolated_b', email='ib@example.com', password='pass123')
        Journey.objects.create(supporter=supporter, branch=branch_b, match=match, status=JourneyStatus.MATCH_ATTENDED)

        metrics = BranchAnalyticsService.get_branch_match_metrics(branch=branch_a, match=match)

        self.assertEqual(metrics['booked'], 3)
        self.assertEqual(metrics['attended'], 0)
        self.assertEqual(metrics['attendance_rate'], 0)
