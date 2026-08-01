from uuid import uuid4

from django.utils import timezone

from branches.services.authorization import BranchAdminRequired, is_branch_admin

from ..events import dispatch_event
from ..models import BranchRole, CommitteeAction
from .committee import CommitteeService
from engagement.events import EngagementEvent


class BranchAdminAlreadyAssigned(Exception):
    """Raised when the target user is already an active branch admin."""


class UserNotInBranch(Exception):
    """Raised when the target user is not assigned to the branch."""


class PromoteBranchAdminService:
    @staticmethod
    def promote(branch, target_user, acting_admin):
        if not is_branch_admin(acting_admin, branch):
            raise BranchAdminRequired("Only branch admins can promote another admin.")
        if target_user.branch_id != branch.pk:
            raise UserNotInBranch("The target user is not assigned to this branch.")
        if BranchRole.objects.filter(branch=branch, user=target_user, role=BranchRole.Role.BRANCH_ADMIN, is_active=True).exists():
            raise BranchAdminAlreadyAssigned("The target user is already a branch admin.")

        assignment = BranchRole.objects.create(
            branch=branch,
            user=target_user,
            role=BranchRole.Role.BRANCH_ADMIN,
            assigned_by=acting_admin,
            is_active=True,
        )

        CommitteeService.log_activity(
            branch=branch,
            actor=acting_admin,
            action=CommitteeAction.ADMIN_PROMOTED,
            target_user=target_user,
            metadata={"role": BranchRole.Role.BRANCH_ADMIN},
        )

        correlation_id = uuid4()
        dispatch_event(
            EngagementEvent.BRANCH_ROLE_ASSIGNED,
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
