from django.db import models
from core.models import TimeStampedModel
from competitions.models import Competition

class Team(TimeStampedModel):
    name = models.CharField(max_length=128)
    short_name = models.CharField(max_length=32, blank=True)
    country = models.CharField(max_length=64, blank=True)
    provider_refs = models.JSONField(default=dict, blank=True)
    # optional default competition context (useful for lookups)
    default_competition = models.ForeignKey(
        Competition, null=True, blank=True, on_delete=models.SET_NULL, related_name="default_teams"
    )

    class Meta:
        unique_together = (("name", "country"),)
        indexes = [
            models.Index(fields=["name"]),
            models.Index(fields=["country", "name"]),
        ]

    def __str__(self) -> str:
        return self.name


class TeamAlias(TimeStampedModel):
    team = models.ForeignKey(Team, on_delete=models.CASCADE, related_name="aliases")
    alias = models.CharField(max_length=128)

    class Meta:
        unique_together = (("team", "alias"),)
        indexes = [models.Index(fields=["alias"])]

    def __str__(self) -> str:
        return f"{self.alias} → {self.team.name}"
