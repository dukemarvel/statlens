from django.db import IntegrityError, transaction
from django.test import TestCase
from django.utils import timezone
from django.db.models.deletion import ProtectedError

from ..models import MetricType, MatchMetric, Period
from matches.models import Match, MatchStatus
from competitions.models import Competition, Season
from teams.models import Team


class MetricTypeModelTests(TestCase):
    def test_str_uses_display_name_else_key(self):
        # corners may already exist (seeded) → get_or_create
        m1, _ = MetricType.objects.get_or_create(
            key="corners",
            defaults={"unit": "count", "display_name": "Corners", "decimals": 0},
        )
        # Ensure display_name is set for this assertion
        if not m1.display_name:
            m1.display_name = "Corners"
            m1.save(update_fields=["display_name"])

        # shots_on_target may exist; ensure we test the fallback behavior
        m2, _ = MetricType.objects.get_or_create(
            key="shots_on_target",
            defaults={"unit": "count", "display_name": "", "decimals": 0},
        )
        # Force empty display_name so __str__ falls back to key (isolated per test txn)
        m2.display_name = ""
        m2.save(update_fields=["display_name"])

        self.assertEqual(str(m1), "Corners")
        self.assertEqual(str(m2), "shots_on_target")
        
    def test_unique_key(self):
        MetricType.objects.get_or_create(key="cards_total", defaults={"unit": "count", "display_name": "Cards"})
        with self.assertRaises(IntegrityError):
            with transaction.atomic():
                MetricType.objects.create(key="cards_total", unit="count")


class MatchMetricModelTests(TestCase):
    def setUp(self):
        # minimal related entities
        self.comp = Competition.objects.create(name="EPL", country="England")
        self.season = Season.objects.create(competition=self.comp, name="2024/25", year_start=2024, year_end=2025)
        self.home = Team.objects.create(name="Arsenal", country="England")
        self.away = Team.objects.create(name="Chelsea", country="England")
        self.kick = timezone.now().replace(microsecond=0)

        self.match = Match.objects.create(
            competition=self.comp, season=self.season, utc_kickoff=self.kick,
            home=self.home, away=self.away, status=MatchStatus.FT
        )

        self.mt_corners, _ = MetricType.objects.get_or_create(
            key="corners", defaults={"unit": "count", "display_name": "Corners", "decimals": 0}
        )

    def test_str_format(self):
        mm = MatchMetric.objects.create(
            match=self.match, team=self.home, metric_type=self.mt_corners,
            period=Period.FT, value=7, source="test"
        )
        s = str(mm)
        self.assertIn("corners", s)
        self.assertIn(self.home.name, s)
        self.assertIn("FT", s)
        self.assertIn("7", s)

    def test_unique_together_match_team_type_period(self):
        MatchMetric.objects.create(
            match=self.match, team=self.home, metric_type=self.mt_corners,
            period=Period.FT, value=5
        )
        with self.assertRaises(IntegrityError):
            with transaction.atomic():
                MatchMetric.objects.create(
                    match=self.match, team=self.home, metric_type=self.mt_corners,
                    period=Period.FT, value=6
                )

        # different team → allowed
        MatchMetric.objects.create(
            match=self.match, team=self.away, metric_type=self.mt_corners,
            period=Period.FT, value=3
        )
        # different period → allowed
        MatchMetric.objects.create(
            match=self.match, team=self.home, metric_type=self.mt_corners,
            period=Period.HT, value=2
        )

    def test_metric_type_is_protected_on_delete(self):
        # create a value referencing the metric type
        MatchMetric.objects.create(
            match=self.match, team=self.home, metric_type=self.mt_corners, period=Period.FT, value=4
        )
        with self.assertRaises(ProtectedError):
            with transaction.atomic():
                self.mt_corners.delete()
