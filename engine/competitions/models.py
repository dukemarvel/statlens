from django.db import models
from django.contrib.postgres.fields import ArrayField
from core.models import TimeStampedModel

class Competition(TimeStampedModel):
    name = models.CharField(max_length=128)
    country = models.CharField(max_length=64, blank=True)
    # provider code → id mapping, e.g. {"api_football": {"league_id": 39}}
    provider_refs = models.JSONField(default=dict, blank=True)

    class Meta:
        unique_together = (("name", "country"),)
        indexes = [
            models.Index(fields=["country", "name"]),
        ]

    def __str__(self) -> str:
        return f"{self.name} ({self.country})" if self.country else self.name


class Season(TimeStampedModel):
    competition = models.ForeignKey(Competition, on_delete=models.CASCADE, related_name="seasons")
    name = models.CharField(max_length=32)  # e.g. "2024/25"
    year_start = models.IntegerField()
    year_end = models.IntegerField()

    class Meta:
        unique_together = (("competition", "name"),)
        indexes = [models.Index(fields=["competition", "year_start", "year_end"])]

    def __str__(self) -> str:
        return f"{self.competition.name} {self.name}"