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

import subprocess
import sys
import os
import threading
import queue

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
    Uses a Queue to manage dispatching subprocesses.
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
        """Background thread that consumes the queue and launches subprocesses."""
        while True:
            try:
                site, title, link, icon_path = self._queue.get()
                
                # Wait for a slot to open up (prevents 100 subprocesses from spawning at once)
                self._semaphore.acquire()
                
                # Launch the notification in a way that will release the semaphore when done
                threading.Thread(
                    target=self._launch_subprocess_and_wait,
                    args=(site, title, link, icon_path),
                    daemon=True
                ).start()
                
            except Exception as e:
                print(f"[Notifier] Worker loop error: {e}")

    def _launch_subprocess_and_wait(self, site: str, title: str, link: str, icon_path: str):
        """Launch the subprocess and wait for it to exit, then release semaphore."""
        try:
            self._send_blocking(site, title, link, icon_path)
        finally:
            self._semaphore.release()

    def _send_blocking(self, site: str, title: str, link: str, icon_path: str = None) -> None:
        """
        Spawn a subprocess that posts the toast and waits for user interaction.
        """
        safe_title = title.replace("\\", "\\\\").replace('"', '\\"').replace("\n", " ")[:150]
        safe_site  = site.replace("\\", "\\\\").replace('"', '\\"')
        safe_link  = link.replace("\\", "\\\\").replace('"', '\\"')

        icon_arg = ""
        if icon_path:
            safe_icon = icon_path.replace("\\", "\\\\")
            icon_arg = f', icon=r"{safe_icon}"'

        script = f'''
import sys
import webbrowser

try:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass

URL = "{safe_link}"
TITLE = "{safe_site} - New Project"
BODY  = "{safe_title}"

def on_click(args):
    try:
        webbrowser.open(URL)
    except Exception:
        pass
    return args

try:
    from win11toast import toast
    result = toast(
        TITLE,
        BODY,
        on_click=on_click,
        duration="short",
        audio={{"silent": "false"}}{icon_arg}
    )
except Exception:
    pass
'''

        try:
            # We use Popen and wait() to block the thread until the subprocess finishes (toast dismissed/clicked)
            proc = subprocess.Popen(
                [sys.executable, "-c", script],
                creationflags=subprocess.CREATE_NO_WINDOW,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
            )
            # Wait up to 30 seconds for the toast to naturally disappear or be clicked
            try:
                proc.wait(timeout=30)
            except subprocess.TimeoutExpired:
                proc.kill()
        except Exception as e:
            print(f"[Notifier] [ERROR] Subprocess failed: {e}")
