"""
notifier.py -- Windows toast notification handler.

Architecture:
    Each notification spawns a subprocess that calls win11toast.toast() with a
    CALLABLE on_click handler. The subprocess stays alive waiting for the click,
    then calls webbrowser.open(url) and exits cleanly.

    To prevent subprocess accumulation, we use a background thread with a bounded
    queue and a concurrency limiter (Semaphore) to ensure no more than 3
    toast processes run simultaneously.
"""

import sys
import os
import threading
import queue
import traceback
try:
    from win11toast import toast
except ImportError:
    toast = None

from src.utils.resources import (
    APP_ICON, MOSTAQL_ICON, NAFEZLY_ICON,
    KAFIIL_ICON, KHAMSAT_ICON, FREELANCEYARD_ICON
)

# ==========================================
# ICON MAPPING
# ==========================================

PLATFORM_ICONS = {
    "Mostaql":       MOSTAQL_ICON,
    "Nafezly":       NAFEZLY_ICON,
    "Kafiil":        KAFIIL_ICON,
    "Khamsat":       KHAMSAT_ICON,
    "FreelanceYard": FREELANCEYARD_ICON,
    "Truelancer":    APP_ICON,
}


class Notifier:
    """
    Handles Windows toast notifications for new freelance projects.
    Uses a Queue to manage dispatching toast notifications natively.
    """

    def __init__(self, notifications_enabled: bool = True):
        self.notifications_enabled = notifications_enabled
        self._queue = queue.Queue(maxsize=100)
        self._semaphore = threading.Semaphore(3)  # Max 3 active notifications at once
        
        self._worker_thread = threading.Thread(target=self._worker_loop, daemon=True)
        self._worker_thread.start()

    def notify(self, project: dict) -> None:
        """
        Queue a Windows toast notification for a new project.
        """
        if not self.notifications_enabled:
            return

        site  = project.get("site", "Unknown")
        title = project.get("title", "New Project")
        link  = project.get("link", "")

        icon_path = PLATFORM_ICONS.get(site, APP_ICON)
        if icon_path and not os.path.exists(icon_path):
            icon_path = None

        try:
            self._queue.put_nowait((site, title, link, icon_path))
            print(f"[Notifier] [OK] Notification queued | {site} - {title[:60]}")
        except queue.Full:
            print(f"[Notifier] [WARN] Notification queue is full. Dropping: {title[:30]}")

    def _worker_loop(self):
        """Background thread that consumes the queue and displays native toast notifications."""
        while True:
            try:
                site, title, link, icon_path = self._queue.get()
                
                # Wait for a slot to open up (prevents 100 subprocesses from spawning at once)
                self._semaphore.acquire()
                
                # Launch the notification in a way that will release the semaphore when done
                threading.Thread(
                    target=self._display_toast,
                    args=(site, title, link, icon_path),
                    daemon=True
                ).start()
                
            except Exception as e:
                print(f"[Notifier] Worker loop error: {e}")

    def _display_toast(self, site: str, title: str, link: str, icon_path: str):
        """Display the native toast notification and wait for user interaction, then release semaphore."""
        try:
            print(f"[Notifier] [INFO] Toast requested for: {title[:50]}...")
            if toast is None:
                print("[Notifier] [ERROR] win11toast is not installed. Cannot display notification.")
                return

            safe_title = title.replace("\\n", " ")[:150]
            safe_site  = site
            safe_link  = link

            kwargs = {
                "title": f"{safe_site} - New Project",
                "body": safe_title,
                "on_click": safe_link,  # Native URL handling
                "duration": "short",
                "audio": {"src": "ms-winsoundevent:Notification.Default", "silent": "false"}
            }

            if icon_path and os.path.exists(icon_path):
                kwargs["icon"] = icon_path

            # This call blocks until the toast is dismissed or clicked
            result = toast(**kwargs)
            print(f"[Notifier] [SUCCESS] Toast displayed successfully. Result: {result}")

        except Exception as e:
            print(f"[Notifier] [ERROR] Toast execution failed: {e}")
            traceback.print_exc()
        finally:
            self._semaphore.release()
