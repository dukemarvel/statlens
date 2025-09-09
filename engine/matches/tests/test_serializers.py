from django.test import TestCase, RequestFactory
from django.utils import timezone

from ..serializers import MatchSerializer
from ..models import Match, MatchStatus
from competitions.models import Competition, Season
from teams.models import Team
from metrics.models import MetricType, MatchMetric


class MatchSerializerTests(TestCase):
    def setUp(self):
        self.factory = RequestFactory()
        comp = Competition.objects.create(name="Comp", country="X")
        season = Season.objects.create(competition=comp, name="2024/25", year_start=2024, year_end=2025)
        home = Team.objects.create(name="H", country="X")
        away = Team.objects.create(name="A", country="X")
        self.match = Match.objects.create(
            competition=comp, season=season, utc_kickoff=timezone.now(),
            home=home, away=away, status=MatchStatus.FT
        )
        mt, _ = MetricType.objects.get_or_create(
            key="corners",
            defaults=dict(unit="count", display_name="Corners", decimals=0),
        )
        MatchMetric.objects.get_or_create(
            match=self.match, team=home, metric_type=mt, period="FT",
            defaults=dict(value=5, source="test"),
        )
