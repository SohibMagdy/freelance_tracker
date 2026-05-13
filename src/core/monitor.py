"""
monitor.py — Standard threading-based monitoring engine.
Runs platform scrapers in a background thread.
Communication with the GUI is done via callbacks to ensure CustomTkinter's
single-threaded requirements are met.
"""

import time
import threading
from datetime import datetime
from typing import List, Set, Callable

from src.core.scrapers.base import BaseScraper
from src.core.scrapers.mostaql import MostaqlScraper
from src.core.scrapers.nafezly import NafezlyScraper
from src.core.scrapers.truelancer import TruelancerScraper
from src.core.notifier import Notifier


# ==========================================
# SCRAPER REGISTRY
# ==========================================

SCRAPER_REGISTRY = {
    "mostaql": MostaqlScraper,
    "nafezly": NafezlyScraper,
    "truelancer": TruelancerScraper,
}


class MonitorThread(threading.Thread):
    """
    Background monitoring thread that periodically scrapes enabled platforms.
    """

    def __init__(self):
        super().__init__(daemon=True)
        self._mutex = threading.Lock()
        self._seen_projects: Set[str] = set()
        self._enabled_platforms: List[str] = []
        self._check_interval: int = 20
        self._notifier = Notifier()
        self._is_initial_load = True
        self._keyword_filter: list = []
        
        self._stop_event = threading.Event()

        # Callbacks to update the UI
        self.on_new_project: Callable[[dict], None] = None
        self.on_status_changed: Callable[[str], None] = None
        self.on_error_occurred: Callable[[str], None] = None
        self.on_cycle_complete: Callable[[int], None] = None
        self.on_finished: Callable[[], None] = None

    # ==========================================
    # CONFIGURATION
    # ==========================================

    def configure(
        self,
        enabled_platforms: List[str],
        check_interval: int = 20,
        notifications_enabled: bool = True,
        keyword_filter: List[str] = None,
    ) -> None:
        with self._mutex:
            self._enabled_platforms = list(enabled_platforms)
            self._check_interval = max(10, min(120, check_interval))
            self._notifier.notifications_enabled = notifications_enabled
            self._keyword_filter = keyword_filter or []

    def update_platforms(self, enabled_platforms: List[str]) -> None:
        with self._mutex:
            self._enabled_platforms = list(enabled_platforms)

    def update_interval(self, interval: int) -> None:
        with self._mutex:
            self._check_interval = max(10, min(120, interval))

    def update_notifications(self, notifications: bool) -> None:
        self._notifier.notifications_enabled = notifications

    # ==========================================
    # THREAD EXECUTION
    # ==========================================

    def run(self) -> None:
        if self.on_status_changed:
            self.on_status_changed("ONLINE")
            
        self._is_initial_load = True

        # Initial load
        self._scrape_cycle(notify=False)
        self._is_initial_load = False

        # Main loop
        while not self._stop_event.is_set():
            self._scrape_cycle(notify=True)

            # Interruptible sleep
            elapsed = 0
            with self._mutex:
                interval = self._check_interval

            while elapsed < interval and not self._stop_event.is_set():
                time.sleep(0.5)
                elapsed += 0.5

        if self.on_status_changed:
            self.on_status_changed("OFFLINE")
            
        if self.on_finished:
            self.on_finished()

    def _scrape_cycle(self, notify: bool = True) -> None:
        with self._mutex:
            platforms = list(self._enabled_platforms)
            keywords = list(self._keyword_filter)

        for platform_key in platforms:
            if self._stop_event.is_set():
                return

            scraper_class = SCRAPER_REGISTRY.get(platform_key)
            if not scraper_class:
                continue

            try:
                scraper = scraper_class()
                projects = scraper.scrape()

                for project in projects:
                    unique_id = project.get("link", "")
                    if not unique_id:
                        continue

                    if unique_id not in self._seen_projects:
                        self._seen_projects.add(unique_id)

                        if keywords and not self._matches_keywords(project, keywords):
                            continue

                        project["timestamp"] = datetime.now().strftime("%H:%M:%S")

                        if notify and not self._is_initial_load:
                            if self.on_new_project:
                                self.on_new_project(project)
                            self._notifier.notify(project)

            except Exception as e:
                error_msg = f"[{platform_key}] Scrape error: {e}"
                print(error_msg)
                if self.on_error_occurred:
                    self.on_error_occurred(error_msg)

        if self.on_cycle_complete:
            self.on_cycle_complete(len(self._seen_projects))

    def _matches_keywords(self, project: dict, keywords: List[str]) -> bool:
        text = (
            project.get("title", "").lower()
            + " "
            + project.get("description", "").lower()
        )
        return any(kw in text for kw in keywords)

    # ==========================================
    # CONTROL
    # ==========================================

    def stop(self) -> None:
        self._stop_event.set()

    @property
    def total_seen(self) -> int:
        return len(self._seen_projects)
