from django.urls import reverse
from django.utils import timezone

from analytics.services import BranchAnalyticsService
from journeys.models import Journey, JourneyStatus
from matches.models import Match
from supporters.models import StudentVerification, StudentVerificationStatus, SupporterEligibility
from users.models import User

from ..models import Branch, BranchRole, CommitteeAction, CommitteeActivity, CommitteePosition, MatchAllocation


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
        assigned_users = User.objects.filter(branch=branch).distinct()
        supporters = assigned_users.exclude(
            branch_roles__branch=branch,
            branch_roles__role=BranchRole.Role.BRANCH_ADMIN,
            branch_roles__is_active=True,
        ).distinct()

        total_supporters = assigned_users.count()

        verified_supporters = 0
        eligible_supporters = 0
        active_members = 0

        for supporter in supporters:
            latest_verification = (
                StudentVerification.objects.filter(user=supporter)
                .order_by("-created_at")
                .first()
            )
            latest_eligibility = (
                SupporterEligibility.objects.filter(supporter=supporter)
                .order_by("-updated_at")
                .first()
            )

            is_verified = bool(
                latest_verification
                and latest_verification.status in {
                    StudentVerificationStatus.APPROVED,
                    StudentVerificationStatus.VERIFIED,
                }
            )
            is_eligible = bool(latest_eligibility and latest_eligibility.is_eligible) or is_verified

            if is_verified:
                verified_supporters += 1
            if is_eligible:
                eligible_supporters += 1
            if is_verified and supporter.is_active and is_eligible:
                active_members += 1

        inactive_members = max(total_supporters - active_members, 0)

        # ------------------------------------------------------------
        # Upcoming / relevant match
        # ------------------------------------------------------------
        # First prefer an explicitly published operational match on the branch.
        operational_match = getattr(branch, "operational_match", None)

        # If none published, fall back to the earliest branch match with
        # journeys in BOOKED or TICKET_READY state.
        if not operational_match:
            operational_match = (
                Match.objects.filter(
                    journeys__branch=branch,
                    journeys__status__in=[
                        JourneyStatus.BOOKED,
                        JourneyStatus.TICKET_READY,
                    ],
                )
                .order_by("date")
                .distinct()
                .first()
            )

        branch_match = (
            Match.objects.filter(journeys__branch=branch)
            .order_by("-date")
            .distinct()
            .first()
        )

        upcoming_match = Match.objects.filter(
            date__gte=timezone.now()
        ).order_by("date").first()

        dashboard_match = operational_match or branch_match or upcoming_match
        if dashboard_match is None:
            dashboard_match = Match.objects.order_by("date").first()

        # ------------------------------------------------------------
        # Journey metrics
        # ------------------------------------------------------------
        if dashboard_match:
            journeys = Journey.objects.filter(branch=branch, match=dashboard_match)

            booked_count = journeys.filter(
                status__in=[
                    JourneyStatus.BOOKED,
                    JourneyStatus.TICKET_READY,
                    JourneyStatus.TICKET_COLLECTED,
                    JourneyStatus.MATCH_ATTENDED,
                ],
            ).count()
            allocation_record = MatchAllocation.objects.filter(branch=branch, match=dashboard_match).first()
            allocated_count = allocation_record.allocated_tickets if allocation_record else (
                journeys.filter(status__in=[JourneyStatus.TICKET_READY, JourneyStatus.MATCH_ATTENDED]).count()
                + journeys.filter(ticket__isnull=False, status=JourneyStatus.BOOKED).count()
            )
            attended_count = journeys.filter(status__in=[JourneyStatus.TICKET_COLLECTED, JourneyStatus.MATCH_ATTENDED]).count()
            pending_count = journeys.filter(status=JourneyStatus.TICKET_READY).count()

            branch_match_analytics = BranchAnalyticsService.get_branch_match_metrics(branch, dashboard_match)
            journey_metrics = {
                "allocated_count": allocated_count,
                "booked_count": booked_count,
                "pending_count": pending_count,
                "attended_count": attended_count,
                "booked_progress": round((booked_count / max(booked_count, 1)) * 100, 1) if booked_count else 0,
                "allocated_progress": round((allocated_count / max(booked_count, 1)) * 100, 1) if booked_count else 0,
                "pending_progress": round((pending_count / max(booked_count, 1)) * 100, 1) if booked_count else 0,
                "attended_progress": round((attended_count / max(booked_count, 1)) * 100, 1) if booked_count else 0,
            }
        else:
            branch_match_analytics = {
                "match": None,
                "booked": 0,
                "attended": 0,
                "attendance_rate": 0,
                "verification_completed": 0,
            }
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

        branch_history = BranchAnalyticsService.get_branch_performance(branch)[:10]

        # ------------------------------------------------------------
        # Committee members
        # ------------------------------------------------------------
        if not CommitteePosition.objects.filter(branch=branch).exists():
            first_admin_role = BranchRole.objects.filter(
                branch=branch,
                role=BranchRole.Role.BRANCH_ADMIN,
                is_active=True,
            ).order_by("assigned_at").first()
            if first_admin_role:
                CommitteePosition.objects.create(
                    branch=branch,
                    branch_role=first_admin_role,
                    position=CommitteePosition.Position.CHAIRPERSON,
                    created_by=admin_user,
                )

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
                reverse("match_operations_console", args=[branch.pk, dashboard_match.pk])
                if dashboard_match else "#"
            ),
            "collect_ticket": (
                reverse("match_operations_console", args=[branch.pk, dashboard_match.pk])
                if dashboard_match else "#"
            ),
            "record_attendance": (
                reverse("match_operations_console", args=[branch.pk, dashboard_match.pk])
                if dashboard_match else "#"
            ),
            "view_match_console": (
                reverse("match_operations_console", args=[branch.pk, dashboard_match.pk])
                if dashboard_match else "#"
            ),
            "view_supporters": reverse("branch_detail_page", args=[branch.pk]),
        }

        return {
            "branch": branch,
            "admin_branches": list(admin_branches.order_by("name")),
            "dashboard_match": dashboard_match,
            "selected_match": dashboard_match,
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
            "branch_analytics": branch_match_analytics,
            "branch_performance": branch_history,
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

