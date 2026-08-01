from django.contrib.auth import get_user_model
from django.db import IntegrityError
from django.test import TestCase

from .models import Branch, BranchPolicy, BranchRole, BranchStatus
from .serializers import BranchPolicySerializer, BranchRoleSerializer, BranchSerializer
from .services.assign_branch_role import AssignBranchRoleService, BranchRoleAlreadyAssigned


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

        BranchRole.objects.create(branch=branch, user=user, role=BranchRole.Role.PRESIDENT)

        with self.assertRaises(IntegrityError):
            BranchRole.objects.create(branch=branch, user=user, role=BranchRole.Role.PRESIDENT)

    def test_user_can_have_multiple_different_roles_in_same_branch(self):
        branch = Branch.objects.create(name="Multi Role Branch")
        user = self._create_user(username="multi-role-user")

        BranchRole.objects.create(branch=branch, user=user, role=BranchRole.Role.PRESIDENT)
        BranchRole.objects.create(branch=branch, user=user, role=BranchRole.Role.STUDENT_VERIFIER)

        roles = BranchRole.objects.filter(branch=branch, user=user)
        self.assertEqual(roles.count(), 2)

    def test_inactive_role_is_not_treated_as_active_duplicate(self):
        branch = Branch.objects.create(name="Inactive Role Branch")
        user = self._create_user(username="inactive-role-user")

        BranchRole.objects.create(branch=branch, user=user, role=BranchRole.Role.PRESIDENT)
        BranchRole.objects.create(branch=branch, user=user, role=BranchRole.Role.PRESIDENT, is_active=False)

        roles = BranchRole.objects.filter(branch=branch, user=user)
        self.assertEqual(roles.count(), 2)

    def test_role_serializer_exposes_role_fields(self):
        branch = Branch.objects.create(name="Role Serializer Branch")
        user = self._create_user(username="role-serializer-user")
        role = BranchRole.objects.create(
            branch=branch,
            user=user,
            role=BranchRole.Role.TRANSPORT_COORDINATOR,
            assigned_by=user,
        )

        serializer = BranchRoleSerializer(role)

        self.assertEqual(serializer.data["role"], BranchRole.Role.TRANSPORT_COORDINATOR)
        self.assertEqual(serializer.data["is_active"], True)

    def test_assign_branch_role_service_assigns_successfully(self):
        branch = Branch.objects.create(name="Service Branch")
        user = self._create_user(username="service-user")
        assigner = self._create_user(username="assigner-user")

        assigned_role = AssignBranchRoleService.assign(
            branch=branch,
            user=user,
            role=BranchRole.Role.PRESIDENT,
            assigned_by=assigner,
        )

        self.assertEqual(assigned_role.branch, branch)
        self.assertEqual(assigned_role.user, user)
        self.assertEqual(assigned_role.role, BranchRole.Role.PRESIDENT)
        self.assertEqual(assigned_role.assigned_by, assigner)
        self.assertTrue(assigned_role.is_active)

    def test_assign_branch_role_service_prevents_duplicate_assignment(self):
        branch = Branch.objects.create(name="Duplicate Service Branch")
        user = self._create_user(username="duplicate-user")

        AssignBranchRoleService.assign(
            branch=branch,
            user=user,
            role=BranchRole.Role.SECRETARY,
        )

        with self.assertRaises(BranchRoleAlreadyAssigned):
            AssignBranchRoleService.assign(
                branch=branch,
                user=user,
                role=BranchRole.Role.SECRETARY,
            )

    def test_assign_branch_role_service_allows_multiple_different_roles(self):
        branch = Branch.objects.create(name="Multi Role Service Branch")
        user = self._create_user(username="multi-service-user")

        AssignBranchRoleService.assign(branch=branch, user=user, role=BranchRole.Role.PRESIDENT)
        AssignBranchRoleService.assign(branch=branch, user=user, role=BranchRole.Role.STUDENT_VERIFIER)

        self.assertEqual(BranchRole.objects.filter(branch=branch, user=user).count(), 2)

    def test_assign_branch_role_service_allows_same_role_for_different_users(self):
        branch = Branch.objects.create(name="Shared Role Service Branch")
        user_one = self._create_user(username="shared-user-one")
        user_two = self._create_user(username="shared-user-two")

        AssignBranchRoleService.assign(branch=branch, user=user_one, role=BranchRole.Role.PRESIDENT)
        assigned_role = AssignBranchRoleService.assign(branch=branch, user=user_two, role=BranchRole.Role.PRESIDENT)

        self.assertEqual(assigned_role.user, user_two)
        self.assertEqual(BranchRole.objects.filter(branch=branch, role=BranchRole.Role.PRESIDENT).count(), 2)

    def _create_user(self, username):
        return get_user_model().objects.create_user(
            username=username,
            email=f"{username}@example.com",
            password="test-pass-123",
        )
