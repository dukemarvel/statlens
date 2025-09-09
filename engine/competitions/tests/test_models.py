from django.db import IntegrityError, transaction
from django.test import TestCase

from ..models import Competition, Season


class CompetitionModelTests(TestCase):
    def test_str_with_and_without_country(self):
        c1 = Competition.objects.create(name="Premier League", country="England")
        c2 = Competition.objects.create(name="UEFA Champions League", country="")
        self.assertEqual(str(c1), "Premier League (England)")
        self.assertEqual(str(c2), "UEFA Champions League")

    def test_unique_together_name_country(self):
        Competition.objects.create(name="La Liga", country="Spain")
        # Isolate the violating insert so the outer transaction remains usable
        with self.assertRaises(IntegrityError):
            with transaction.atomic():
                Competition.objects.create(name="La Liga", country="Spain")  # duplicate

        # Different country is allowed (and the connection is still clean)
        Competition.objects.create(name="La Liga", country="USA")


class SeasonModelTests(TestCase):
    def test_str_and_basic_fields(self):
        comp = Competition.objects.create(name="Serie A", country="Italy")
        s = Season.objects.create(competition=comp, name="2024/25", year_start=2024, year_end=2025)
        self.assertEqual(str(s), "Serie A 2024/25")
        self.assertEqual(s.year_start, 2024)
        self.assertEqual(s.year_end, 2025)

    def test_unique_together_competition_name(self):
        comp = Competition.objects.create(name="Bundesliga", country="Germany")
        Season.objects.create(competition=comp, name="2024/25", year_start=2024, year_end=2025)

        with self.assertRaises(IntegrityError):
            with transaction.atomic():
                Season.objects.create(competition=comp, name="2024/25", year_start=2024, year_end=2025)

        # same season name under a different competition is allowed
        comp2 = Competition.objects.create(name="2. Bundesliga", country="Germany")
        Season.objects.create(competition=comp2, name="2024/25", year_start=2024, year_end=2025)