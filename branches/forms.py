from django import forms

from users.models import User

from .models import BranchRole, CommitteePosition
from matches.models import Match


class MatchForm(forms.ModelForm):
    class Meta:
        model = Match
        fields = ["opponent", "date", "location", "ticket_collection_timeframe", "gate_number", "published"]
        labels = {
            "opponent": "Opposition",
            "date": "Match Date",
            "location": "Venue",
            "ticket_collection_timeframe": "Ticket Collection Timeframe",
            "gate_number": "Gate Number",
            "published": "Publish Match",
        }
        widgets = {
            "date": forms.DateInput(attrs={"type": "date"}),
            "ticket_collection_timeframe": forms.TextInput(attrs={"placeholder": "18:00–19:00"}),
            "gate_number": forms.TextInput(attrs={"placeholder": "Gate 3"}),
        }


class PromoteBranchAdminForm(forms.Form):
    supporter = forms.ModelChoiceField(
        queryset=User.objects.none(),
        label="Supporter",
        required=True,
    )

    def __init__(self, *args, branch=None, **kwargs):
        super().__init__(*args, **kwargs)
        if branch is not None:
            self.fields["supporter"].queryset = (
                User.objects.filter(branch=branch)
                .exclude(branch_roles__branch=branch, branch_roles__role=BranchRole.Role.BRANCH_ADMIN, branch_roles__is_active=True)
                .order_by("username")
            )


class CommitteePositionManagementForm(forms.Form):
    member = forms.ModelChoiceField(
        queryset=User.objects.none(),
        label="Committee member",
        required=True,
    )
    position = forms.ChoiceField(
        choices=[("", "Select leadership position")],
        required=False,
        label="Leadership position",
    )
    action = forms.ChoiceField(
        choices=[
            ("assign", "Assign Leadership Position"),
            ("change", "Change Leadership Position"),
            ("remove", "Remove Leadership Position"),
        ],
        required=True,
        label="Action",
    )

    def __init__(self, *args, branch=None, **kwargs):
        super().__init__(*args, **kwargs)
        if branch is not None:
            self.fields["member"].queryset = (
                User.objects.filter(branch=branch)
                .filter(branch_roles__branch=branch, branch_roles__role=BranchRole.Role.BRANCH_ADMIN, branch_roles__is_active=True)
                .distinct()
                .order_by("username")
            )
            self.fields["position"].choices = [("", "Select leadership position")] + list(CommitteePosition.Position.choices)


class RemoveBranchAdminForm(forms.Form):
    user = forms.ModelChoiceField(
        queryset=User.objects.none(),
        label="Branch admin",
        required=True,
    )

    def __init__(self, *args, branch=None, **kwargs):
        super().__init__(*args, **kwargs)
        if branch is not None:
            self.fields["user"].queryset = (
                User.objects.filter(branch=branch)
                .filter(branch_roles__branch=branch, branch_roles__role=BranchRole.Role.BRANCH_ADMIN, branch_roles__is_active=True)
                .distinct()
                .order_by("username")
            )
