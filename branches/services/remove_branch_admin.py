from uuid import uuid4

from django.utils import timezone

from branches.services.authorization import BranchAdminRequired, is_branch_admin

from ..events import dispatch_event
from ..models import BranchRole, CommitteeAction
from .committee import CommitteeService
from engagement.events import EngagementEvent


class LastBranchAdminRemovalError(Exception):
    """Raised when the last remaining branch admin would be removed."""


class RemoveBranchAdminService:
    @staticmethod
    def remove(branch, target_user, acting_admin):
        if not is_branch_admin(acting_admin, branch):
            raise BranchAdminRequired("Only branch admins can remove another admin.")

        admin_count = BranchRole.objects.filter(branch=branch, role=BranchRole.Role.BRANCH_ADMIN, is_active=True).count()
        if admin_count <= 1 and target_user.pk == acting_admin.pk:
            raise LastBranchAdminRemovalError("The branch must retain at least one branch admin.")

        assignment = BranchRole.objects.filter(
            branch=branch,
            user=target_user,
            role=BranchRole.Role.BRANCH_ADMIN,
            is_active=True,
        ).order_by("-assigned_at").first()
        if assignment is None:
            return None

        assignment.is_active = False
        assignment.save(update_fields=["is_active"])

        CommitteeService.log_activity(
            branch=branch,
            actor=acting_admin,
            action=CommitteeAction.ADMIN_REMOVED,
            target_user=target_user,
            metadata={"role": BranchRole.Role.BRANCH_ADMIN},
        )

        correlation_id = uuid4()
        dispatch_event(
            EngagementEvent.BRANCH_ROLE_REMOVED,
            user=target_user,
            payload={
                "branch_id": branch.pk,
                "target_user_id": target_user.pk,
                "acted_by": acting_admin.pk if acting_admin else None,
                "role": BranchRole.Role.BRANCH_ADMIN,
                "timestamp": timezone.now(),
                "correlation_id": str(correlation_id),
            },
            correlation_id=correlation_id,
        )

        return assignment
