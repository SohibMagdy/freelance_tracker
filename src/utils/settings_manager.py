"""
settings_manager.py — JSON-based settings persistence with thread-safe access.
Handles saving/loading all user preferences including platform toggles,
check interval, keyword filters, and notification preferences.
"""

import json
import os
import threading
from typing import Any


# ==========================================
# DEFAULT SETTINGS
# ==========================================

DEFAULTS = {
    "platforms": {
        "mostaql": True,
        "nafezly": True,
        "truelancer": True,
    },
    "check_interval": 20,          # seconds (10–120)
    "notifications_enabled": True,
    "keyword_filter": "",          # comma-separated keywords
    "start_with_windows": False,
    "start_minimized": False,
}


class SettingsManager:
    """
    Thread-safe settings manager that persists user preferences to a JSON file.
    All reads/writes are guarded by a lock for safe access from monitor threads.
    """

    def __init__(self, filepath: str):
        self._filepath = filepath
        self._lock = threading.Lock()
        self._data: dict = {}
        self.load()

    # ==========================================
    # LOAD / SAVE
    # ==========================================

    def load(self) -> None:
        """Load settings from disk, falling back to defaults for missing keys."""
        with self._lock:
            if os.path.exists(self._filepath):
                try:
                    with open(self._filepath, "r", encoding="utf-8") as f:
                        self._data = json.load(f)
                except (json.JSONDecodeError, IOError):
                    self._data = {}
            else:
                self._data = {}

            # Merge defaults for any missing keys
            for key, default_value in DEFAULTS.items():
                if key not in self._data:
                    self._data[key] = default_value
                elif isinstance(default_value, dict):
                    for sub_key, sub_default in default_value.items():
                        if sub_key not in self._data[key]:
                            self._data[key][sub_key] = sub_default

    def save(self) -> None:
        """Persist current settings to disk."""
        with self._lock:
            try:
                with open(self._filepath, "w", encoding="utf-8") as f:
                    json.dump(self._data, f, indent=2, ensure_ascii=False)
            except IOError as e:
                print(f"[SettingsManager] Failed to save settings: {e}")

    # ==========================================
    # GETTERS / SETTERS
    # ==========================================

    def get(self, key: str, default: Any = None) -> Any:
        """Get a setting value by key."""
        with self._lock:
            return self._data.get(key, default)

    def set(self, key: str, value: Any) -> None:
        """Set a setting value and auto-save."""
        with self._lock:
            self._data[key] = value
        self.save()

    # ==========================================
    # CONVENIENCE METHODS
    # ==========================================

    def is_platform_enabled(self, platform: str) -> bool:
        """Check if a specific platform is enabled for monitoring."""
        platforms = self.get("platforms", {})
        return platforms.get(platform, False)

    def set_platform_enabled(self, platform: str, enabled: bool) -> None:
        """Enable or disable a specific platform."""
        with self._lock:
            if "platforms" not in self._data:
                self._data["platforms"] = {}
            self._data["platforms"][platform] = enabled
        self.save()

    @property
    def check_interval(self) -> int:
        return self.get("check_interval", 20)

    @check_interval.setter
    def check_interval(self, value: int) -> None:
        self.set("check_interval", max(10, min(120, value)))



    @property
    def notifications_enabled(self) -> bool:
        return self.get("notifications_enabled", True)

    @property
    def keyword_filter(self) -> str:
        return self.get("keyword_filter", "")

    @property
    def keyword_list(self) -> list:
        """Return keyword filter as a cleaned list."""
        raw = self.keyword_filter.strip()
        if not raw:
            return []
        return [k.strip().lower() for k in raw.split(",") if k.strip()]
