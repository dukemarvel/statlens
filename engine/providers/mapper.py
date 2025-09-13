from typing import Dict, Any, List, Tuple
from datetime import datetime

def normalize_fixture_api_football(fixture_payload: Dict[str, Any]) -> Dict[str, Any]:
    """
    Map API-Football fixture JSON to our Match data shape.
    Keep these fields minimal: match_provider_id, utc_kickoff, competition_provider_id, season_name, home_provider_id, away_provider_id, venue, status
    """
    # The exact path depends on provider payload. Adjust these keys for the real API response.
    fixture = fixture_payload.get("fixture") or fixture_payload
    league = fixture_payload.get("league") or {}
    teams = fixture_payload.get("teams") or {}
    # sample mapping - update to actual provider keys in your environment
    return {
        "provider_id": str(fixture.get("id") or fixture.get("fixture_id")),
        "utc_kickoff": datetime.fromtimestamp(fixture.get("timestamp")) if fixture.get("timestamp") else fixture.get("date"),
        "competition_provider_id": str(league.get("id") or league.get("league_id")),
        "season_name": league.get("season") or None,
        "home_provider_id": str(teams.get("home", {}).get("id")),
        "away_provider_id": str(teams.get("away", {}).get("id")),
        "venue": (fixture.get("venue") or {}).get("name"),
        "status_text": (fixture.get("status") or {}).get("short") or "SCHED",
    }

def normalize_stats_api_football(stats_payload: Dict[str, Any]) -> List[Dict[str, Any]]:
    """
    Convert provider stats structure into a list of {metric_key, team_provider_id, value, period}
    This is highly provider-specific; adjust when you inspect a real response.
    Example return:
      [
        {"metric_key":"corners","team_provider_id":"33","value":5,"period":"FT"},
        ...
      ]
    """
    rows = []
    # Example provider format: {"response":[{"team": {"id":..}, "statistics":[{"type":"Corner","value":5}, ...]}]}
    for team_block in stats_payload:
        team = team_block.get("team") or {}
        tid = str(team.get("id"))
        for stat in team_block.get("statistics", []):
            t = stat.get("type", "").lower().replace(" ", "_")
            # Map provider label to your metric key names
            map_key = {
                "corner": "corners",
                "shots on target": "shots_on_target",
                "yellow cards": "cards_total",  # simple mapping; you may want to split yellow/red
            }.get(stat.get("type", "").strip().lower(), None)

            if map_key:
                rows.append({
                    "metric_key": map_key,
                    "team_provider_id": tid,
                    "value": stat.get("value"),
                    "period": "FT",  # provider may include period; adjust accordingly
                })
    return rows
