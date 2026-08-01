from uuid import uuid4

from django.utils import timezone
from engagement.events import EngagementEvent

from ..models import BranchRole
from ..events import dispatch_event


class BranchRoleNotAssigned(Exception):
    """Raised when a role assignment does not exist or is already inactive."""


class RemoveBranchRoleService:
    """Soft-remove an active branch role assignment by deactivating it."""

    @staticmethod
    def remove(branch, user, role, removed_by=None):
        assignment = BranchRole.objects.filter(
            branch=branch,
            user=user,
            role=role,
            is_active=True,
        ).order_by("-assigned_at").first()

        if assignment is None:
            raise BranchRoleNotAssigned(
                f"{user} does not currently hold the role {role} in {branch}."
            )

        assignment.is_active = False
        assignment.save(update_fields=["is_active"])

        correlation_id = uuid4()
        dispatch_event(
            EngagementEvent.BRANCH_ROLE_REMOVED,
            user=user,
            payload={
                "branch_id": branch.pk,
                "supporter_id": user.pk,
                "role": role,
                "removed_by": removed_by.pk if removed_by else None,
                "removed_at": timezone.now(),
                "correlation_id": str(correlation_id),
            },
            correlation_id=correlation_id,
        )

        return assignment
