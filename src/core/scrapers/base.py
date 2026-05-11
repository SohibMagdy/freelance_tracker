"""
base.py — Abstract base class for all platform scrapers.
New platforms can be added by subclassing BaseScraper and implementing scrape().
"""

from abc import ABC, abstractmethod
from typing import List, Dict


class BaseScraper(ABC):
    """
    Abstract scraper interface. Every platform scraper must implement:
      - platform_name: Human-readable platform name
      - platform_key:  Internal key used in settings (e.g. "mostaql")
      - base_url:      Base URL of the platform
      - scrape():      Returns a list of project dicts
    """

    platform_name: str = ""
    platform_key: str = ""
    base_url: str = ""

    HEADERS = {
        "User-Agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/120.0.0.0 Safari/537.36"
        )
    }

    @abstractmethod
    def scrape(self) -> List[Dict[str, str]]:
        """
        Scrape the platform for current project listings.

        Returns:
            List of dicts, each containing:
              - "site":        Platform name (e.g. "Mostaql")
              - "title":       Project title
              - "description": Project description (may be empty)
              - "link":        Full URL to the project
        """
        pass

    def _fix_relative_link(self, link: str) -> str:
        """Convert relative URLs to absolute using the platform's base_url."""
        if link and link.startswith("/"):
            return self.base_url.rstrip("/") + link
        return link
