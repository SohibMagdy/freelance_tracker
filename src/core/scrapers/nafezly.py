"""
nafezly.py — Scraper for Nafezly (nafezly.com) freelance platform.
Parses the projects listing page using BeautifulSoup.
"""

import requests
from bs4 import BeautifulSoup
from typing import List, Dict

from .base import BaseScraper


class NafezlyScraper(BaseScraper):
    """Scraper for Nafezly freelance projects."""

    platform_name = "Nafezly"
    platform_key = "nafezly"
    base_url = "https://nafezly.com"

    def scrape(self) -> List[Dict[str, str]]:
        """Scrape latest projects from Nafezly."""
        url = f"{self.base_url}/projects"

        try:
            response = requests.get(
                url,
                headers=self.HEADERS,
                timeout=15
            )
            response.raise_for_status()
        except requests.RequestException as e:
            print(f"[NafezlyScraper] Request failed: {e}")
            return []

        soup = BeautifulSoup(response.text, "html.parser")
        projects = []

        cards = soup.select("div.project-box")

        for card in cards:
            try:
                title_element = card.select_one("a.text-truncate")
                desc_element = card.select_one("h3")

                if not title_element:
                    continue

                title = title_element.get_text(strip=True)
                link = title_element.get("href", "")
                link = self._fix_relative_link(link)

                description = ""
                if desc_element:
                    description = desc_element.get_text(strip=True)

                projects.append({
                    "site": self.platform_name,
                    "title": title,
                    "description": description,
                    "link": link,
                })

            except Exception as e:
                print(f"[NafezlyScraper] Parse error: {e}")

        return projects
