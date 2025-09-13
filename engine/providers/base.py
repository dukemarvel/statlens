from abc import ABC, abstractmethod
from typing import Any, Dict, List

class ProviderError(Exception):
    pass

class RateLimitError(ProviderError):
    pass

class ProviderAdapter(ABC):
    """
    Base interface for providers.
    Implementations must return normalized dicts the mapper can use.
    """

    name: str  # provider key, e.g. "api_football"

    def __init__(self, api_key: str = None, base_url: str = None):
        self.api_key = api_key
        self.base_url = base_url

    @abstractmethod
    def fetch_fixtures(self, competition_provider_id: str, date_from: str = None, date_to: str = None) -> List[Dict[str, Any]]:
        """Return a list of fixture payloads (raw provider JSON)."""

    @abstractmethod
    def fetch_live(self) -> List[Dict[str, Any]]:
        """Return a list of live match payloads."""

    @abstractmethod
    def fetch_match_stats(self, match_provider_id: str) -> Dict[str, Any]:
        """Return stats for a single match (raw provider JSON)."""
