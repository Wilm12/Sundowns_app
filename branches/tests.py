from unittest.mock import patch

from django.contrib.auth import get_user_model
from django.db import IntegrityError
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from engagement.events import EngagementEvent

from journeys.models import Journey, JourneyStatus
from matches.models import Match
from supporters.models import EligibilityReason, SupporterEligibility, StudentVerification
from ticketing.models import Ticket
from users.models import User

from .models import Branch, BranchPolicy, BranchRole, BranchStatus, CommitteeActivity, CommitteeAction
from .serializers import BranchPolicySerializer, BranchRoleSerializer, BranchSerializer
from .services.assign_branch_role import AssignBranchRoleService, BranchRoleAlreadyAssigned
from .services.committee import CommitteeService
from .services.promote_branch_admin import BranchAdminAlreadyAssigned, PromoteBranchAdminService, UserNotInBranch
from .services.remove_branch_admin import LastBranchAdminRemovalError, RemoveBranchAdminService
from .services.remove_branch_role import BranchRoleNotAssigned, RemoveBranchRoleService
from branches.services.authorization import BranchAdminRequired


class CommitteeManagementTests(TestCase):
    def test_admin_can_promote_another_member(self):
        branch = Branch.objects.create(name="Committee Branch")
        acting_admin = self._create_user(username="committee-admin")
        member = self._create_user(username="committee-member")
        acting_admin.branch = branch
        acting_admin.save(update_fields=["branch"])
        member.branch = branch
        member.save(update_fields=["branch"])
        BranchRole.objects.create(branch=branch, user=acting_admin, role=BranchRole.Role.BRANCH_ADMIN, is_active=True)

        promoted = PromoteBranchAdminService.promote(branch=branch, target_user=member, acting_admin=acting_admin)

        self.assertEqual(promoted.role, BranchRole.Role.BRANCH_ADMIN)
        self.assertTrue(BranchRole.objects.filter(branch=branch, user=member, role=BranchRole.Role.BRANCH_ADMIN, is_active=True).exists())

    def test_non_admin_cannot_promote(self):
        branch = Branch.objects.create(name="Non Admin Branch")
        member = self._create_user(username="non-admin-member")
        actor = self._create_user(username="non-admin-actor")
        member.branch = branch
        member.save(update_fields=["branch"])
        actor.branch = branch
        actor.save(update_fields=["branch"])

        with self.assertRaises(BranchAdminRequired):
            PromoteBranchAdminService.promote(branch=branch, target_user=member, acting_admin=actor)

    def test_duplicate_promotion_is_prevented(self):
        branch = Branch.objects.create(name="Duplicate Branch")
        acting_admin = self._create_user(username="duplicate-admin")
        member = self._create_user(username="duplicate-member")
        acting_admin.branch = branch
        acting_admin.save(update_fields=["branch"])
        member.branch = branch
        member.save(update_fields=["branch"])
        BranchRole.objects.create(branch=branch, user=acting_admin, role=BranchRole.Role.BRANCH_ADMIN, is_active=True)
        BranchRole.objects.create(branch=branch, user=member, role=BranchRole.Role.BRANCH_ADMIN, is_active=True)

        with self.assertRaises(BranchAdminAlreadyAssigned):
            PromoteBranchAdminService.promote(branch=branch, target_user=member, acting_admin=acting_admin)

    def test_admin_can_remove_another_admin(self):
        branch = Branch.objects.create(name="Remove Branch")
        acting_admin = self._create_user(username="remove-admin")
        target_admin = self._create_user(username="target-admin")
        acting_admin.branch = branch
        acting_admin.save(update_fields=["branch"])
        target_admin.branch = branch
        target_admin.save(update_fields=["branch"])
        BranchRole.objects.create(branch=branch, user=acting_admin, role=BranchRole.Role.BRANCH_ADMIN, is_active=True)
        BranchRole.objects.create(branch=branch, user=target_admin, role=BranchRole.Role.BRANCH_ADMIN, is_active=True)

        removed = RemoveBranchAdminService.remove(branch=branch, target_user=target_admin, acting_admin=acting_admin)

        self.assertFalse(removed.is_active)
        self.assertFalse(BranchRole.objects.filter(branch=branch, user=target_admin, role=BranchRole.Role.BRANCH_ADMIN, is_active=True).exists())

    def test_last_admin_cannot_be_removed(self):
        branch = Branch.objects.create(name="Last Admin Branch")
        acting_admin = self._create_user(username="last-admin")
        acting_admin.branch = branch
        acting_admin.save(update_fields=["branch"])
        BranchRole.objects.create(branch=branch, user=acting_admin, role=BranchRole.Role.BRANCH_ADMIN, is_active=True)

        with self.assertRaises(LastBranchAdminRemovalError):
            RemoveBranchAdminService.remove(branch=branch, target_user=acting_admin, acting_admin=acting_admin)

    def test_committee_list_returns_only_admins(self):
        branch = Branch.objects.create(name="Committee List Branch")
        admin = self._create_user(username="list-admin")
        member = self._create_user(username="list-member")
        admin.branch = branch
        admin.save(update_fields=["branch"])
        member.branch = branch
        member.save(update_fields=["branch"])
        BranchRole.objects.create(branch=branch, user=admin, role=BranchRole.Role.BRANCH_ADMIN, is_active=True)
        BranchRole.objects.create(branch=branch, user=member, role=BranchRole.Role.MEMBER, is_active=True)

        committee = CommitteeService.list_committee_members(branch)

        self.assertEqual(list(committee), [admin])

    def test_activity_log_records_actions(self):
        branch = Branch.objects.create(name="Activity Branch")
        actor = self._create_user(username="activity-actor")
        target = self._create_user(username="activity-target")
        actor.branch = branch
        actor.save(update_fields=["branch"])
        target.branch = branch
        target.save(update_fields=["branch"])
        BranchRole.objects.create(branch=branch, user=actor, role=BranchRole.Role.BRANCH_ADMIN, is_active=True)
        PromoteBranchAdminService.promote(branch=branch, target_user=target, acting_admin=actor)

        activity = CommitteeActivity.objects.filter(branch=branch, action=CommitteeAction.ADMIN_PROMOTED).latest("created_at")
        self.assertEqual(activity.actor, actor)
        self.assertEqual(activity.target_user, target)

    def test_promote_publishes_event(self):
        branch = Branch.objects.create(name="Event Branch")
        acting_admin = self._create_user(username="event-admin")
        member = self._create_user(username="event-member")
        acting_admin.branch = branch
        acting_admin.save(update_fields=["branch"])
        member.branch = branch
        member.save(update_fields=["branch"])
        BranchRole.objects.create(branch=branch, user=acting_admin, role=BranchRole.Role.BRANCH_ADMIN, is_active=True)

        with patch("branches.services.promote_branch_admin.dispatch_event") as mock_dispatch:
            PromoteBranchAdminService.promote(branch=branch, target_user=member, acting_admin=acting_admin)

        self.assertEqual(mock_dispatch.call_count, 1)

    def _create_user(self, username):
        return get_user_model().objects.create_user(
            username=username,
            email=f"{username}@example.com",
            password="test-pass-123",
        )


