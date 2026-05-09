from rest_framework import viewsets
from rest_framework.permissions import IsAuthenticated
from django.contrib.auth.decorators import login_required
from django.shortcuts import render

from authentication.permissions import IsAdminOrReadOnly
from .models import Match
from .serializers import MatchSerializer

from django.shortcuts import render, get_object_or_404

from .models import Match
from transport.models import Transport


@login_required
def match_detail_page(request, match_id):
    match = get_object_or_404(Match, id=match_id)

    transports = Transport.objects.filter(
        match=match,
        status="active"
    ).select_related("branch")

    return render(request, "matches/detail.html", {
        "match": match,
        "transports": transports,
    })

@login_required
def match_list_page(request):
     matches = Match.objects.all().order_by("date")
     return render(request, "matches/list.html", {"matches": matches})

class MatchViewSet(viewsets.ModelViewSet):
    queryset = Match.objects.all().order_by('-date')
    serializer_class = MatchSerializer
    permission_classes = [IsAuthenticated, IsAdminOrReadOnly]
