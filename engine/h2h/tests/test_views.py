from django.urls import reverse
from rest_framework.test import APITestCase

from ..models import H2HCache
from teams.models import Team


class H2HViewTests(APITestCase):
    def setUp(self):
        self.home = Team.objects.create(name="Arsenal", country="England")
        self.away = Team.objects.create(name="Chelsea", country="England")
        self.url = reverse("h2h")  # configured in project urls.py

    def test_400_when_params_missing(self):
        # missing away
        resp = self.client.get(self.url, {"home": str(self.home.id)})
        self.assertEqual(resp.status_code, 400)
        self.assertIn("home and away are required", resp.data.get("detail", ""))

        # missing home
        resp = self.client.get(self.url, {"away": str(self.away.id)})
        self.assertEqual(resp.status_code, 400)

    def test_404_when_cache_absent(self):
        resp = self.client.get(self.url, {
            "home": str(self.home.id),
            "away": str(self.away.id),
            "metric": "corners",
            "window": "5y",
        })
        self.assertEqual(resp.status_code, 404)
        self.assertIn("not yet materialized", resp.data.get("detail", ""))

    def test_200_when_cache_present(self):
        row = H2HCache.objects.create(
            home=self.home,
            away=self.away,
            metric_key="corners",
            window="5y",
            payload={"meetings": 10, "home_total": 42, "away_total": 36},
        )
        resp = self.client.get(self.url, {
            "home": str(self.home.id),
            "away": str(self.away.id),
            "metric": "corners",
            "window": "5y",
        })
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.data["home"], str(self.home.id))
        self.assertEqual(resp.data["away"], str(self.away.id))
        self.assertEqual(resp.data["metric"], "corners")
        self.assertEqual(resp.data["window"], "5y")
        self.assertEqual(resp.data["payload"], row.payload)
