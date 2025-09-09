from django.urls import reverse
from rest_framework.test import APITestCase

from ..models import Competition, Season


class CompetitionViewSetTests(APITestCase):
    def setUp(self):
        self.c1 = Competition.objects.create(name="EPL", country="England")
        self.c2 = Competition.objects.create(name="La Liga", country="Spain")

    def test_list_competitions(self):
        url = reverse("competitions-list")
        resp = self.client.get(url)
        self.assertEqual(resp.status_code, 200)

        # paginated response: {count, next, previous, results}
        results = resp.data["results"]
        self.assertEqual(len(results), 2)
        names = {c["name"] for c in results}
        self.assertSetEqual(names, {"EPL", "La Liga"})


class SeasonViewSetTests(APITestCase):
    def setUp(self):
        self.comp1 = Competition.objects.create(name="EPL", country="England")
        self.comp2 = Competition.objects.create(name="La Liga", country="Spain")
        self.s1 = Season.objects.create(competition=self.comp1, name="2024/25", year_start=2024, year_end=2025)
        self.s2 = Season.objects.create(competition=self.comp1, name="2023/24", year_start=2023, year_end=2024)
        self.s3 = Season.objects.create(competition=self.comp2, name="2024/25", year_start=2024, year_end=2025)

    def test_list_seasons_all(self):
        url = reverse("seasons-list")
        resp = self.client.get(url)
        self.assertEqual(resp.status_code, 200)

        results = resp.data["results"]
        self.assertEqual(len(results), 3)

    def test_list_seasons_filtered_by_competition(self):
        url = reverse("seasons-list")
        resp = self.client.get(url, {"competition": str(self.comp1.id)})
        self.assertEqual(resp.status_code, 200)

        results = resp.data["results"]
        names = [s["name"] for s in results]
        self.assertCountEqual(names, ["2024/25", "2023/24"])
