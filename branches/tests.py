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

        self.assertEqual(dashboard["supporter_metrics"]["total_supporters"], 2)
        self.assertEqual(dashboard["supporter_metrics"]["verified_supporters"], 1)
        self.assertEqual(dashboard["supporter_metrics"]["eligible_supporters"], 1)
        self.assertEqual(dashboard["supporter_metrics"]["active_members"], 1)
        self.assertEqual(dashboard["journey_metrics"]["allocated_count"], 2)
        self.assertEqual(dashboard["journey_metrics"]["booked_count"], 1)
        self.assertEqual(dashboard["journey_metrics"]["pending_count"], 1)
        self.assertEqual(dashboard["journey_metrics"]["attended_count"], 1)

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

    def _create_user(self, username):
        return get_user_model().objects.create_user(
            username=username,
            email=f"{username}@example.com",
            password="test-pass-123",
        )
