from django.db.models import Q

from branches.models import Branch
from matches.models import Match

from ..models import Journey, JourneyStatus


class MatchOperationsService:
    @staticmethod
    def get_console(branch, match, search_query=None):
        branch = Branch.objects.get(pk=branch.pk if hasattr(branch, "pk") else branch)
        match = Match.objects.get(pk=match.pk if hasattr(match, "pk") else match)

        journeys = (
            Journey.objects.filter(branch=branch, match=match)
            .select_related("supporter", "ticket", "branch", "match")
            .prefetch_related("supporter__student_verifications")
            .order_by("supporter__username")
        )

        if search_query:
            search_query = search_query.strip()
            journeys = journeys.filter(
                Q(supporter__username__icontains=search_query)
                | Q(supporter__first_name__icontains=search_query)
                | Q(supporter__last_name__icontains=search_query)
                | Q(supporter__email__icontains=search_query)
                | Q(supporter__student_verifications__student_number__icontains=search_query)
            )

        booked_count = journeys.filter(status=JourneyStatus.BOOKED).count()
        allocated_count = journeys.filter(status=JourneyStatus.TICKET_READY).count()
        collected_count = journeys.filter(status=JourneyStatus.TICKET_COLLECTED).count()
        attended_count = journeys.filter(status=JourneyStatus.MATCH_ATTENDED).count()
        pending_collections = journeys.filter(status=JourneyStatus.TICKET_READY).count()
        no_shows = booked_count

        return {
            "branch": branch,
            "match": match,
            "journeys": journeys,
            "booked_count": booked_count,
            "allocated_count": allocated_count,
            "collected_count": collected_count,
            "attended_count": attended_count,
            "pending_collections": pending_collections,
            "no_shows": no_shows,
            "booking_completion": round((attended_count / booked_count) * 100, 1) if booked_count else 0,
            "allocation_completion": round((allocated_count / max(booked_count, 1)) * 100, 1),
            "collection_completion": round((collected_count / max(allocated_count, 1)) * 100, 1),
            "attendance_completion": round((attended_count / max(collected_count, 1)) * 100, 1),
            "search_query": search_query or "",
        }
