"""
resources.py — Asset path resolver for both development and PyInstaller frozen modes.
All icon and resource paths are centralized here.
"""

import os
import sys


def resource_path(filename: str) -> str:
    """
    Resolve the absolute path to a bundled resource file (read-only assets).
    Works in both normal Python execution and PyInstaller frozen builds.
    NOTE: Do NOT use this for writable files (e.g. settings.json).
          PyInstaller's _MEIPASS is a temporary, read-only extraction directory.
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


def writable_path(filename: str) -> str:
    """
    Resolve the absolute path to a writable user-data file.
    Always resolves next to the .exe (frozen) or the project root (dev),
    so the file can be created and updated at runtime on any machine.
    """
    if getattr(sys, "frozen", False):
        # Frozen build: place data next to the .exe
        base_path = os.path.dirname(sys.executable)
    else:
        # Development: project root
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

# Settings file lives next to the executable (writable at runtime).
# writable_path() is used so it is NEVER inside the read-only _MEIPASS bundle.
SETTINGS_FILE = writable_path("settings.json")
