from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, redirect, render

from .models import Reward, RewardRedemption
from .services import redeem_reward
from points import tiers as tier_helpers


@login_required
def reward_list_page(request):
    """Display a list of active rewards ordered by points cost."""
    rewards = list(Reward.objects.filter(is_active=True).order_by('points_cost'))

    user_tier = tier_helpers.get_user_tier(request.user)
    user_rank = tier_helpers.get_tier_rank(user_tier)

    # annotate eligibility
    for r in rewards:
        required = getattr(r, 'minimum_tier', 'bronze')
        r.is_eligible_for_user = user_rank >= tier_helpers.get_tier_rank(required)

    return render(request, 'rewards/reward_list.html', {'rewards': rewards, 'user_tier': user_tier})


@login_required
def reward_detail_page(request, reward_id):
    reward = get_object_or_404(Reward, pk=reward_id)
    user_tier = tier_helpers.get_user_tier(request.user)
    user_rank = tier_helpers.get_tier_rank(user_tier)
    required = getattr(reward, 'minimum_tier', 'bronze')
    is_eligible = user_rank >= tier_helpers.get_tier_rank(required)
    return render(request, 'rewards/reward_detail.html', {'reward': reward, 'user_tier': user_tier, 'is_eligible': is_eligible})


@login_required
def redeem_reward_view(request, reward_id):
    reward = get_object_or_404(Reward, pk=reward_id)
    if request.method != 'POST':
        return redirect('reward_detail_page', reward_id=reward.pk)

    try:
        redeem_reward(request.user, reward)
    except ValueError as exc:
        error_text = str(exc).lower()
        if 'insufficient' in error_text:
            messages.error(request, 'You do not have enough points to redeem this reward.')
        elif 'inactive' in error_text or 'not active' in error_text:
            messages.error(request, 'This reward is not currently active.')
        elif 'out of stock' in error_text:
            messages.error(request, 'This reward is out of stock.')
        else:
            messages.error(request, 'Could not redeem reward.')
        return redirect('reward_detail_page', reward_id=reward.pk)

    messages.success(request, 'Reward redeemed successfully!')
    return redirect('my_redemptions_page')


@login_required
def my_redemptions_page(request):
    redemptions = (
        RewardRedemption.objects.filter(user=request.user)
        .select_related('reward')
        .order_by('-created_at')
    )
    return render(request, 'rewards/my_redemptions.html', {'redemptions': redemptions})
