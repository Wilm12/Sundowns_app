from rest_framework import viewsets
from rest_framework.permissions import IsAuthenticated
from django.contrib.auth.decorators import login_required
from django.shortcuts import render, get_object_or_404, redirect
from users.models import User
from transport.models import Transport
from .models import Branch
from authentication.permissions import IsAdminOrReadOnly
from .serializers import BranchSerializer
from django.contrib import messages

@login_required
def my_branch_page(request):
    if not request.user.branch:
        messages.error(request, "You are not assigned to a branch.")
        return redirect("dashboard")

    return redirect("branch_detail_page", branch_id=request.user.branch.id)


class BranchViewSet(viewsets.ModelViewSet):
    queryset = Branch.objects.all().order_by('name')
    serializer_class = BranchSerializer
    permission_classes = [IsAuthenticated, IsAdminOrReadOnly]

@login_required
def branch_list_page(request):
    branches = Branch.objects.all().order_by("name")

    return render(request, "branches/list.html", {
        "branches": branches,
    })


@login_required
def branch_detail_page(request, branch_id):
    branch = get_object_or_404(Branch, id=branch_id)

    members = User.objects.filter(
        branch=branch
    ).order_by("username")

    transport = Transport.objects.filter(
        branch=branch,
        status="active"
    )

    return render(request, "branches/detail.html", {
        "branch": branch,
        "members": members,
        "transport": transport,
    })

