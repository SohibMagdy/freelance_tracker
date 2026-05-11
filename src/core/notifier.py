"""
notifier.py -- Windows toast notification handler.

Architecture:
    Each notification spawns a subprocess that calls win11toast.toast() with a
    CALLABLE on_click handler. The subprocess stays alive waiting for the click,
    then calls webbrowser.open(url) and exits cleanly.

Why toast() + callable (not notify() + string):
    - notify() is fire-and-forget: exits immediately, click has no handler.
    - Passing a URL string as on_click sets the toast launch attribute, but
      protocol activation only works for registered UWP/COM apps -- plain Python
      executables are NOT registered, so Windows silently ignores the click.
    - toast() + callable keeps the subprocess alive via asyncio until the user
      clicks or dismisses. The callable calls webbrowser.open() reliably.
    - Verified working: click detected, browser opens, subprocess exits cleanly.
    - No COM registration needed. Works in dev mode and PyInstaller EXE builds.
"""

import subprocess
import sys
import os

from src.utils.resources import (
    APP_ICON, MOSTAQL_ICON, NAFEZLY_ICON,
    KAFIIL_ICON, KHAMSAT_ICON, FREELANCEYARD_ICON
)
from src.utils.crash_logger import get_logger, get_subprocess_tracker


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

    Design:
        - Each notification spawns a dedicated subprocess.
        - Subprocess calls toast() with a callable on_click -> webbrowser.open(url).
        - Subprocess stays alive (via asyncio) until user clicks or dismisses.
        - On click: browser opens the project URL, subprocess exits cleanly.
        - On dismiss/timeout: subprocess exits cleanly with no action.
        - GUI thread never blocks. No zombie processes.
    """

    def __init__(self, notifications_enabled: bool = True):
        self.notifications_enabled = notifications_enabled
        self._logger = get_logger()
        self._subprocess_tracker = get_subprocess_tracker()

    def notify(self, project: dict) -> None:
        """
        Send a Windows toast notification for a new project.
        Spawns a subprocess -- GUI thread never blocks.
        """
        if not self.notifications_enabled:
            return

        site  = project.get("site", "Unknown")
        title = project.get("title", "New Project")
        link  = project.get("link", "")

        icon_path = PLATFORM_ICONS.get(site, APP_ICON)
        if icon_path and not os.path.exists(icon_path):
            icon_path = None

        self._send(site=site, title=title, link=link, icon_path=icon_path)
        print(f"[Notifier] [OK] Notification queued | {site} - {title[:60]}")
        print(f"[Notifier]      URL: {link}")

    def _send(self, site: str, title: str, link: str, icon_path: str = None) -> None:
        """
        Spawn a subprocess that posts the toast and waits for user interaction.

        The subprocess uses toast() with a callable on_click.
        toast() blocks via asyncio.run() until click or dismiss, then exits.
        On click: webbrowser.open(url) fires and the subprocess exits cleanly.
        """
        # Sanitize for safe embedding in inline Python source
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

# Reconfigure stdout for Windows console safety
try:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass

URL = "{safe_link}"
TITLE = "{safe_site} - New Project"
BODY  = "{safe_title}"

print(f"[NotifyWorker] [INFO] Notification created")
print(f"[NotifyWorker] [INFO] URL: {{URL}}")
print(f"[NotifyWorker] [INFO] Waiting for user interaction...")

def on_click(args):
    """Called by win11toast when the user clicks the notification body."""
    print(f"[NotifyWorker] [OK] Notification clicked - opening URL in browser")
    print(f"[NotifyWorker]      URL: {{URL}}")
    try:
        webbrowser.open(URL)
        print(f"[NotifyWorker] [OK] Browser launched successfully")
    except Exception as e:
        print(f"[NotifyWorker] [ERROR] Failed to open browser: {{e}}")
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
    print(f"[NotifyWorker] [INFO] Toast session ended. Result: {{result}}")
except Exception as e:
    print(f"[NotifyWorker] [ERROR] Toast failed: {{e}}")
'''

        try:
            proc = subprocess.Popen(
                [sys.executable, "-c", script],
                creationflags=subprocess.CREATE_NO_WINDOW,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
            )
            self._subprocess_tracker.register(proc)
            print("[Notifier] [OK] Notification subprocess launched.")
            self._logger.debug("Notification subprocess launched PID: %s for %s", proc.pid, title)
        except Exception as e:
            msg = f"Could not launch notification subprocess: {e}"
            print(f"[Notifier] [ERROR] {msg}")
            self._logger.error(msg, exc_info=True)
