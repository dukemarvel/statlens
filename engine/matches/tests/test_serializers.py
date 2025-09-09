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
        mt = MetricType.objects.create(key="corners", unit="count", display_name="Corners", decimals=0)
        MatchMetric.objects.create(match=self.match, team=home, metric_type=mt, period="FT", value=5)

    def test_embeds_selected_metrics_when_requested(self):
        request = self.factory.get("/api/v1/matches?metrics=corners&period=FT")
        ser = MatchSerializer(self.match, context={"request": request})
        data = ser.data
        self.assertIn("selected_metrics", data)
        self.assertEqual(len(data["selected_metrics"]), 1)
        self.assertEqual(data["selected_metrics"][0]["metric_key"], "corners")
