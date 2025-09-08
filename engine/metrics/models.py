from django.db import models
from core.models import TimeStampedModel
from matches.models import Match
from teams.models import Team

class Period(models.TextChoices):
    FT = "FT", "Full Time"
    HT = "HT", "Half Time"
    H1 = "1H", "First Half"
    H2 = "2H", "Second Half"
    ET = "ET", "Extra Time"

class MetricType(TimeStampedModel):
    """
    Registry of allowed metrics for normalization.
    Examples:
      key="corners", unit="count"
      key="shots_on_target", unit="count"
      key="cards_total", unit="count"
      key="xg", unit="expected_goals"
    """
    key = models.SlugField(max_length=64, unique=True)
    unit = models.CharField(max_length=64, default="count")
    description = models.TextField(blank=True)
    # optional display metadata for frontend
    display_name = models.CharField(max_length=64, blank=True)
    decimals = models.PositiveSmallIntegerField(default=0)

    class Meta:
        indexes = [models.Index(fields=["key"])]

    def __str__(self) -> str:
        return self.display_name or self.key


class MatchMetric(TimeStampedModel):
    """
    A single team’s value for a given metric within a match and period.
    """
    match = models.ForeignKey(Match, on_delete=models.CASCADE, related_name="metrics")
    team = models.ForeignKey(Team, on_delete=models.CASCADE, related_name="metrics")
    metric_type = models.ForeignKey(MetricType, on_delete=models.PROTECT, related_name="values")

    period = models.CharField(max_length=2, choices=Period.choices, default=Period.FT, db_index=True)
    value = models.FloatField()

    source = models.CharField(max_length=32, blank=True)  # e.g., "api_football"
    confidence = models.FloatField(default=1.0)           # 0–1 if you ever reconcile sources

    class Meta:
        unique_together = (("match", "team", "metric_type", "period"),)
        indexes = [
            models.Index(fields=["match", "period"]),
            models.Index(fields=["metric_type", "period"]),
            models.Index(fields=["team", "metric_type"]),
        ]

    def __str__(self) -> str:
        return f"{self.metric_type.key} {self.team} {self.period}: {self.value}"
