from users.models import User

from ..models import BranchRole, CommitteeActivity, CommitteeAction, CommitteePosition


class CommitteeService:
    @staticmethod
    def list_committee_members(branch):
        return (
            User.objects.filter(
                branch_roles__branch=branch,
                branch_roles__role=BranchRole.Role.BRANCH_ADMIN,
                branch_roles__is_active=True,
            )
            .order_by("username")
            .distinct()
        )

    @staticmethod
    def get_leadership_positions(branch):
        positions = {
            CommitteePosition.Position(position_value).label: None
            for position_value, _ in CommitteePosition.Position.choices
        }
        for committee_position in CommitteePosition.objects.filter(branch=branch).select_related("branch_role", "branch_role__user"):
            if committee_position.branch_role and committee_position.branch_role.is_active:
                positions[committee_position.get_position_display()] = committee_position.branch_role.user
        return positions

    @staticmethod
    def is_branch_admin(user, branch):
        return BranchRole.objects.filter(
            branch=branch,
            user=user,
            role=BranchRole.Role.BRANCH_ADMIN,
            is_active=True,
        ).exists()

    @staticmethod
    def log_activity(branch, actor, action, target_user=None, metadata=None):
        return CommitteeActivity.objects.create(
            branch=branch,
            actor=actor,
            action=action,
            target_user=target_user,
            metadata=metadata or {},
        )

    @staticmethod
    def get_committee_stats(branch):
        total_supporters = User.objects.filter(branch=branch).count()
        verified_supporters = User.objects.filter(
            branch=branch,
            student_verifications__status="VERIFIED",
        ).distinct().count()
        active_journeys = 0
        return {
            "total_supporters": total_supporters,
            "verified_supporters": verified_supporters,
            "active_journeys": active_journeys,
        }
