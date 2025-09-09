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

        # Matches (two days, mixed status)
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

        # Metric types
        self.mt_corners = MetricType.objects.create(key="corners", unit="count", display_name="Corners", decimals=0)
        self.mt_cards   = MetricType.objects.create(key="cards_total", unit="count", display_name="Cards", decimals=0)

        # Add FT metrics for m1 only (so lists differ per match)
        MatchMetric.objects.create(match=self.m1, team=self.home, metric_type=self.mt_corners, period="FT", value=6, source="test")
        MatchMetric.objects.create(match=self.m1, team=self.away, metric_type=self.mt_corners, period="FT", value=4, source="test")
        MatchMetric.objects.create(match=self.m1, team=self.home, metric_type=self.mt_cards,   period="FT", value=2, source="test")
        MatchMetric.objects.create(match=self.m1, team=self.away, metric_type=self.mt_cards,   period="FT", value=3, source="test")

    def test_list_all_paginated(self):
        url = reverse("matches-list")
        resp = self.client.get(url)
        self.assertEqual(resp.status_code, 200)
        self.assertIn("results", resp.data)
        self.assertEqual(len(resp.data["results"]), 3)

    def test_filter_by_date(self):
        url = reverse("matches-list")
        date_str = self.kickoff_day1.date().isoformat()
        resp = self.client.get(url, {"date": date_str})
        self.assertEqual(resp.status_code, 200)
        ids = {m["id"] for m in resp.data["results"]}
        self.assertSetEqual(ids, {str(self.m1.id), str(self.m2.id)})

    def test_filter_by_status(self):
        url = reverse("matches-list")
        resp = self.client.get(url, {"status": "LIVE,FT"})
        self.assertEqual(resp.status_code, 200)
        statuses = {m["status"] for m in resp.data["results"]}
        self.assertSetEqual(statuses, {"LIVE", "FT"})

    def test_filter_by_competition(self):
        url = reverse("matches-list")
        resp = self.client.get(url, {"competition": str(self.comp.id)})
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(len(resp.data["results"]), 3)  # all 3 belong to same comp

    def test_selected_metrics_embedding(self):
        url = reverse("matches-list")
        date_str = self.kickoff_day1.date().isoformat()
        resp = self.client.get(url, {"date": date_str, "metrics": "corners,cards_total", "period": "FT"})
        self.assertEqual(resp.status_code, 200)

        by_id = {m["id"]: m for m in resp.data["results"]}

        # m1 has metrics
        m1_metrics = by_id[str(self.m1.id)]["selected_metrics"]
        # Expect 4 rows (2 teams x 2 metric keys)
        self.assertEqual(len(m1_metrics), 4)
        keys = {row["metric_key"] for row in m1_metrics}
        self.assertSetEqual(keys, {"corners", "cards_total"})

        # m2 has no metrics for FT
        m2_metrics = by_id[str(self.m2.id)]["selected_metrics"]
        self.assertEqual(m2_metrics, [])

    def test_match_metrics_action(self):
        # /api/v1/matches/{id}/metrics?period=FT
        url = reverse("matches-detail", kwargs={"pk": str(self.m1.id)}) + "metrics/"
        # DRF @action with url_path="metrics" typically maps to /matches/<id>/metrics/
        # If your router output differs, adjust the path accordingly.
        resp = self.client.get(url, {"period": "FT"})
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(len(resp.data), 4)
        self.assertSetEqual({r["metric_key"] for r in resp.data}, {"corners", "cards_total"})
