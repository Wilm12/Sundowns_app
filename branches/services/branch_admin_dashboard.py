from django.urls import reverse
from django.utils import timezone

from journeys.models import Journey, JourneyStatus
from matches.models import Match
from supporters.models import StudentVerification, StudentVerificationStatus
from users.models import User

from ..models import Branch, BranchRole, CommitteeAction, CommitteeActivity, CommitteePosition


class BranchAdminDashboardService:
    @staticmethod
    def get_dashboard(admin_user, branch=None):
        if not isinstance(admin_user, User):
            raise TypeError("admin_user must be a User instance")

        admin_branches = Branch.objects.filter(
            branch_roles__user=admin_user,
            branch_roles__role=BranchRole.Role.BRANCH_ADMIN,
            branch_roles__is_active=True,
        ).distinct()

        if branch is None:
            branch = admin_branches.order_by("name").first()

        if branch is None:
            raise ValueError("User is not assigned as a branch admin")

        branch = Branch.objects.get(pk=branch.pk)

        # ------------------------------------------------------------
        # Supporter metrics
        # ------------------------------------------------------------
        total_supporters = BranchRole.objects.filter(
            branch=branch,
            role=BranchRole.Role.MEMBER,
            is_active=True,
        ).count()

        verified_supporters = BranchRole.objects.filter(
            branch=branch,
            role=BranchRole.Role.MEMBER,
            is_active=True,
            user__student_verifications__status=StudentVerificationStatus.VERIFIED,
        ).values("user").distinct().count()

        eligible_supporters = BranchRole.objects.filter(
            branch=branch,
            role=BranchRole.Role.MEMBER,
            is_active=True,
            user__supporter_eligibility__is_eligible=True,
        ).values("user").distinct().count()

        active_members, inactive_members = BranchAdminDashboardService._calculate_membership_status(branch)

        # ------------------------------------------------------------
        # Upcoming match
        # ------------------------------------------------------------
        upcoming_match = Match.objects.filter(
            date__gte=timezone.now()
        ).order_by("date").first()

        if upcoming_match is None:
            upcoming_match = Match.objects.order_by("date").first()

        # ------------------------------------------------------------
        # Journey metrics
        # ------------------------------------------------------------
        if upcoming_match:
            journeys = Journey.objects.filter(branch=branch, match=upcoming_match)

            booked_count = journeys.filter(status=JourneyStatus.BOOKED).count()
            allocated_count = journeys.filter(
                status__in=[
                    JourneyStatus.TICKET_READY,
                    JourneyStatus.MATCH_ATTENDED,
                ],
            ).count()
            attended_count = journeys.filter(
                status=JourneyStatus.MATCH_ATTENDED
            ).count()
            pending_count = journeys.filter(status=JourneyStatus.TICKET_READY).count()

            journey_metrics = {
                "allocated_count": allocated_count,
                "booked_count": booked_count,
                "pending_count": pending_count,
                "attended_count": attended_count,
                "booked_progress": round(
                    (booked_count / max(booked_count, 1)) * 100, 1
                ) if booked_count else 0,
                "allocated_progress": round(
                    (allocated_count / max(booked_count, 1)) * 100, 1
                ) if booked_count else 0,
                "pending_progress": round(
                    (pending_count / max(booked_count, 1)) * 100, 1
                ) if booked_count else 0,
                "attended_progress": round(
                    (attended_count / max(booked_count, 1)) * 100, 1
                ) if booked_count else 0,
            }
        else:
            journey_metrics = {
                "allocated_count": 0,
                "booked_count": 0,
                "pending_count": 0,
                "attended_count": 0,
                "booked_progress": 0,
                "allocated_progress": 0,
                "pending_progress": 0,
                "attended_progress": 0,
            }

        # ------------------------------------------------------------
        # Committee members
        # ------------------------------------------------------------
        committee_members = []
        for committee_position in CommitteePosition.objects.filter(
            branch=branch,
        ).select_related("branch_role", "branch_role__user", "branch_role__assigned_by").order_by("position"):
            role = committee_position.branch_role
            if not role or not role.is_active or role.role != BranchRole.Role.BRANCH_ADMIN:
                continue

            committee_members.append({
                "position": committee_position.get_position_display(),
                "user": role.user,
                "name": role.user.get_full_name() or role.user.username,
                "email": role.user.email,
                "assigned_at": role.assigned_at,
                "assigned_by": (
                    role.assigned_by.get_full_name()
                    or role.assigned_by.username
                ) if role.assigned_by else "System",
            })

        # ------------------------------------------------------------
        # Recent activity
        # ------------------------------------------------------------
        recent_activity = []
        for activity in CommitteeActivity.objects.filter(
            branch=branch
        ).select_related("actor", "target_user").order_by("-created_at")[:10]:
            title = BranchAdminDashboardService._activity_label(activity)
            recent_activity.append({
                "title": title,
                "action": activity.action,
                "actor": (
                    activity.actor.get_full_name()
                    or activity.actor.username
                ) if activity.actor else "System",
                "created_at": activity.created_at,
            })

        # ------------------------------------------------------------
        # Quick actions
        # ------------------------------------------------------------
        quick_action_urls = {
            "verify_supporter": reverse("branch_committee", args=[branch.pk]),
            "allocate_ticket": (
                reverse("match_operations_console", args=[branch.pk, upcoming_match.pk])
                if upcoming_match else "#"
            ),
            "collect_ticket": (
                reverse("match_operations_console", args=[branch.pk, upcoming_match.pk])
                if upcoming_match else "#"
            ),
            "record_attendance": (
                reverse("match_operations_console", args=[branch.pk, upcoming_match.pk])
                if upcoming_match else "#"
            ),
            "view_match_console": (
                reverse("match_operations_console", args=[branch.pk, upcoming_match.pk])
                if upcoming_match else "#"
            ),
            "view_supporters": reverse("branch_detail_page", args=[branch.pk]),
        }

        return {
            "branch": branch,
            "admin_branches": list(admin_branches.order_by("name")),
            "supporter_metrics": {
                "total_supporters": total_supporters,
                "verified_supporters": verified_supporters,
                "eligible_supporters": eligible_supporters,
                "active_members": active_members,
                "inactive_members": inactive_members,
            },
            "verification_metrics": {
                "verified_supporters": verified_supporters,
                "pending_verifications": StudentVerification.objects.filter(
                    user__branch=branch,
                    status=StudentVerificationStatus.PENDING,
                ).count(),
                "rejected_verifications": StudentVerification.objects.filter(
                    user__branch=branch,
                    status=StudentVerificationStatus.REJECTED,
                ).count(),
            },
            "eligibility_metrics": {
                "eligible_supporters": eligible_supporters,
                "ineligible_supporters": total_supporters - eligible_supporters,
            },
            "upcoming_match": upcoming_match,
            "journey_metrics": journey_metrics,
            "committee_members": committee_members,
            "recent_activity": recent_activity,
            "quick_action_urls": quick_action_urls,
        }

    @staticmethod
    def _calculate_membership_status(branch):
        recent_matches = list(
            Match.objects.filter(journeys__branch=branch)
            .order_by("-date")
            .distinct()[:3]
        )

        if not recent_matches:
            return 0, 0

        active_members = 0
        inactive_members = 0

        supporter_roles = BranchRole.objects.filter(
            branch=branch,
            role=BranchRole.Role.MEMBER,
            is_active=True,
        ).values_list("user_id", flat=True)

        for supporter_id in supporter_roles:
            journey_records = list(
                Journey.objects.filter(
                    branch=branch,
                    supporter_id=supporter_id,
                    match__in=recent_matches,
                ).select_related("match").order_by("match__date")
            )

            if not journey_records:
                continue

            attended = any(record.status == JourneyStatus.MATCH_ATTENDED for record in journey_records)
            if attended:
                active_members += 1
            elif len(journey_records) >= len(recent_matches):
                inactive_members += 1

        return active_members, inactive_members

    @staticmethod
    def _activity_label(activity):
        if activity.action == CommitteeAction.ADMIN_PROMOTED:
            return "Branch admin promoted"
        if activity.action == CommitteeAction.ADMIN_REMOVED:
            return "Branch admin removed"
        if activity.action == CommitteeAction.SUPPORTER_VERIFIED:
            return "Supporter verified"
        if activity.action == CommitteeAction.TICKET_ALLOCATED:
            return "Ticket allocated"
        if activity.action == CommitteeAction.TICKET_COLLECTED:
            return "Ticket redeemed"
        if activity.action == CommitteeAction.ATTENDANCE_RECORDED:
            return "Attendance recorded"
        return activity.action.replace("_", " ").title()

