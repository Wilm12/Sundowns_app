from django.urls import reverse
from django.utils import timezone

from journeys.models import Journey, JourneyStatus
from matches.models import Match
from supporters.models import StudentVerification, StudentVerificationStatus, SupporterEligibility
from users.models import User

from ..models import Branch, BranchRole, CommitteeAction, CommitteeActivity


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

        supporters = User.objects.filter(branch=branch)
        total_supporters = supporters.count()
        verified_supporters = User.objects.filter(
            branch=branch,
            student_verifications__status=StudentVerificationStatus.VERIFIED,
        ).distinct().count()
        eligible_supporters = User.objects.filter(
            branch=branch,
            supporter_eligibility__is_eligible=True,
        ).distinct().count()
        branch_admin_count = BranchRole.objects.filter(
            branch=branch,
            role=BranchRole.Role.BRANCH_ADMIN,
            is_active=True,
        ).count()

        upcoming_match = Match.objects.filter(date__gte=timezone.now()).order_by("date").first()
        if upcoming_match is None:
            upcoming_match = Match.objects.order_by("date").first()

        journey_metrics = {}
        if upcoming_match:
            journeys = Journey.objects.filter(branch=branch, match=upcoming_match)
            booked_count = journeys.filter(status=JourneyStatus.BOOKED).count()
            allocated_count = journeys.filter(status__in=[JourneyStatus.TICKET_READY, JourneyStatus.TICKET_COLLECTED, JourneyStatus.MATCH_ATTENDED]).count()
            collected_count = journeys.filter(status__in=[JourneyStatus.TICKET_COLLECTED, JourneyStatus.MATCH_ATTENDED]).count()
            attended_count = journeys.filter(status=JourneyStatus.MATCH_ATTENDED).count()
            pending_collection = max(allocated_count - collected_count, 0)
            no_shows = max(booked_count - attended_count, 0)

            journey_metrics = {
                "booked_count": booked_count,
                "allocated_count": allocated_count,
                "collected_count": collected_count,
                "attended_count": attended_count,
                "pending_collection": pending_collection,
                "no_shows": no_shows,
                "booked_progress": round((booked_count / max(booked_count, 1)) * 100, 1) if booked_count else 0,
                "allocated_progress": round((allocated_count / max(booked_count, 1)) * 100, 1) if booked_count else 0,
                "collected_progress": round((collected_count / max(booked_count, 1)) * 100, 1) if booked_count else 0,
                "attended_progress": round((attended_count / max(booked_count, 1)) * 100, 1) if booked_count else 0,
            }
        else:
            journey_metrics = {
                "booked_count": 0,
                "allocated_count": 0,
                "collected_count": 0,
                "attended_count": 0,
                "pending_collection": 0,
                "no_shows": 0,
                "booked_progress": 0,
                "allocated_progress": 0,
                "collected_progress": 0,
                "attended_progress": 0,
            }

        committee_members = []
        for role in BranchRole.objects.filter(
            branch=branch,
            role=BranchRole.Role.BRANCH_ADMIN,
            is_active=True,
        ).select_related("user", "assigned_by").order_by("assigned_at"):
            committee_members.append({
                "user": role.user,
                "name": role.user.get_full_name() or role.user.username,
                "email": role.user.email,
                "assigned_at": role.assigned_at,
                "assigned_by": role.assigned_by.get_full_name() or role.assigned_by.username if role.assigned_by else "System",
            })

        recent_activity = []
        for activity in CommitteeActivity.objects.filter(branch=branch).select_related("actor", "target_user").order_by("-created_at")[:10]:
            title = BranchAdminDashboardService._activity_label(activity)
            recent_activity.append({
                "title": title,
                "action": activity.action,
                "actor": activity.actor.get_full_name() or activity.actor.username if activity.actor else "System",
                "created_at": activity.created_at,
            })

        quick_action_urls = {
            "verify_supporter": reverse("branch_committee", args=[branch.pk]),
            "allocate_ticket": reverse("match_operations_console", args=[branch.pk, upcoming_match.pk]) if upcoming_match else "#",
            "collect_ticket": reverse("match_operations_console", args=[branch.pk, upcoming_match.pk]) if upcoming_match else "#",
            "record_attendance": reverse("match_operations_console", args=[branch.pk, upcoming_match.pk]) if upcoming_match else "#",
            "view_match_console": reverse("match_operations_console", args=[branch.pk, upcoming_match.pk]) if upcoming_match else "#",
            "view_supporters": reverse("branch_detail_page", args=[branch.pk]),
        }

        return {
            "branch": branch,
            "admin_branches": list(admin_branches.order_by("name")),
            "supporter_metrics": {
                "total_supporters": total_supporters,
                "verified_supporters": verified_supporters,
                "eligible_supporters": eligible_supporters,
                "branch_admins": branch_admin_count,
            },
            "verification_metrics": {
                "verified_supporters": verified_supporters,
                "pending_verifications": StudentVerification.objects.filter(user__branch=branch, status=StudentVerificationStatus.PENDING).count(),
                "rejected_verifications": StudentVerification.objects.filter(user__branch=branch, status=StudentVerificationStatus.REJECTED).count(),
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
            return "Ticket collected"
        if activity.action == CommitteeAction.ATTENDANCE_RECORDED:
            return "Attendance recorded"
        return activity.action.replace("_", " ").title()
