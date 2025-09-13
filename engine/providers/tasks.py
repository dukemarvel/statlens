import logging
from celery import shared_task
from django.db import transaction
from django.utils.dateparse import parse_datetime
from .api_football import APIFootballAdapter, RateLimitError, ProviderError
from .mapper import normalize_fixture_api_football, normalize_stats_api_football
from matches.models import Match, MatchStatus
from metrics.models import MatchMetric, MetricType
from teams.models import Team
from competitions.models import Competition, Season

logger = logging.getLogger(__name__)

@shared_task(bind=True, max_retries=5, default_retry_delay=10)
def sync_fixtures_for_league(self, competition_provider_id, date_from=None, date_to=None):
    adapter = APIFootballAdapter()
    try:
        fixtures = adapter.fetch_fixtures(competition_provider_id, date_from=date_from, date_to=date_to)
    except RateLimitError as e:
        logger.warning("Rate limited; retrying: %s", e)
        raise self.retry(exc=e, countdown=30)
    except ProviderError as e:
        logger.error("Provider error: %s", e)
        return

    for fx in fixtures:
        norm = normalize_fixture_api_football(fx)
        with transaction.atomic():
            # find or create competition/season by provider refs
            comp, _ = Competition.objects.get_or_create(
                provider_refs__contains={adapter.name: {"league_id": norm["competition_provider_id"]}},
                defaults={"name": str(norm.get("competition_provider_id"))}
            )
            season, _ = Season.objects.get_or_create(competition=comp, name=str(norm.get("season_name") or ""), defaults={"year_start": 0, "year_end": 0})
            # map teams by provider id (create placeholders if unknown)
            home_team, _ = Team.objects.get_or_create(provider_refs__contains={adapter.name: {"team_id": norm["home_provider_id"]}}, defaults={"name": f"team-{norm['home_provider_id']}"})
            away_team, _ = Team.objects.get_or_create(provider_refs__contains={adapter.name: {"team_id": norm["away_provider_id"]}}, defaults={"name": f"team-{norm['away_provider_id']}"})

            kick = norm["utc_kickoff"]
            if isinstance(kick, str):
                kick = parse_datetime(kick)

            match, _ = Match.objects.update_or_create(
                provider_refs__contains={adapter.name: {"fixture_id": norm["provider_id"]}},
                defaults={
                    "competition": comp,
                    "season": season,
                    "utc_kickoff": kick,
                    "home": home_team,
                    "away": away_team,
                    "venue": norm.get("venue") or "",
                    "status": MatchStatus.SCHEDULED,
                }
            )
            # stamp provider id in provider_refs (ensure provider_refs dict)
            refs = match.provider_refs or {}
            refs.setdefault(adapter.name, {})["fixture_id"] = norm["provider_id"]
            match.provider_refs = refs
            match.save(update_fields=["provider_refs"])

@shared_task(bind=True, max_retries=3, default_retry_delay=5)
def hydrate_match_stats(self, match_id):
    """
    Given our Match.id, look up provider fixture id and call provider stats,
    then write MatchMetric rows.
    """
    adapter = APIFootballAdapter()
    try:
        match = Match.objects.get(id=match_id)
    except Match.DoesNotExist:
        return

    provider_refs = match.provider_refs or {}
    provider_info = provider_refs.get(adapter.name) or {}
    fixture_id = provider_info.get("fixture_id")
    if not fixture_id:
        logger.warning("No fixture id for match %s in provider %s", match_id, adapter.name)
        return

    try:
        raw_stats = adapter.fetch_match_stats(fixture_id)
    except RateLimitError as e:
        raise self.retry(exc=e, countdown=30)
    except ProviderError as e:
        logger.error("Provider error fetching stats for %s: %s", match_id, e)
        return

    rows = normalize_stats_api_football(raw_stats)

    # Bulk upsert metrics
    with transaction.atomic():
        for r in rows:
            # Map team_provider_id -> Team object
            team_q = Team.objects.filter(provider_refs__contains={adapter.name: {"team_id": r["team_provider_id"]}})
            team = team_q.first()
            if not team:
                # Create placeholder
                team = Team.objects.create(name=f"team-{r['team_provider_id']}", provider_refs={adapter.name: {"team_id": r["team_provider_id"]}})

            # Get metric_type by key (create if unknown)
            mtype, _ = MetricType.objects.get_or_create(key=r["metric_key"], defaults={"display_name": r["metric_key"], "unit": "count"})
            MatchMetric.objects.update_or_create(
                match=match,
                team=team,
                metric_type=mtype,
                period=r.get("period", "FT"),
                defaults={"value": r["value"], "source": adapter.name, "confidence": 1.0}
            )

    # finally, mark freshness_ts on match
    match.freshness_ts = match.updated_at
    match.save(update_fields=["freshness_ts"])
