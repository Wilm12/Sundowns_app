from rest_framework import viewsets
from rest_framework.permissions import IsAuthenticated
from django.contrib.auth.decorators import login_required
from django.shortcuts import render


from authentication.permissions import IsAdminOrReadOnly
from .models import Match
from .serializers import MatchSerializer

@login_required
def match_list_page(request):
     matches = Match.objects.all().order_by("date")
     return render(request, "matches/list.html", {"matches": matches})

class MatchViewSet(viewsets.ModelViewSet):
    queryset = Match.objects.all().order_by('-date')
    serializer_class = MatchSerializer
    permission_classes = [IsAuthenticated, IsAdminOrReadOnly]
