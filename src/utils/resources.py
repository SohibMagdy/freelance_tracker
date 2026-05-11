"""
resources.py — Asset path resolver for both development and PyInstaller frozen modes.
All icon and resource paths are centralized here.
"""

import os
import sys


def resource_path(filename: str) -> str:
    """
    Resolve the absolute path to a bundled resource file.
    Works in both normal Python execution and PyInstaller frozen builds.
    """
    try:
        # PyInstaller stores extracted files in a temp folder
        base_path = sys._MEIPASS
    except AttributeError:
        # Normal development — assets are in the project root
        base_path = os.path.abspath(
            os.path.join(os.path.dirname(__file__), "..", "..")
        )

    return os.path.join(base_path, filename)


# ==========================================
# APPLICATION ICON
# ==========================================

APP_ICON = resource_path(os.path.join("icons", "FWT.ico"))

# ==========================================
# PLATFORM ICONS (for notifications)
# ==========================================

MOSTAQL_ICON = resource_path(os.path.join("icons", "mostaql.ico"))
NAFEZLY_ICON = resource_path(os.path.join("icons", "nafezly.ico"))
KAFIIL_ICON  = resource_path(os.path.join("icons", "kafiil.ico"))
KHAMSAT_ICON = resource_path(os.path.join("icons", "khamsat.ico"))
FREELANCEYARD_ICON = resource_path(os.path.join("icons", "freelanceyard.ico"))

# ==========================================
# SETTINGS FILE
# ==========================================

# Settings file lives next to the executable / project root
SETTINGS_FILE = resource_path("settings.json")
