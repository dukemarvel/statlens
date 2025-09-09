from uuid import uuid4
from django.urls import reverse
from django.utils import timezone
from rest_framework.test import APITestCase

from ..models import Match, MatchStatus
from competitions.models import Competition, Season
from teams.models import Team
from metrics.models import MetricType, MatchMetric



class MatchViewSetTests(APITestCase):
    def setUp(self):
        # Core refs
        self.comp = Competition.objects.create(name="EPL", country="England")
        self.season = Season.objects.create(
            competition=self.comp, name="2024/25", year_start=2024, year_end=2025
        )
        self.home = Team.objects.create(name="Arsenal", country="England")
        self.away = Team.objects.create(name="Chelsea", country="England")
        self.away2 = Team.objects.create(name="Spurs", country="England")

        # Times
        self.kickoff_day1 = timezone.now().replace(hour=15, minute=0, second=0, microsecond=0)
        self.kickoff_day2 = self.kickoff_day1 + timezone.timedelta(days=1)

        # Matches
        self.m1 = Match.objects.create(
            competition=self.comp, season=self.season,
            utc_kickoff=self.kickoff_day1,
            home=self.home, away=self.away,
            status=MatchStatus.FT,
        )
        self.m2 = Match.objects.create(
            competition=self.comp, season=self.season,
            utc_kickoff=self.kickoff_day1,
            home=self.home, away=self.away2,
            status=MatchStatus.LIVE, minute=72,
        )
        self.m3 = Match.objects.create(
            competition=self.comp, season=self.season,
            utc_kickoff=self.kickoff_day2,
            home=self.away2, away=self.home,
            status=MatchStatus.SCHEDULED,
        )

        # Metric types (safe if seeded)
        self.mt_corners, _ = MetricType.objects.get_or_create(
            key="corners",
            defaults=dict(unit="count", display_name="Corners", decimals=0),
        )
        self.mt_cards, _ = MetricType.objects.get_or_create(
            key="cards_total",
            defaults=dict(unit="count", display_name="Cards", decimals=0),
        )

        # FT metrics for m1 only
        MatchMetric.objects.get_or_create(
            match=self.m1, team=self.home, metric_type=self.mt_corners, period="FT",
            defaults=dict(value=6, source="test"),
        )
        MatchMetric.objects.get_or_create(
            match=self.m1, team=self.away, metric_type=self.mt_corners, period="FT",
            defaults=dict(value=4, source="test"),
        )
        MatchMetric.objects.get_or_create(
            match=self.m1, team=self.home, metric_type=self.mt_cards, period="FT",
            defaults=dict(value=2, source="test"),
        )
        MatchMetric.objects.get_or_create(
            match=self.m1, team=self.away, metric_type=self.mt_cards, period="FT",
            defaults=dict(value=3, source="test"),
        )
