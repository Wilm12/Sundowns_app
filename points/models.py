from django.db import models
from membership.models import Membership


class Reward(models.Model):
    membership = models.ForeignKey(Membership, on_delete=models.CASCADE)
    points_earned = models.IntegerField()
    reward_date = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Reward {self.id} - {self.membership.user.username} - {self.points_earned} points"

