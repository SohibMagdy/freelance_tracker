"""
monitor.py — QThread-based monitoring engine.
Runs platform scrapers in a background thread, emitting Qt signals
when new projects are found. The GUI subscribes to these signals
and never blocks.
"""

import time
from datetime import datetime
from typing import List, Set

from PySide6.QtCore import QThread, Signal, QMutex

from src.core.scrapers.base import BaseScraper
from src.core.scrapers.mostaql import MostaqlScraper
from src.core.scrapers.nafezly import NafezlyScraper
from src.core.scrapers.truelancer import TruelancerScraper
from src.core.notifier import Notifier
from src.utils.crash_logger import (
    get_logger,
    get_watchdog,
    get_rate_limiter,
    get_subprocess_tracker,
    safe_qthread_run
)


# ==========================================
# SCRAPER REGISTRY
# ==========================================

SCRAPER_REGISTRY = {
    "mostaql": MostaqlScraper,
    "nafezly": NafezlyScraper,
    "truelancer": TruelancerScraper,
}


class MonitorThread(QThread):
    """
    Background monitoring thread that periodically scrapes enabled platforms.

    Signals:
        new_project(dict):    Emitted when a new project is found
        status_changed(str):  Emitted when monitoring status changes
        error_occurred(str):  Emitted when an error occurs
        cycle_complete(int):  Emitted after each scraping cycle with project count
    """

    # ==========================================
    # SIGNALS
    # ==========================================

    new_project = Signal(dict)       # {site, title, description, link, timestamp}
    status_changed = Signal(str)     # "ONLINE" or "OFFLINE"
    error_occurred = Signal(str)     # Error message
    cycle_complete = Signal(int)     # Total projects seen count

    def __init__(self, parent=None):
        super().__init__(parent)
        self._mutex = QMutex()
        self._seen_projects: Set[str] = set()
        self._enabled_platforms: List[str] = []
        self._check_interval: int = 20
        self._notifier = Notifier()
        self._is_initial_load = True
        self._keyword_filter: list = []
        self._logger = get_logger()
        self._watchdog = get_watchdog()
        self._rate_limiter = get_rate_limiter()
        self._subprocess_tracker = get_subprocess_tracker()

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
        """Configure the monitor before starting."""
        self._mutex.lock()
        self._enabled_platforms = list(enabled_platforms)
        self._check_interval = max(10, min(120, check_interval))
        self._notifier.notifications_enabled = notifications_enabled
        self._keyword_filter = keyword_filter or []
        self._mutex.unlock()

    def update_platforms(self, enabled_platforms: List[str]) -> None:
        """Update enabled platforms while running."""
        self._mutex.lock()
        self._enabled_platforms = list(enabled_platforms)
        self._mutex.unlock()

    def update_interval(self, interval: int) -> None:
        """Update check interval while running."""
        self._mutex.lock()
        self._check_interval = max(10, min(120, interval))
        self._mutex.unlock()

    def update_notifications(self, notifications: bool) -> None:
        """Update notification preferences while running."""
        self._notifier.notifications_enabled = notifications

    # ==========================================
    # THREAD EXECUTION
    # ==========================================

    @safe_qthread_run
    def run(self) -> None:
        """Main thread loop — scrape, compare, emit, sleep, repeat."""
        self.status_changed.emit("ONLINE")
        self._is_initial_load = True
        self._logger.info("MonitorThread started.")

        # Initial load — populate seen_projects without notifications
        self._scrape_cycle(notify=False)
        self._is_initial_load = False

        # Main monitoring loop
        while not self.isInterruptionRequested():
            self._scrape_cycle(notify=True)

            # Interruptible sleep — check every 500ms for stop requests
            elapsed = 0
            self._mutex.lock()
            interval = self._check_interval
            self._mutex.unlock()

            while elapsed < interval and not self.isInterruptionRequested():
                self.msleep(500)
                elapsed += 0.5
                
                # Watchdog heartbeat
                self._watchdog.heartbeat("MonitorThread")
                
                # Drain queued notifications
                queued_project = self._rate_limiter.drain_one()
                if queued_project:
                    self._notifier.notify(queued_project)
                
                # Clean up finished subprocesses
                self._subprocess_tracker.cleanup()
                
                # Periodic watchdog log (every ~300s, WatchdogLogger handles internal timing, but actually WatchdogLogger.log_status() logs it unconditionally. Let's not call log_status here, just heartbeat)

        self.status_changed.emit("OFFLINE")
        self._logger.info("MonitorThread stopped.")
        # Kill any remaining subprocesses when monitor stops
        self._subprocess_tracker.kill_all()

    def _scrape_cycle(self, notify: bool = True) -> None:
        """Run one scraping cycle across all enabled platforms."""
        self._mutex.lock()
        platforms = list(self._enabled_platforms)
        keywords = list(self._keyword_filter)
        self._mutex.unlock()

        for platform_key in platforms:
            if self.isInterruptionRequested():
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

                        # Apply keyword filter
                        if keywords and not self._matches_keywords(project, keywords):
                            continue

                        # Add timestamp
                        project["timestamp"] = datetime.now().strftime("%H:%M:%S")

                        if notify and not self._is_initial_load:
                            # Emit signal for GUI
                            self.new_project.emit(project)
                            # Queue for Windows notification (rate limited)
                            if self._rate_limiter.try_send(project):
                                self._notifier.notify(project)

            except Exception as e:
                error_msg = f"[{platform_key}] Scrape error: {e}"
                self._logger.error(error_msg, exc_info=True)
                print(error_msg)
                self.error_occurred.emit(error_msg)

        self.cycle_complete.emit(len(self._seen_projects))

    def _matches_keywords(self, project: dict, keywords: List[str]) -> bool:
        """Check if a project matches any of the keyword filters."""
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
        """Request the thread to stop gracefully."""
        self.requestInterruption()

    @property
    def total_seen(self) -> int:
        """Return count of total projects seen."""
        return len(self._seen_projects)
