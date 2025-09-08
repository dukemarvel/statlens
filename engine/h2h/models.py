from django.db import models
from core.models import TimeStampedModel
from teams.models import Team

class H2HCache(TimeStampedModel):
    """
    Materialized cache for expensive H2H + metric queries.
    """
    home = models.ForeignKey(Team, on_delete=models.CASCADE, related_name="h2h_home")
    away = models.ForeignKey(Team, on_delete=models.CASCADE, related_name="h2h_away")
    metric_key = models.SlugField(max_length=64)
    window = models.CharField(max_length=32, default="5y")  # e.g., "5y", "20_matches"
    payload = models.JSONField()  # aggregated stats blob
    updated_at_source = models.DateTimeField(null=True, blank=True)

    class Meta:
        unique_together = (("home", "away", "metric_key", "window"),)
        indexes = [
            models.Index(fields=["metric_key", "window"]),
            models.Index(fields=["home", "away"]),
        ]

    def __str__(self) -> str:
        return f"H2H {self.home} vs {self.away} [{self.metric_key}/{self.window}]"
