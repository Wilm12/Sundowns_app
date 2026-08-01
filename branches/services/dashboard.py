from datetime import datetime

from django.db.models import Count, Q

from journeys.models import Journey, JourneyStatus
from supporters.models import SupporterEligibility
from ticketing.models import Ticket
from users.models import User

from ..models import Branch


class BranchDashboardService:
    @staticmethod
    def get_dashboard(branch):
        branch = Branch.objects.get(pk=branch.pk if isinstance(branch, Branch) else branch)

        supporters = User.objects.filter(branch=branch)
        supporters_count = supporters.count()
        verified_count = SupporterEligibility.objects.filter(
            supporter__branch=branch,
            is_eligible=True,
        ).count()
        eligible_count = SupporterEligibility.objects.filter(
            supporter__branch=branch,
            is_eligible=True,
        ).count()

        journeys_open = Journey.objects.filter(branch=branch, status=JourneyStatus.OPEN).count()
        journeys_booked = Journey.objects.filter(branch=branch, status=JourneyStatus.BOOKED).count()
        tickets_allocated = Journey.objects.filter(branch=branch, status__in=[JourneyStatus.TICKET_READY, JourneyStatus.TICKET_COLLECTED, JourneyStatus.MATCH_ATTENDED]).count()
        tickets_collected = Journey.objects.filter(branch=branch, status__in=[JourneyStatus.TICKET_COLLECTED, JourneyStatus.MATCH_ATTENDED]).count()
        attendance_recorded = Journey.objects.filter(branch=branch, status=JourneyStatus.MATCH_ATTENDED).count()

        booked_count = max(journeys_booked, 1)
        allocated_count = max(tickets_allocated, 1)
        collected_count = max(tickets_collected, 1)

        attendance_rate = round((attendance_recorded / booked_count) * 100, 1) if booked_count else 0
        collection_rate = round((tickets_collected / allocated_count) * 100, 1) if allocated_count else 0
        no_show_rate = max(booked_count - attendance_recorded, 0)

        recent_activity = []
        recent_supporters = supporters.order_by('-date_joined')[:5]
        recent_verified = SupporterEligibility.objects.filter(supporter__branch=branch).order_by('-pk')[:5]
        recent_collections = Journey.objects.filter(branch=branch, status__in=[JourneyStatus.TICKET_COLLECTED, JourneyStatus.MATCH_ATTENDED]).order_by('-updated_at')[:5]
        recent_attendance = Journey.objects.filter(branch=branch, status=JourneyStatus.MATCH_ATTENDED).order_by('-attended_at')[:5]

        for supporter in recent_supporters:
            recent_activity.append({"type": "registration", "title": f"New supporter registered: {supporter.username}", "timestamp": supporter.date_joined})
        for eligibility in recent_verified:
            if eligibility.is_eligible:
                recent_activity.append({"type": "verification", "title": f"Supporter verified: {eligibility.supporter.username}", "timestamp": eligibility.pk})
        for journey in recent_collections:
            recent_activity.append({"type": "collection", "title": f"Ticket collected for {journey.supporter.username}", "timestamp": journey.updated_at})
        for journey in recent_attendance:
            recent_activity.append({"type": "attendance", "title": f"Attendance recorded for {journey.supporter.username}", "timestamp": journey.attended_at})

        def sort_key(item):
            timestamp = item.get("timestamp")
            if isinstance(timestamp, datetime):
                return timestamp.timestamp()
            if isinstance(timestamp, (int, float)):
                return float(timestamp)
            if timestamp is None:
                return 0.0
            return 0.0

        recent_activity.sort(key=sort_key, reverse=True)
        recent_activity = recent_activity[:10]

        return {
            "branch": branch,
            "supporters": supporters_count,
            "verified": verified_count,
            "eligible": eligible_count,
            "journeys_open": journeys_open,
            "journeys_booked": journeys_booked,
            "tickets_allocated": tickets_allocated,
            "tickets_collected": tickets_collected,
            "attendance_recorded": attendance_recorded,
            "attendance_rate": attendance_rate,
            "collection_rate": collection_rate,
            "no_show_rate": no_show_rate,
            "recent_activity": recent_activity,
        }
