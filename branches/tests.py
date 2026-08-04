from unittest.mock import patch

from django.contrib.auth import get_user_model
from django.db import IntegrityError
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from engagement.events import EngagementEvent

from journeys.models import Journey, JourneyStatus
from matches.models import Match
from supporters.models import EligibilityReason, SupporterEligibility, StudentVerification, StudentVerificationStatus
from ticketing.models import Ticket
from users.models import User

from .models import Branch, BranchPolicy, BranchRole, BranchStatus, CommitteeActivity, CommitteeAction, CommitteePosition
from .serializers import BranchPolicySerializer, BranchRoleSerializer, BranchSerializer
from .services.assign_branch_role import AssignBranchRoleService, BranchRoleAlreadyAssigned
from .services.branch_admin_dashboard import BranchAdminDashboardService
from .services.committee import CommitteeService
from .services.promote_branch_admin import BranchAdminAlreadyAssigned, PromoteBranchAdminService, UserNotInBranch
from .services.remove_branch_admin import LastBranchAdminRemovalError, RemoveBranchAdminService
from .services.remove_branch_role import BranchRoleNotAssigned, RemoveBranchRoleService
from branches.services.authorization import BranchAdminRequired, is_branch_admin


class BranchAdminDashboardTests(TestCase):
    def test_branch_admin_helper_returns_true_for_authorized_users(self):
        branch = Branch.objects.create(name="Authorization Branch")
        admin = self._create_user(username="authorization-admin")
        admin.branch = branch
        admin.save(update_fields=["branch"])
        BranchRole.objects.create(branch=branch, user=admin, role=BranchRole.Role.BRANCH_ADMIN, is_active=True)

        self.assertTrue(is_branch_admin(admin))
        self.assertTrue(is_branch_admin(admin, branch))

    def test_dashboard_metrics_are_correct(self):
        branch = Branch.objects.create(name="Metrics Branch")
        admin = self._create_user(username="metrics-admin")
        admin.branch = branch
        admin.save(update_fields=["branch"])
        BranchRole.objects.create(branch=branch, user=admin, role=BranchRole.Role.BRANCH_ADMIN, is_active=True)

        supporter_one = self._create_user(username="metrics-supporter-one")
        supporter_one.branch = branch
        supporter_one.save(update_fields=["branch"])
        BranchRole.objects.create(
            branch=branch,
            user=supporter_one,
            role=BranchRole.Role.MEMBER,
            is_active=True,
        )

        supporter_two = self._create_user(username="metrics-supporter-two")
        supporter_two.branch = branch
        supporter_two.save(update_fields=["branch"])
        BranchRole.objects.create(
            branch=branch,
            user=supporter_two,
            role=BranchRole.Role.MEMBER,
            is_active=True,
        )

        supporter_three = self._create_user(username="metrics-supporter-three")
        supporter_three.branch = branch
        supporter_three.save(update_fields=["branch"])

        StudentVerification.objects.create(user=supporter_one, student_number="u10001", university="TUKS", status=StudentVerificationStatus.VERIFIED)
        StudentVerification.objects.create(user=supporter_two, student_number="u10002", university="TUKS", status=StudentVerificationStatus.PENDING)
        SupporterEligibility.objects.create(supporter=supporter_one, is_eligible=True, reason=EligibilityReason.VERIFIED)
        SupporterEligibility.objects.create(supporter=supporter_two, is_eligible=False, reason=EligibilityReason.VERIFICATION_PENDING)

        match = Match.objects.create(date=timezone.now(), location="Loftus", opponent="Orlando Pirates")
        Journey.objects.create(supporter=supporter_one, branch=branch, match=match, status=JourneyStatus.BOOKED)
        Journey.objects.create(supporter=supporter_two, branch=branch, match=match, status=JourneyStatus.MATCH_ATTENDED)
        Journey.objects.create(supporter=supporter_three, branch=branch, match=match, status=JourneyStatus.TICKET_READY)

        dashboard = BranchAdminDashboardService.get_dashboard(admin, branch=branch)

        self.assertEqual(dashboard["supporter_metrics"]["total_supporters"], 3)
        self.assertEqual(dashboard["supporter_metrics"]["verified_supporters"], 1)
        self.assertEqual(dashboard["supporter_metrics"]["eligible_supporters"], 1)
        self.assertEqual(dashboard["supporter_metrics"]["active_members"], 1)
        self.assertEqual(dashboard["journey_metrics"]["allocated_count"], 2)
        self.assertEqual(dashboard["journey_metrics"]["booked_count"], 3)
        self.assertEqual(dashboard["journey_metrics"]["pending_count"], 1)
        self.assertEqual(dashboard["journey_metrics"]["attended_count"], 1)

    def test_gate_redemption_redirects_unverified_supporter_to_verification(self):
        branch = Branch.objects.create(name="Gate Redirect Branch")
        admin = self._create_user(username="gate-redirect-admin")
        admin.branch = branch
        admin.save(update_fields=["branch"])
        BranchRole.objects.create(branch=branch, user=admin, role=BranchRole.Role.BRANCH_ADMIN, is_active=True)

        supporter = self._create_user(username="gate-redirect-supporter")
        supporter.branch = branch
        supporter.save(update_fields=["branch"])
        BranchRole.objects.create(branch=branch, user=supporter, role=BranchRole.Role.MEMBER, is_active=True)

        match = Match.objects.create(date=timezone.now(), location="Cape Town", opponent="Mamelodi Sundowns")
        SupporterEligibility.objects.create(supporter=supporter, is_eligible=True, reason=EligibilityReason.VERIFIED)
        StudentVerification.objects.create(user=supporter, student_number="u90001", university="UCT", status=StudentVerificationStatus.PENDING)
        journey = Journey.objects.create(supporter=supporter, branch=branch, match=match, status=JourneyStatus.BOOKED, collection_code="4827")

        self.client.force_login(admin)
        response = self.client.post(
            reverse("match_operations_console", args=[branch.pk, match.pk]),
            data={"action": "redeem", "collection_code": "4827"},
        )

        self.assertEqual(response.status_code, 302)
        self.assertIn(reverse("branch_supporter_verification", args=[branch.pk, supporter.pk]), response.url)
        self.assertIn("next=gate-redemption", response.url)
        self.assertIn("code=4827", response.url)
        self.assertEqual(journey.status, JourneyStatus.BOOKED)

    def test_verification_redirect_completes_redemption_after_verification(self):
        branch = Branch.objects.create(name="Verification Redemption Branch")
        admin = self._create_user(username="verification-redemption-admin")
        admin.branch = branch
        admin.save(update_fields=["branch"])
        BranchRole.objects.create(branch=branch, user=admin, role=BranchRole.Role.BRANCH_ADMIN, is_active=True)

        supporter = self._create_user(username="verification-redemption-supporter")
        supporter.branch = branch
        supporter.save(update_fields=["branch"])
        BranchRole.objects.create(branch=branch, user=supporter, role=BranchRole.Role.MEMBER, is_active=True)

        match = Match.objects.create(date=timezone.now(), location="Durban", opponent="Kaizer Chiefs")
        SupporterEligibility.objects.create(supporter=supporter, is_eligible=True, reason=EligibilityReason.VERIFIED)
        verification = StudentVerification.objects.create(user=supporter, student_number="u90002", university="Wits", status=StudentVerificationStatus.PENDING)
        journey = Journey.objects.create(supporter=supporter, branch=branch, match=match, status=JourneyStatus.BOOKED, collection_code="4827")

        self.client.force_login(admin)
        response = self.client.post(
            f"{reverse('branch_supporter_verification', args=[branch.pk, supporter.pk])}?next=gate-redemption&code=4827&match_id={match.pk}",
            data={},
        )

        self.assertEqual(response.status_code, 302)
        verification.refresh_from_db()
        journey.refresh_from_db()
        self.assertEqual(verification.status, StudentVerificationStatus.VERIFIED)
        self.assertEqual(journey.status, JourneyStatus.MATCH_ATTENDED)
        self.assertEqual(journey.attended_by, admin)

    def test_redemption_redirects_unverified_supporter_to_verification(self):
        branch = Branch.objects.create(name="Gate Redirect Branch")
        admin = self._create_user(username="gate-redirect-admin")
        admin.branch = branch
        admin.save(update_fields=["branch"])
        BranchRole.objects.create(branch=branch, user=admin, role=BranchRole.Role.BRANCH_ADMIN, is_active=True)

        supporter = self._create_user(username="gate-redirect-supporter")
        supporter.branch = branch
        supporter.save(update_fields=["branch"])
        BranchRole.objects.create(branch=branch, user=supporter, role=BranchRole.Role.MEMBER, is_active=True)

        match = Match.objects.create(date=timezone.now(), location="Cape Town", opponent="Mamelodi Sundowns")
        SupporterEligibility.objects.create(supporter=supporter, is_eligible=True, reason=EligibilityReason.VERIFIED)
        StudentVerification.objects.create(user=supporter, student_number="u90001", university="UCT", status=StudentVerificationStatus.PENDING)
        journey = Journey.objects.create(supporter=supporter, branch=branch, match=match, status=JourneyStatus.BOOKED, collection_code="4827")

        self.client.force_login(admin)
        response = self.client.post(
            reverse("match_operations_console", args=[branch.pk, match.pk]),
            data={"action": "redeem", "collection_code": "4827"},
        )

        self.assertEqual(response.status_code, 302)
        self.assertIn(reverse("branch_supporter_verification", args=[branch.pk, supporter.pk]), response.url)
        self.assertIn("next=gate-redemption", response.url)
        self.assertIn("code=4827", response.url)
        self.assertEqual(journey.status, JourneyStatus.BOOKED)

    def test_verification_redirect_completes_redemption_after_verification(self):
        branch = Branch.objects.create(name="Verification Redemption Branch")
        admin = self._create_user(username="verification-redemption-admin")
        admin.branch = branch
        admin.save(update_fields=["branch"])
        BranchRole.objects.create(branch=branch, user=admin, role=BranchRole.Role.BRANCH_ADMIN, is_active=True)

        supporter = self._create_user(username="verification-redemption-supporter")
        supporter.branch = branch
        supporter.save(update_fields=["branch"])
        BranchRole.objects.create(branch=branch, user=supporter, role=BranchRole.Role.MEMBER, is_active=True)

        match = Match.objects.create(date=timezone.now(), location="Durban", opponent="Kaizer Chiefs")
        SupporterEligibility.objects.create(supporter=supporter, is_eligible=True, reason=EligibilityReason.VERIFIED)
        verification = StudentVerification.objects.create(user=supporter, student_number="u90002", university="Wits", status=StudentVerificationStatus.PENDING)
        journey = Journey.objects.create(supporter=supporter, branch=branch, match=match, status=JourneyStatus.BOOKED, collection_code="4827")

        self.client.force_login(admin)
        response = self.client.post(
            f"{reverse('branch_supporter_verification', args=[branch.pk, supporter.pk])}?next=gate-redemption&code=4827&match_id={match.pk}",
            data={},
        )

        self.assertEqual(response.status_code, 302)
        verification.refresh_from_db()
        journey.refresh_from_db()
        self.assertEqual(verification.status, StudentVerificationStatus.VERIFIED)
        self.assertEqual(journey.status, JourneyStatus.MATCH_ATTENDED)
        self.assertEqual(journey.attended_by, admin)

    def test_dashboard_renders_leadership_positions_and_reports_before_committee(self):
        branch = Branch.objects.create(name="Leadership Branch")
        admin = self._create_user(username="leadership-admin")
        admin.branch = branch
        admin.save(update_fields=["branch"])
        admin_role = BranchRole.objects.create(branch=branch, user=admin, role=BranchRole.Role.BRANCH_ADMIN, is_active=True)
        CommitteePosition.objects.create(branch=branch, branch_role=admin_role, position=CommitteePosition.Position.CHAIRPERSON, created_by=admin)

        supporter = self._create_user(username="leadership-supporter")
        supporter.branch = branch
        supporter.save(update_fields=["branch"])
        BranchRole.objects.create(branch=branch, user=supporter, role=BranchRole.Role.MEMBER, is_active=True)

        match = Match.objects.create(date=timezone.now(), location="Loftus", opponent="Orlando Pirates")
        Journey.objects.create(supporter=supporter, branch=branch, match=match, status=JourneyStatus.BOOKED)

        self.client.force_login(admin)
        response = self.client.get(reverse("branch_admin_dashboard"))
        content = response.content.decode()

        self.assertContains(response, "Reports")
        self.assertContains(response, "Leadership")
        self.assertContains(response, "Chairperson")
        self.assertNotContains(response, "Collected")
        self.assertLess(content.index("Reports"), content.index("Committee"))

    def test_dashboard_assigns_default_chairperson_when_no_leadership_positions_exist(self):
        branch = Branch.objects.create(name="Auto Chair Branch")
        admin = self._create_user(username="auto-chair-admin")
        admin.branch = branch
        admin.save(update_fields=["branch"])
        BranchRole.objects.create(branch=branch, user=admin, role=BranchRole.Role.BRANCH_ADMIN, is_active=True)

        dashboard = BranchAdminDashboardService.get_dashboard(admin, branch=branch)

        self.assertTrue(
            CommitteePosition.objects.filter(
                branch=branch,
                branch_role__user=admin,
                position=CommitteePosition.Position.CHAIRPERSON,
            ).exists()
        )
        self.assertIn("Chairperson", dashboard["committee_members"][0]["position"])

    def test_dashboard_renders_single_reports_and_recent_activity_sections(self):
        branch = Branch.objects.create(name="Layout Branch")
        admin = self._create_user(username="layout-admin")
        admin.branch = branch
        admin.save(update_fields=["branch"])
        BranchRole.objects.create(branch=branch, user=admin, role=BranchRole.Role.BRANCH_ADMIN, is_active=True)

        self.client.force_login(admin)
        response = self.client.get(reverse("branch_admin_dashboard"))
        content = response.content.decode()

        self.assertEqual(content.count("Quick access to branch reporting"), 1)
        self.assertEqual(content.count("Leadership Panel"), 1)

    def test_promotion_and_committee_position_management_workflow(self):
        branch = Branch.objects.create(name="Committee Workflow Branch")
        admin = self._create_user(username="committee-admin")
        admin.branch = branch
        admin.save(update_fields=["branch"])
        BranchRole.objects.create(branch=branch, user=admin, role=BranchRole.Role.BRANCH_ADMIN, is_active=True)

        supporter = self._create_user(username="committee-supporter")
        supporter.branch = branch
        supporter.save(update_fields=["branch"])
        BranchRole.objects.create(branch=branch, user=supporter, role=BranchRole.Role.MEMBER, is_active=True)

        promoted = PromoteBranchAdminService.promote(branch, supporter, admin)
        self.assertEqual(promoted.role, BranchRole.Role.BRANCH_ADMIN)

        role = BranchRole.objects.get(branch=branch, user=supporter, role=BranchRole.Role.BRANCH_ADMIN, is_active=True)
        CommitteePosition.objects.create(branch=branch, branch_role=role, position=CommitteePosition.Position.SECRETARY, created_by=admin)
        committee_position = CommitteePosition.objects.get(branch=branch, branch_role=role)
        committee_position.position = CommitteePosition.Position.CHAIRPERSON
        committee_position.save(update_fields=["position"])

        self.assertEqual(committee_position.position, CommitteePosition.Position.CHAIRPERSON)

        committee_position.delete()
        self.assertFalse(CommitteePosition.objects.filter(branch=branch, branch_role=role).exists())

    def test_last_branch_admin_cannot_be_removed(self):
        branch = Branch.objects.create(name="Last Admin Branch")
        admin = self._create_user(username="last-admin")
        admin.branch = branch
        admin.save(update_fields=["branch"])
        BranchRole.objects.create(branch=branch, user=admin, role=BranchRole.Role.BRANCH_ADMIN, is_active=True)

        with self.assertRaises(LastBranchAdminRemovalError):
            RemoveBranchAdminService.remove(branch, admin, admin)

    def _create_user(self, username):
        return get_user_model().objects.create_user(
            username=username,
            email=f"{username}@example.com",
            password="test-pass-123",
        )
