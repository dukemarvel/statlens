from django.db import IntegrityError, transaction
from django.test import TestCase
from django.utils import timezone

from ..models import Match, MatchStatus
from competitions.models import Competition, Season
from teams.models import Team


class MatchModelTests(TestCase):
    def setUp(self):
        self.comp = Competition.objects.create(name="EPL", country="England")
        self.season = Season.objects.create(competition=self.comp, name="2024/25", year_start=2024, year_end=2025)
        self.home = Team.objects.create(name="Arsenal", country="England")
        self.away = Team.objects.create(name="Chelsea", country="England")
        self.kick = timezone.now().replace(microsecond=0)

    def test_str_format(self):
        m = Match.objects.create(
            competition=self.comp, season=self.season, utc_kickoff=self.kick,
            home=self.home, away=self.away, status=MatchStatus.SCHEDULED
        )
        self.assertIn("Arsenal", str(m))
        self.assertIn("Chelsea", str(m))
        self.assertIn(self.kick.strftime("%Y-%m-%d"), str(m))

    def test_unique_together_season_home_away_kickoff(self):
        Match.objects.create(
            competition=self.comp, season=self.season, utc_kickoff=self.kick,
            home=self.home, away=self.away, status=MatchStatus.SCHEDULED
        )
        with self.assertRaises(IntegrityError):
            with transaction.atomic():
                Match.objects.create(
                    competition=self.comp, season=self.season, utc_kickoff=self.kick,
                    home=self.home, away=self.away, status=MatchStatus.SCHEDULED
                )

    def test_status_choices(self):
        m = Match.objects.create(
            competition=self.comp, season=self.season, utc_kickoff=self.kick,
            home=self.home, away=self.away, status=MatchStatus.LIVE, minute=10
        )
        self.assertEqual(m.status, MatchStatus.LIVE)
        self.assertEqual(m.minute, 10)
