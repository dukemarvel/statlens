from django.db import IntegrityError, transaction
from django.test import TestCase

from ..models import Team, TeamAlias
from competitions.models import Competition


class TeamModelTests(TestCase):
    def setUp(self):
        self.comp = Competition.objects.create(name="EPL", country="England")

    def test_str_and_optional_default_competition(self):
        t = Team.objects.create(name="Arsenal", country="England", default_competition=self.comp)
        self.assertEqual(str(t), "Arsenal")
        self.assertEqual(t.default_competition, self.comp)

        # also valid without default_competition
        t2 = Team.objects.create(name="Chelsea", country="England")
        self.assertIsNone(t2.default_competition)

    def test_unique_together_name_country(self):
        Team.objects.create(name="Barcelona", country="Spain")
        with self.assertRaises(IntegrityError):
            with transaction.atomic():
                Team.objects.create(name="Barcelona", country="Spain")
        # same name different country allowed
        Team.objects.create(name="Barcelona", country="Ecuador")


class TeamAliasModelTests(TestCase):
    def setUp(self):
        self.team = Team.objects.create(name="Manchester United", country="England")

    def test_str(self):
        alias = TeamAlias.objects.create(team=self.team, alias="Man Utd")
        self.assertEqual(str(alias), "Man Utd → Manchester United")

    def test_unique_together_team_alias(self):
        TeamAlias.objects.create(team=self.team, alias="Man Utd")
        with self.assertRaises(IntegrityError):
            with transaction.atomic():
                TeamAlias.objects.create(team=self.team, alias="Man Utd")

        # same alias for a different team is allowed
        other = Team.objects.create(name="Newcastle United", country="England")
        TeamAlias.objects.create(team=other, alias="Man Utd")
