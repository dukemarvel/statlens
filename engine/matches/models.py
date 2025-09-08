from django.db import models
from core.models import TimeStampedModel
from competitions.models import Competition, Season
from teams.models import Team

class MatchStatus(models.TextChoices):
    SCHEDULED = "SCHED", "Scheduled"
    LIVE = "LIVE", "Live"
    HT = "HT", "Half-Time"
    FT = "FT", "Full-Time"
    AET = "AET", "After Extra Time"
    PEN = "PEN", "Penalties"
    POSTPONED = "PPD", "Postponed"
    ABANDONED = "ABD", "Abandoned"
    CANCELLED = "CANC", "Cancelled"

class Match(TimeStampedModel):
    competition = models.ForeignKey(Competition, on_delete=models.PROTECT, related_name="matches")
    season = models.ForeignKey(Season, on_delete=models.PROTECT, related_name="matches")
    utc_kickoff = models.DateTimeField(db_index=True)

    home = models.ForeignKey(Team, on_delete=models.PROTECT, related_name="home_matches")
    away = models.ForeignKey(Team, on_delete=models.PROTECT, related_name="away_matches")

    venue = models.CharField(max_length=128, blank=True)
    status = models.CharField(max_length=5, choices=MatchStatus.choices, default=MatchStatus.SCHEDULED, db_index=True)
    minute = models.PositiveSmallIntegerField(default=0)  # live minute when applicable

    provider_refs = models.JSONField(default=dict, blank=True)  # {"api_football": {"fixture_id": 12345}}
    freshness_ts = models.DateTimeField(null=True, blank=True)  # last time any metric/status was refreshed

    class Meta:
        unique_together = (("season", "home", "away", "utc_kickoff"),)
        indexes = [
            models.Index(fields=["utc_kickoff"]),
            models.Index(fields=["competition", "utc_kickoff"]),
            models.Index(fields=["status", "utc_kickoff"]),
        ]

    def __str__(self) -> str:
        return f"{self.home} vs {self.away} ({self.utc_kickoff:%Y-%m-%d})"
