from django.conf import settings
from django.db import models
from core.models import TimeStampedModel

class UserProfile(TimeStampedModel):
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="profile")
    # user preferences (e.g., default metrics)
    default_metric_keys = models.JSONField(default=list, blank=True)  # e.g., ["corners","cards_total"]
    timezone = models.CharField(max_length=64, default="UTC")

    def __str__(self) -> str:
        return f"Profile({self.user})"


class UserView(TimeStampedModel):
    """
    Saved custom dashboards: metric presets + filters.
    """
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="views")
    name = models.CharField(max_length=64)
    metric_keys = models.JSONField(default=list, blank=True)     # ["corners","shots_on_target"]
    filters = models.JSONField(default=dict, blank=True)         # {"competition_ids":[...], "status":"LIVE"}

    class Meta:
        unique_together = (("user", "name"),)

    def __str__(self) -> str:
        return f"{self.user}: {self.name}"
