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

from .models import Branch, BranchPolicy, BranchRole, BranchStatus, CommitteeActivity, CommitteeAction
from .serializers import BranchPolicySerializer, BranchRoleSerializer, BranchSerializer
from .services.assign_branch_role import AssignBranchRoleService, BranchRoleAlreadyAssigned
from .services.branch_admin_dashboard import BranchAdminDashboardService
from .services.committee import CommitteeService
from .services.promote_branch_admin import BranchAdminAlreadyAssigned, PromoteBranchAdminService, UserNotInBranch
from .services.remove_branch_admin import LastBranchAdminRemovalError, RemoveBranchAdminService
from .services.remove_branch_role import BranchRoleNotAssigned, RemoveBranchRoleService
from branches.services.authorization import BranchAdminRequired


class BranchAdminDashboardTests(TestCase):
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

        StudentVerification.objects.create(user=supporter_one, student_number="u10001", university="TUKS", status=StudentVerificationStatus.VERIFIED)
        StudentVerification.objects.create(user=supporter_two, student_number="u10002", university="TUKS", status=StudentVerificationStatus.PENDING)
        SupporterEligibility.objects.create(supporter=supporter_one, is_eligible=True, reason=EligibilityReason.VERIFIED)
        SupporterEligibility.objects.create(supporter=supporter_two, is_eligible=False, reason=EligibilityReason.VERIFICATION_PENDING)

        match = Match.objects.create(date=timezone.now(), location="Loftus", opponent="Orlando Pirates")
        Journey.objects.create(supporter=supporter_one, branch=branch, match=match, status=JourneyStatus.BOOKED)
        Journey.objects.create(supporter=supporter_two, branch=branch, match=match, status=JourneyStatus.TICKET_COLLECTED)

        dashboard = BranchAdminDashboardService.get_dashboard(admin, branch=branch)

        self.assertEqual(dashboard["supporter_metrics"]["total_supporters"], 2)
        self.assertEqual(dashboard["supporter_metrics"]["committee_members"], 1)
        self.assertEqual(dashboard["supporter_metrics"]["verified_supporters"], 1)
        self.assertEqual(dashboard["supporter_metrics"]["eligible_supporters"], 1)
        self.assertEqual(dashboard["journey_metrics"]["booked_count"], 1)
        self.assertEqual(dashboard["journey_metrics"]["collected_count"], 1)

    def _create_user(self, username):
        return get_user_model().objects.create_user(
            username=username,
            email=f"{username}@example.com",
            password="test-pass-123",
        )
