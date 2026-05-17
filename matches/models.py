"""Match models representing scheduled games and opponents."""

from django.db import models

class Match(models.Model):
    """Represents a scheduled match with location and opponent information."""
    date = models.DateTimeField()
    location = models.CharField(max_length=255)
    opponent = models.CharField(max_length=255)

    def __str__(self):
        return f"{self.opponent} - {self.date}"