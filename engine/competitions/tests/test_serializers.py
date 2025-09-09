from django.test import TestCase

from ..models import Competition, Season
from ..serializers import CompetitionSerializer, SeasonSerializer


class CompetitionSerializerTests(TestCase):
    def test_serializes_expected_fields(self):
        c = Competition.objects.create(name="Eredivisie", country="Netherlands")
        data = CompetitionSerializer(c).data
        self.assertSetEqual(set(data.keys()), {"id", "name", "country"})
        self.assertEqual(data["name"], "Eredivisie")
        self.assertEqual(data["country"], "Netherlands")


class SeasonSerializerTests(TestCase):
    def test_serializes_nested_competition_read_only(self):
        comp = Competition.objects.create(name="Ligue 1", country="France")
        s = Season.objects.create(competition=comp, name="2024/25", year_start=2024, year_end=2025)

        data = SeasonSerializer(s).data
        # has nested competition block
        self.assertIn("competition", data)
        self.assertEqual(data["competition"]["name"], "Ligue 1")
        self.assertEqual(data["competition"]["country"], "France")
        self.assertEqual(data["name"], "2024/25")
        self.assertEqual(data["year_start"], 2024)
        self.assertEqual(data["year_end"], 2025)
