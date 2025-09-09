from django.db import IntegrityError, transaction
from django.test import TestCase

from ..models import H2HCache
from teams.models import Team


class H2HCacheModelTests(TestCase):
    def setUp(self):
        self.home = Team.objects.create(name="Arsenal", country="England")
        self.away = Team.objects.create(name="Chelsea", country="England")

    def test_str_format(self):
        row = H2HCache.objects.create(
            home=self.home,
            away=self.away,
            metric_key="corners",
            window="5y",
            payload={"sample": True},
        )
        s = str(row)
        self.assertIn("H2H Arsenal vs Chelsea", s)
        self.assertIn("corners/5y", s)

    def test_unique_together_home_away_metric_window(self):
        H2HCache.objects.create(
            home=self.home,
            away=self.away,
            metric_key="corners",
            window="5y",
            payload={"x": 1},
        )
        with self.assertRaises(IntegrityError):
            with transaction.atomic():
                H2HCache.objects.create(
                    home=self.home,
                    away=self.away,
                    metric_key="corners",
                    window="5y",
                    payload={"x": 2},
                )

        # different window is allowed
        H2HCache.objects.create(
            home=self.home,
            away=self.away,
            metric_key="corners",
            window="20_matches",
            payload={"x": 3},
        )
