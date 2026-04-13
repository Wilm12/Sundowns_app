from django.db import models
from membership.models import Membership


class Event(models.Model):
    name = models.CharField(max_length=200)
    date = models.DateTimeField()
    location = models.CharField(max_length=200)

    def __str__(self):
        return self.name


class Ticket(models.Model):
    membership = models.ForeignKey(Membership, on_delete=models.CASCADE)
    event = models.ForeignKey(Event, on_delete=models.CASCADE)
    seat_number = models.CharField(max_length=10)
    ticket_date = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Ticket {self.id} - {self.membership.user.username} - {self.event.name}"

