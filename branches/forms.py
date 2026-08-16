from django import forms

from users.models import User

from .models import Branch, BranchRole, CommitteePosition, MatchAllocation
from matches.models import Match


class MatchAllocationForm(forms.Form):
    """Dynamic admin form for branch allocations tied to a match."""

    def __init__(self, *args, branch=None, match=None, **kwargs):
        super().__init__(*args, **kwargs)
        if branch is not None:
            eligible_branches = Branch.objects.filter(pk=branch.pk).order_by("name")
        else:
            eligible_branches = Branch.objects.order_by("name")

        for branch_obj in eligible_branches:
            field_name = f"allocation_{branch_obj.pk}"
            initial_value = 0
            if match is not None:
                existing_allocation = MatchAllocation.objects.filter(branch=branch_obj, match=match).first()
                if existing_allocation is not None:
                    initial_value = existing_allocation.allocated_tickets
            self.fields[field_name] = forms.IntegerField(
                required=False,
                min_value=0,
                initial=initial_value,
                label=branch_obj.name,
                widget=forms.NumberInput(attrs={"min": 0, "class": "w-full rounded-2xl border border-slate-200 bg-white px-3 py-2.5 text-slate-700", "placeholder": "0"}),
            )

    def get_allocation_values(self):
        values = {}
        for key, value in self.cleaned_data.items():
            if not key.startswith("allocation_"):
                continue
            if value is None:
                values[int(key.split("_", 1)[1])] = 0
            else:
                values[int(key.split("_", 1)[1])] = value
        return values


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
