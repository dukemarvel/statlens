from typing import Dict, Any, List
from datetime import datetime

STATUS_MAP = {
    "NS":"SCHED","1H":"LIVE","HT":"HT","2H":"LIVE","ET":"AET","FT":"FT",
    "P":"PEN","AET":"AET","PST":"PPD","CANC":"CANC","ABD":"ABD",
}

def normalize_fixture_api_football(fx: Dict[str, Any]) -> Dict[str, Any]:
    fixture = fx.get("fixture", {})
    league = fx.get("league", {})
    teams = fx.get("teams", {})
    ts = fixture.get("timestamp")
    return {
        "provider_id": str(fixture.get("id")),
        "utc_kickoff": datetime.utcfromtimestamp(ts) if ts else fixture.get("date"),
        "competition_provider_id": str(league.get("id")),
        "season_name": league.get("season"),
        "home_provider_id": str(teams.get("home", {}).get("id")),
        "away_provider_id": str(teams.get("away", {}).get("id")),
        "venue": (fixture.get("venue") or {}).get("name") or "",
        "status_text": STATUS_MAP.get((fixture.get("status") or {}).get("short", ""), "SCHED"),
    }

def normalize_stats_api_football(stats_payload: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    stats_payload is typically a list of two entries (home, away), each:
      {"team":{"id":...},"statistics":[{"type":"Corner Kicks","value":5}, ...]}
    We map:
      - corners            <= ["Corner Kicks","Corners"]
      - shots_on_target    <= ["Shots on Target","Shots on goal"]
      - cards_total        <= sum(["Yellow Cards","Red Cards"])
    """
    rows: List[Dict[str, Any]] = []
    CORNER_KEYS = {"corner kicks", "corners"}
    SOT_KEYS = {"shots on target", "shots on goal"}

    for team_block in (stats_payload or []):
        team = team_block.get("team") or {}
        tid = str(team.get("id"))
        if not tid:
            continue

        stats = team_block.get("statistics") or []
        # normalize labels
        kv = {}
        for s in stats:
            label = (s.get("type") or "").strip().lower()
            kv[label] = s.get("value")

        # corners
        val_corners = next((kv[k] for k in CORNER_KEYS if k in kv), None)
        if isinstance(val_corners, (int, float)):
            rows.append({"metric_key": "corners", "team_provider_id": tid, "value": float(val_corners), "period": "FT"})

        # shots on target
        val_sot = next((kv[k] for k in SOT_KEYS if k in kv), None)
        if isinstance(val_sot, (int, float)):
            rows.append({"metric_key": "shots_on_target", "team_provider_id": tid, "value": float(val_sot), "period": "FT"})

        # cards_total = yellow + red
        y = kv.get("yellow cards")
        r = kv.get("red cards")
        if isinstance(y, (int, float)) or isinstance(r, (int, float)):
            total = (float(y) if isinstance(y, (int, float)) else 0.0) + (float(r) if isinstance(r, (int, float)) else 0.0)
            rows.append({"metric_key": "cards_total", "team_provider_id": tid, "value": total, "period": "FT"})

    return rows