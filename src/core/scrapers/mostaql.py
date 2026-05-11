"""
mostaql.py — Scraper for Mostaql (mostaql.com) freelance platform.
Parses the projects listing page using BeautifulSoup.
"""

import requests
from bs4 import BeautifulSoup
from typing import List, Dict

from .base import BaseScraper


class MostaqlScraper(BaseScraper):
    """Scraper for Mostaql freelance projects."""

    platform_name = "Mostaql"
    platform_key = "mostaql"
    base_url = "https://mostaql.com"

    def scrape(self) -> List[Dict[str, str]]:
        """Scrape latest projects from Mostaql."""
        url = f"{self.base_url}/projects"

        try:
            response = requests.get(
                url,
                headers=self.HEADERS,
                timeout=15
            )
            response.raise_for_status()
        except requests.RequestException as e:
            print(f"[MostaqlScraper] Request failed: {e}")
            return []

        soup = BeautifulSoup(response.text, "html.parser")
        projects = []

        rows = soup.select("tr.project-row")

        for row in rows:
            try:
                title_element = row.select_one("h2 a")
                desc_element = row.select_one("p.project__brief a")

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
                print(f"[MostaqlScraper] Parse error: {e}")

        return projects
