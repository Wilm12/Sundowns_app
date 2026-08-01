from unittest.mock import patch

from django.contrib.auth import get_user_model
from django.db import IntegrityError
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from engagement.events import EngagementEvent

from journeys.models import Journey, JourneyStatus
from supporters.models import EligibilityReason, SupporterEligibility
from ticketing.models import Ticket
from users.models import User

from .models import Branch, BranchPolicy, BranchRole, BranchStatus
from .serializers import BranchPolicySerializer, BranchRoleSerializer, BranchSerializer
from .services.assign_branch_role import AssignBranchRoleService, BranchRoleAlreadyAssigned
from .services.remove_branch_role import BranchRoleNotAssigned, RemoveBranchRoleService


class BranchModelTests(TestCase):
    def test_branch_defaults_to_active_status(self):
        branch = Branch.objects.create(name="Test Branch")

        self.assertEqual(branch.status, BranchStatus.ACTIVE)
        self.assertIsNone(branch.branch_code)

    def test_serializer_exposes_new_branch_fields(self):
        branch = Branch.objects.create(
            name="Serializer Branch",
            branch_code="UP-TUKS",
            contact_email="branch@example.com",
            contact_phone="0123456789",
            status=BranchStatus.ACTIVE,
        )

        serializer = BranchSerializer(branch)

        self.assertEqual(serializer.data["branch_code"], "UP-TUKS")
        self.assertEqual(serializer.data["contact_email"], "branch@example.com")
        self.assertEqual(serializer.data["contact_phone"], "0123456789")
        self.assertEqual(serializer.data["status"], BranchStatus.ACTIVE)

    def test_branch_creation_auto_creates_policy_with_defaults(self):
        branch = Branch.objects.create(name="Policy Branch")

        policy = BranchPolicy.objects.get(branch=branch)
        self.assertTrue(policy.student_verification_required)
        self.assertEqual(policy.booking_deadline_hours, 24)
        self.assertEqual(policy.maximum_bus_capacity, 100)
        self.assertEqual(policy.attendance_threshold, 70)
        self.assertFalse(policy.allow_guest_supporters)
        self.assertTrue(policy.announcement_requires_approval)

    def test_branch_has_only_one_policy(self):
        branch = Branch.objects.create(name="Single Policy Branch")

        self.assertEqual(BranchPolicy.objects.filter(branch=branch).count(), 1)

    def test_duplicate_policy_creation_is_not_allowed(self):
        branch = Branch.objects.create(name="Duplicate Policy Branch")

        with self.assertRaises(IntegrityError):
            BranchPolicy.objects.create(branch=branch)

    def test_policy_serializer_exposes_policy_fields(self):
        branch = Branch.objects.create(name="Policy Serializer Branch")
        policy = branch.branch_policy

        serializer = BranchPolicySerializer(policy)

        self.assertEqual(serializer.data["student_verification_required"], True)
        self.assertEqual(serializer.data["booking_deadline_hours"], 24)
        self.assertEqual(serializer.data["maximum_bus_capacity"], 100)
        self.assertEqual(serializer.data["attendance_threshold"], 70)

    def test_duplicate_active_roles_cannot_exist_for_same_user_and_branch(self):
        branch = Branch.objects.create(name="Role Branch")
        user = self._create_user(username="role-user")

        BranchRole.objects.create(branch=branch, user=user, role=BranchRole.Role.BRANCH_ADMIN)

        with self.assertRaises(IntegrityError):
            BranchRole.objects.create(branch=branch, user=user, role=BranchRole.Role.BRANCH_ADMIN)

    def test_user_can_have_multiple_different_roles_in_same_branch(self):
        branch = Branch.objects.create(name="Multi Role Branch")
        user = self._create_user(username="multi-role-user")

        BranchRole.objects.create(branch=branch, user=user, role=BranchRole.Role.BRANCH_ADMIN)
        BranchRole.objects.create(branch=branch, user=user, role=BranchRole.Role.MEMBER)

        roles = BranchRole.objects.filter(branch=branch, user=user)
        self.assertEqual(roles.count(), 2)

    def test_inactive_role_is_not_treated_as_active_duplicate(self):
        branch = Branch.objects.create(name="Inactive Role Branch")
        user = self._create_user(username="inactive-role-user")

        BranchRole.objects.create(branch=branch, user=user, role=BranchRole.Role.BRANCH_ADMIN)
        BranchRole.objects.create(branch=branch, user=user, role=BranchRole.Role.BRANCH_ADMIN, is_active=False)

        roles = BranchRole.objects.filter(branch=branch, user=user)
        self.assertEqual(roles.count(), 2)

    def test_role_serializer_exposes_role_fields(self):
        branch = Branch.objects.create(name="Role Serializer Branch")
        user = self._create_user(username="role-serializer-user")
        role = BranchRole.objects.create(
            branch=branch,
            user=user,
            role=BranchRole.Role.BRANCH_ADMIN,
            assigned_by=user,
        )

        serializer = BranchRoleSerializer(role)

        self.assertEqual(serializer.data["role"], BranchRole.Role.BRANCH_ADMIN)
        self.assertEqual(serializer.data["is_active"], True)

    def test_assign_branch_role_service_assigns_successfully(self):
        branch = Branch.objects.create(name="Service Branch")
        user = self._create_user(username="service-user")
        assigner = self._create_user(username="assigner-user")

        assigned_role = AssignBranchRoleService.assign(
            branch=branch,
            user=user,
            role=BranchRole.Role.BRANCH_ADMIN,
            assigned_by=assigner,
        )

        self.assertEqual(assigned_role.branch, branch)
        self.assertEqual(assigned_role.user, user)
        self.assertEqual(assigned_role.role, BranchRole.Role.BRANCH_ADMIN)
        self.assertEqual(assigned_role.assigned_by, assigner)
        self.assertTrue(assigned_role.is_active)

    def test_assign_branch_role_service_prevents_duplicate_assignment(self):
        branch = Branch.objects.create(name="Duplicate Service Branch")
        user = self._create_user(username="duplicate-user")

        AssignBranchRoleService.assign(
            branch=branch,
            user=user,
            role=BranchRole.Role.MEMBER,
        )

        with self.assertRaises(BranchRoleAlreadyAssigned):
            AssignBranchRoleService.assign(
                branch=branch,
                user=user,
                role=BranchRole.Role.MEMBER,
            )

    def test_assign_branch_role_service_allows_multiple_different_roles(self):
        branch = Branch.objects.create(name="Multi Role Service Branch")
        user = self._create_user(username="multi-service-user")

        AssignBranchRoleService.assign(branch=branch, user=user, role=BranchRole.Role.BRANCH_ADMIN)
        AssignBranchRoleService.assign(branch=branch, user=user, role=BranchRole.Role.MEMBER)

        self.assertEqual(BranchRole.objects.filter(branch=branch, user=user).count(), 2)

    def test_assign_branch_role_service_allows_same_role_for_different_users(self):
        branch = Branch.objects.create(name="Shared Role Service Branch")
        user_one = self._create_user(username="shared-user-one")
        user_two = self._create_user(username="shared-user-two")

        AssignBranchRoleService.assign(branch=branch, user=user_one, role=BranchRole.Role.BRANCH_ADMIN)
        assigned_role = AssignBranchRoleService.assign(branch=branch, user=user_two, role=BranchRole.Role.BRANCH_ADMIN)

        self.assertEqual(assigned_role.user, user_two)
        self.assertEqual(BranchRole.objects.filter(branch=branch, role=BranchRole.Role.BRANCH_ADMIN).count(), 2)

    def test_remove_branch_role_service_soft_deactivates_role_when_removed(self):
        branch = Branch.objects.create(name="Remove Role Service Branch")
        user = self._create_user(username="remove-service-user")
        assigned_role = AssignBranchRoleService.assign(
            branch=branch,
            user=user,
            role=BranchRole.Role.MEMBER,
        )

        removed_role = RemoveBranchRoleService.remove(branch=branch, user=user, role=BranchRole.Role.MEMBER)

        self.assertEqual(removed_role.id, assigned_role.id)
        self.assertFalse(removed_role.is_active)
        self.assertFalse(BranchRole.objects.get(pk=assigned_role.pk).is_active)
        self.assertEqual(BranchRole.objects.filter(pk=assigned_role.pk).count(), 1)

    def test_remove_branch_role_service_raises_when_trying_to_remove_unassigned_role(self):
        branch = Branch.objects.create(name="Missing Remove Role Service Branch")
        user = self._create_user(username="missing-remove-service-user")

        with self.assertRaises(BranchRoleNotAssigned):
            RemoveBranchRoleService.remove(branch=branch, user=user, role=BranchRole.Role.MEMBER)

    def test_remove_branch_role_service_leaves_other_roles_active(self):
        branch = Branch.objects.create(name="Leave Other Roles Active Branch")
        user = self._create_user(username="leave-other-user")
        admin = AssignBranchRoleService.assign(branch=branch, user=user, role=BranchRole.Role.BRANCH_ADMIN)
        member = AssignBranchRoleService.assign(branch=branch, user=user, role=BranchRole.Role.MEMBER)

        RemoveBranchRoleService.remove(branch=branch, user=user, role=BranchRole.Role.BRANCH_ADMIN)

        self.assertFalse(BranchRole.objects.get(pk=admin.pk).is_active)
        self.assertTrue(BranchRole.objects.get(pk=member.pk).is_active)

    def test_inactive_role_can_be_reassigned_through_assign_service(self):
        branch = Branch.objects.create(name="Reassign Inactive Role Branch")
        user = self._create_user(username="reassign-user")

        AssignBranchRoleService.assign(branch=branch, user=user, role=BranchRole.Role.BRANCH_ADMIN)
        RemoveBranchRoleService.remove(branch=branch, user=user, role=BranchRole.Role.BRANCH_ADMIN)

        reassigned_role = AssignBranchRoleService.assign(branch=branch, user=user, role=BranchRole.Role.BRANCH_ADMIN)

        self.assertTrue(reassigned_role.is_active)
        self.assertEqual(BranchRole.objects.filter(branch=branch, user=user, role=BranchRole.Role.BRANCH_ADMIN).count(), 2)

    @patch("branches.services.assign_branch_role.dispatch_event")
    def test_assign_branch_role_service_publishes_assigned_event(self, mock_dispatch):
        branch = Branch.objects.create(name="Event Assign Branch")
        user = self._create_user(username="event-assign-user")
        assigner = self._create_user(username="event-assigner")

        AssignBranchRoleService.assign(
            branch=branch,
            user=user,
            role=BranchRole.Role.BRANCH_ADMIN,
            assigned_by=assigner,
        )

        self.assertEqual(mock_dispatch.call_count, 1)
        self.assertEqual(mock_dispatch.call_args.args[0], EngagementEvent.BRANCH_ROLE_ASSIGNED)
        self.assertEqual(mock_dispatch.call_args.kwargs["user"], user)
        self.assertEqual(mock_dispatch.call_args.kwargs["payload"]["branch_id"], branch.pk)
        self.assertEqual(mock_dispatch.call_args.kwargs["payload"]["supporter_id"], user.pk)
        self.assertEqual(mock_dispatch.call_args.kwargs["payload"]["role"], BranchRole.Role.BRANCH_ADMIN)
        self.assertEqual(mock_dispatch.call_args.kwargs["payload"]["assigned_by"], assigner.pk)

    @patch("branches.services.assign_branch_role.dispatch_event")
    def test_duplicate_assignment_does_not_publish_duplicate_events(self, mock_dispatch):
        branch = Branch.objects.create(name="Duplicate Event Branch")
        user = self._create_user(username="duplicate-event-user")

        AssignBranchRoleService.assign(branch=branch, user=user, role=BranchRole.Role.MEMBER)

        with self.assertRaises(BranchRoleAlreadyAssigned):
            AssignBranchRoleService.assign(branch=branch, user=user, role=BranchRole.Role.MEMBER)

        self.assertEqual(mock_dispatch.call_count, 1)

    @patch("branches.services.remove_branch_role.dispatch_event")
    def test_remove_branch_role_service_publishes_removed_event(self, mock_dispatch):
        branch = Branch.objects.create(name="Event Remove Branch")
        user = self._create_user(username="event-remove-user")
        remover = self._create_user(username="event-remover")

        assigned_role = AssignBranchRoleService.assign(branch=branch, user=user, role=BranchRole.Role.MEMBER)
        RemoveBranchRoleService.remove(branch=branch, user=user, role=BranchRole.Role.MEMBER, removed_by=remover)

        self.assertEqual(mock_dispatch.call_count, 1)
        self.assertEqual(mock_dispatch.call_args.args[0], EngagementEvent.BRANCH_ROLE_REMOVED)
        self.assertEqual(mock_dispatch.call_args.kwargs["user"], user)
        self.assertEqual(mock_dispatch.call_args.kwargs["payload"]["branch_id"], branch.pk)
        self.assertEqual(mock_dispatch.call_args.kwargs["payload"]["supporter_id"], user.pk)
        self.assertEqual(mock_dispatch.call_args.kwargs["payload"]["role"], BranchRole.Role.MEMBER)
        self.assertEqual(mock_dispatch.call_args.kwargs["payload"]["removed_by"], remover.pk)

    @patch("branches.services.remove_branch_role.dispatch_event")
    def test_failed_removal_does_not_publish_event(self, mock_dispatch):
        branch = Branch.objects.create(name="Failed Remove Event Branch")
        user = self._create_user(username="failed-remove-event-user")

        with self.assertRaises(BranchRoleNotAssigned):
            RemoveBranchRoleService.remove(branch=branch, user=user, role=BranchRole.Role.MEMBER)

        self.assertEqual(mock_dispatch.call_count, 0)

    def test_dashboard_counts_supporters_and_journey_metrics(self):
        branch = Branch.objects.create(name="Dashboard Branch")
        admin = self._create_user(username="dashboard-admin")
        BranchRole.objects.create(branch=branch, user=admin, role=BranchRole.Role.BRANCH_ADMIN, is_active=True)
        supporter = self._create_user(username="dashboard-supporter")
        supporter.branch = branch
        supporter.save(update_fields=["branch"])
        SupporterEligibility.objects.create(supporter=supporter, is_eligible=True, reason=EligibilityReason.VERIFIED)
        SupporterEligibility.objects.create(supporter=admin, is_eligible=True, reason=EligibilityReason.VERIFIED)

        match = self._create_match()
        journey = Journey.objects.create(supporter=supporter, branch=branch, match=match, status=JourneyStatus.BOOKED)
        ticket = Ticket.objects.create(user=supporter, match=match, status="booked")
        journey.ticket = ticket
        journey.collection_code = "12345678-1234-1234-1234-1234567890ab"
        journey.status = JourneyStatus.TICKET_COLLECTED
        journey.save(update_fields=["ticket", "collection_code", "status", "updated_at"])
        journey.attended_at = timezone.now()
        journey.attended_by = admin
        journey.status = JourneyStatus.MATCH_ATTENDED
        journey.save(update_fields=["attended_at", "attended_by", "status", "updated_at"])

        self.client.force_login(admin)
        response = self.client.get(reverse("branch_dashboard", kwargs={"branch_id": branch.pk}))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Dashboard Branch")
        self.assertContains(response, "1")

    def test_unauthorized_user_cannot_access_dashboard(self):
        branch = Branch.objects.create(name="Restricted Dashboard Branch")
        user = self._create_user(username="restricted-user")
        self.client.force_login(user)

        response = self.client.get(reverse("branch_dashboard", kwargs={"branch_id": branch.pk}))

        self.assertEqual(response.status_code, 403)

    def _create_user(self, username):
        return get_user_model().objects.create_user(
            username=username,
            email=f"{username}@example.com",
            password="test-pass-123",
        )

    def _create_match(self):
        from matches.models import Match
        return Match.objects.create(date=timezone.now(), location="Cape Town", opponent="Ajax")
