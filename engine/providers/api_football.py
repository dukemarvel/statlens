import os
import time
import logging
from typing import Any, Dict, List, Optional
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

from .base import ProviderAdapter, RateLimitError, ProviderError

logger = logging.getLogger(__name__)

API_FOOTBALL_KEY = os.getenv("API_FOOTBALL_KEY")
API_FOOTBALL_BASE = os.getenv("API_FOOTBALL_BASE", "https://v3.football.api-sports.io")

def _build_session(retries=3, backoff_factor=0.5, status_forcelist=(429, 500, 502, 503, 504)):
    s = requests.Session()
    retry = Retry(
        total=retries,
        backoff_factor=backoff_factor,
        status_forcelist=status_forcelist,
        allowed_methods=frozenset(["GET", "POST"]),
        raise_on_status=False,
        respect_retry_after_header=False  # we'll handle 429 Retry-After manually
    )
    adapter = HTTPAdapter(max_retries=retry)
    s.mount("https://", adapter)
    s.mount("http://", adapter)
    return s

class APIFootballAdapter(ProviderAdapter):
    name = "api_football"

    def __init__(self, api_key: Optional[str] = None, base_url: Optional[str] = None):
        super().__init__(api_key or API_FOOTBALL_KEY, base_url or API_FOOTBALL_BASE)
        if not self.api_key:
            raise ProviderError("API_FOOTBALL_KEY not configured")
        self.session = _build_session()
        # Headers for RapidAPI or native API; adjust if using vendor endpoint
        self.session.headers.update({
            "x-apisports-key": self.api_key,
            "Accept": "application/json",
        })

    def _request(self, path: str, params: Dict[str, Any] = None, timeout: int = 10):
        url = f"{self.base_url.rstrip('/')}/{path.lstrip('/')}"
        try:
            resp = self.session.get(url, params=params, timeout=timeout)
        except requests.RequestException as e:
            logger.exception("Network error talking to API-Football")
            raise ProviderError(str(e))

        # handle 429 specially using Retry-After if present
        if resp.status_code == 429:
            ra = resp.headers.get("Retry-After")
            if ra:
                try:
                    sleep = int(ra)
                except Exception:
                    sleep = 5
            else:
                sleep = 5
            logger.warning("API-Football rate limited; sleeping %s seconds", sleep)
            time.sleep(sleep)
            raise RateLimitError("Rate limited by API-Football")

        if not resp.ok:
            logger.error("API-Football returned %s: %s", resp.status_code, resp.text[:500])
            raise ProviderError(f"status {resp.status_code}")

        data = resp.json()
        # provider-specific envelope: often {"response": [...]}
        return data.get("response", data)

    def fetch_fixtures(self, competition_provider_id: str, date_from: str = None, date_to: str = None) -> List[Dict[str, Any]]:
        params = {"league": competition_provider_id}
        if date_from:
            params["from"] = date_from
        if date_to:
            params["to"] = date_to
        return self._request("fixtures", params=params)

    def fetch_live(self) -> List[Dict[str, Any]]:
        return self._request("fixtures", params={"live": "all"})

    def fetch_match_stats(self, match_provider_id: str) -> Dict[str, Any]:
        # many APIs expose "statistics" or "events" endpoints; adjust accordingly
        # example: GET /fixtures/statistics?fixture=match_provider_id
        return self._request("fixtures/statistics", params={"fixture": match_provider_id})
    
    def fetch_fixtures_by_status(self, league: str, season: int, statuses: str) -> List[dict]:
        # e.g. statuses = "FT-AET-PEN-1H-HT-2H-ET-BT-P"
        return self._request("fixtures", params={"league": league, "season": season, "status": statuses})

    def fetch_fixtures_by_ids(self, ids: List[int]) -> List[dict]:
        out = []
        for i in range(0, len(ids), 20):
            chunk = ids[i:i+20]
            resp = self._request("fixtures", params={"ids": "-".join(map(str, chunk))})
            out.extend(resp if isinstance(resp, list) else [])
            time.sleep(1)  # be nice on free tier
        return out