class MatchOperationsConsoleTests(TestCase):
    def test_branch_admin_can_access_match_operations_console(self):
        branch = Branch.objects.create(name="Match Ops Branch")
        match = Match.objects.create(date=timezone.now(), location="Loftus", opponent="Orlando Pirates")
        admin = self._create_user(username="ops-admin")
        admin.branch = branch
        admin.save(update_fields=["branch"])
        BranchRole.objects.create(branch=branch, user=admin, role=BranchRole.Role.BRANCH_ADMIN, is_active=True)

        self.client.force_login(admin)
        response = self.client.get(reverse("match_operations_console", args=[branch.pk, match.pk]))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Match Operations")

    def test_non_admin_cannot_access_match_operations_console(self):
        branch = Branch.objects.create(name="No Access Branch")
        match = Match.objects.create(date=timezone.now(), location="Loftus", opponent="Kaizer Chiefs")
        member = self._create_user(username="ops-member")
        member.branch = branch
        member.save(update_fields=["branch"])

        self.client.force_login(member)
        response = self.client.get(reverse("match_operations_console", args=[branch.pk, match.pk]))

        self.assertEqual(response.status_code, 403)

    def test_console_counts_match_progress(self):
        branch = Branch.objects.create(name="Metrics Branch")
        match = Match.objects.create(date=timezone.now(), location="Loftus", opponent="Chippa United")
        supporter = self._create_user(username="metrics-supporter")
        supporter.branch = branch
        supporter.save(update_fields=["branch"])

        Journey.objects.create(supporter=supporter, branch=branch, match=match, status=JourneyStatus.BOOKED)
        Journey.objects.create(supporter=self._create_user(username="metrics-allocated"), branch=branch, match=match, status=JourneyStatus.TICKET_READY)
        Journey.objects.create(supporter=self._create_user(username="metrics-collected"), branch=branch, match=match, status=JourneyStatus.TICKET_COLLECTED)
        Journey.objects.create(supporter=self._create_user(username="metrics-attended"), branch=branch, match=match, status=JourneyStatus.MATCH_ATTENDED)

        from journeys.services.match_operations import MatchOperationsService
        console = MatchOperationsService.get_console(branch, match)

        self.assertEqual(console["booked_count"], 1)
        self.assertEqual(console["allocated_count"], 1)
        self.assertEqual(console["collected_count"], 1)
        self.assertEqual(console["attended_count"], 1)
        self.assertEqual(console["pending_collections"], 1)
        self.assertEqual(console["no_shows"], 1)

    def test_console_searches_by_supporter_name(self):
        branch = Branch.objects.create(name="Search Branch")
        match = Match.objects.create(date=timezone.now(), location="Loftus", opponent="Mamelodi Sundowns")
        matching_supporter = self._create_user(username="john_search")
        matching_supporter.branch = branch
        matching_supporter.save(update_fields=["branch"])
        Journey.objects.create(supporter=matching_supporter, branch=branch, match=match, status=JourneyStatus.BOOKED)

        other_supporter = self._create_user(username="sarah_search")
        other_supporter.branch = branch
        other_supporter.save(update_fields=["branch"])
        Journey.objects.create(supporter=other_supporter, branch=branch, match=match, status=JourneyStatus.BOOKED)

        from journeys.services.match_operations import MatchOperationsService
        console = MatchOperationsService.get_console(branch, match, search_query="john")

        self.assertEqual(console["journeys"].count(), 1)
        self.assertEqual(console["journeys"].first().supporter, matching_supporter)

    def test_console_searches_by_student_number(self):
        branch = Branch.objects.create(name="Student Search Branch")
        match = Match.objects.create(date=timezone.now(), location="Loftus", opponent="Stellenbosch")
        matching_supporter = self._create_user(username="student-match")
        matching_supporter.branch = branch
        matching_supporter.save(update_fields=["branch"])
        StudentVerification.objects.create(user=matching_supporter, student_number="u12345678", university="TUKS")
        Journey.objects.create(supporter=matching_supporter, branch=branch, match=match, status=JourneyStatus.BOOKED)

        other_supporter = self._create_user(username="other-student")
        other_supporter.branch = branch
        other_supporter.save(update_fields=["branch"])
        StudentVerification.objects.create(user=other_supporter, student_number="u99999999", university="TUKS")
        Journey.objects.create(supporter=other_supporter, branch=branch, match=match, status=JourneyStatus.BOOKED)

        from journeys.services.match_operations import MatchOperationsService
        console = MatchOperationsService.get_console(branch, match, search_query="u12345678")

        self.assertEqual(console["journeys"].count(), 1)
        self.assertEqual(console["journeys"].first().supporter, matching_supporter)

    def test_quick_action_updates_the_correct_journey(self):
        branch = Branch.objects.create(name="Action Branch")
        match = Match.objects.create(date=timezone.now(), location="Loftus", opponent="Golden Arrows")
        admin = self._create_user(username="action-admin")
        admin.branch = branch
        admin.save(update_fields=["branch"])
        BranchRole.objects.create(branch=branch, user=admin, role=BranchRole.Role.BRANCH_ADMIN, is_active=True)
        supporter = self._create_user(username="action-supporter")
        supporter.branch = branch
        supporter.save(update_fields=["branch"])
        journey = Journey.objects.create(supporter=supporter, branch=branch, match=match, status=JourneyStatus.BOOKED)

        self.client.force_login(admin)
        response = self.client.post(
            reverse("match_operations_console", args=[branch.pk, match.pk]),
            {"action": "allocate", "journey_id": journey.pk},
        )

        journey.refresh_from_db()
        self.assertEqual(journey.status, JourneyStatus.TICKET_READY)
        self.assertEqual(response.status_code, 302)

    def _create_user(self, username):
        return get_user_model().objects.create_user(
            username=username,
            email=f"{username}@example.com",
            password="test-pass-123",
        )


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
