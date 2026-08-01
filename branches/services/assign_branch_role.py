from uuid import uuid4

from django.utils import timezone
from engagement.events import EngagementEvent

from branches.services.authorization import BranchAdminRequired

from ..models import BranchRole
from ..events import dispatch_event


class BranchRoleAlreadyAssigned(Exception):
    """Raised when a user already holds the same active role in a branch."""


class AssignBranchRoleService:
    """Thin service for assigning branch roles within a branch."""

    @staticmethod
    def assign(branch, user, role, assigned_by=None):
        if role not in [BranchRole.Role.MEMBER, BranchRole.Role.BRANCH_ADMIN]:
            raise BranchAdminRequired(f"Unsupported role {role}.")
        if BranchRole.objects.filter(
            branch=branch,
            user=user,
            role=role,
            is_active=True,
        ).exists():
            raise BranchRoleAlreadyAssigned(
                f"{user} already has the active role {role} in {branch}."
            )

        assignment = BranchRole.objects.create(
            branch=branch,
            user=user,
            role=role,
            assigned_by=assigned_by,
            is_active=True,
        )

        correlation_id = uuid4()
        dispatch_event(
            EngagementEvent.BRANCH_ROLE_ASSIGNED,
            user=user,
            payload={
                "branch_id": branch.pk,
                "supporter_id": user.pk,
                "role": role,
                "assigned_by": assigned_by.pk if assigned_by else None,
                "assigned_at": timezone.now(),
                "correlation_id": str(correlation_id),
            },
            correlation_id=correlation_id,
        )

        return assignment
