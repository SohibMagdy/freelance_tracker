"""
Freelance Tracker — Premium PySide6 Desktop Application
========================================================
Main entry point. Initializes the Qt application, loads the theme,
creates the main window, and starts the GUI event loop.

Usage:
    python "Freelance Tracker.py"

Single-instance protection:
    A named Windows mutex is acquired at startup.
    If another instance is already running (e.g. triggered by a Windows
    notification click re-launching the EXE), the new process detects the
    mutex, logs a message, and exits immediately without showing any UI.
    This is the final safety net on top of the protocol-activation approach
    used in notifier.py.
"""

import sys
import os

# ==========================================
# UTF-8 CONSOLE SAFETY (Windows EXE builds)
# ==========================================
# Windows console may use cp1252/cp437 which cannot encode Unicode symbols.
# Reconfigure stdout/stderr to UTF-8 with error replacement to prevent
# UnicodeEncodeError crashes in packaged EXE builds.
try:
    if hasattr(sys.stdout, 'reconfigure'):
        sys.stdout.reconfigure(encoding='utf-8', errors='replace')
    if hasattr(sys.stderr, 'reconfigure'):
        sys.stderr.reconfigure(encoding='utf-8', errors='replace')
except Exception:
    # Fallback: if reconfigure fails (e.g., stdout is None in --windowed mode),
    # redirect to devnull to prevent any write crashes.
    import io
    if sys.stdout is None:
        sys.stdout = io.StringIO()
    if sys.stderr is None:
        sys.stderr = io.StringIO()

# ==========================================
# ENSURE PROJECT ROOT IS ON PYTHON PATH
# ==========================================

# This guarantees that `from src.xxx import ...` works
# regardless of where the script is executed from.
PROJECT_ROOT = os.path.dirname(os.path.abspath(__file__))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)


# ==========================================
# SINGLE-INSTANCE GUARD (Windows Mutex)
# ==========================================

def _acquire_single_instance_mutex():
    """
    Attempt to create a named Windows mutex.

    Returns:
        mutex handle on success (first instance),
        None if the mutex already exists (duplicate instance).

    This prevents Windows notification activation from launching
    a second copy of the application.
    """
    try:
        import ctypes
        import ctypes.wintypes

        MUTEX_NAME = "FreelanceTrackerPRO_SingleInstance_Mutex_v1"

        # CreateMutexW returns a handle; if another process already owns
        # the mutex, GetLastError() returns ERROR_ALREADY_EXISTS (183).
        handle = ctypes.windll.kernel32.CreateMutexW(None, True, MUTEX_NAME)
        last_error = ctypes.windll.kernel32.GetLastError()

        ERROR_ALREADY_EXISTS = 183
        if last_error == ERROR_ALREADY_EXISTS:
            if handle:
                ctypes.windll.kernel32.CloseHandle(handle)
            return None  # Another instance is running

        return handle  # We are the first instance; hold the mutex
    except Exception as e:
        # If mutex check fails for any reason, allow startup (fail-open)
        print(f"[SingleInstance] Mutex check failed (non-fatal): {e}")
        return "UNKNOWN"


def main():
    """Application entry point."""

    # ------------------------------------------
    # 0. Global Exception Hooks
    # ------------------------------------------
    try:
        from src.utils.crash_logger import install_crash_hooks, install_qt_message_handler
        install_crash_hooks()
    except Exception as e:
        print(f"[FATAL] Could not install crash hooks: {e}")

    # ------------------------------------------
    # 0.1 Single-instance guard
    # ------------------------------------------
    mutex_handle = _acquire_single_instance_mutex()

    if mutex_handle is None:
        # Another instance is already running.
        # This can happen if Windows re-activates the EXE when the user
        # clicks a toast notification. Exit silently.
        print("[SingleInstance] [BLOCKED] Duplicate launch detected - another instance "
              "is already running. Exiting immediately.")
        print("[SingleInstance]   (This is expected if triggered by a "
              "notification click. The notification's URL should have opened "
              "in your browser instead.)")
        sys.exit(0)

    print("[SingleInstance] [OK] Mutex acquired - this is the primary instance.")

    print("=" * 55)
    print("  FREELANCE TRACKER PRO - Starting...")
    print("=" * 55)

    # ------------------------------------------
    # 1. Import PySide6 (fail-fast with clear message)
    # ------------------------------------------
    try:
        from PySide6.QtWidgets import QApplication
        from PySide6.QtGui import QIcon, QFont
        from PySide6.QtCore import Qt
    except ImportError:
        print("\n[FATAL] PySide6 is not installed.")
        print("  Run:  pip install PySide6")
        sys.exit(1)

    # Install Qt message handler now that PySide6 is imported
    try:
        install_qt_message_handler()
    except Exception as e:
        print(f"[Warning] Could not install Qt message handler: {e}")

    # ------------------------------------------
    # 2. Create QApplication
    # ------------------------------------------
    # Enable High-DPI scaling for sharp rendering on modern displays
    QApplication.setHighDpiScaleFactorRoundingPolicy(
        Qt.HighDpiScaleFactorRoundingPolicy.PassThrough
    )

    app = QApplication(sys.argv)
    app.setApplicationName("Freelance Tracker PRO")
    app.setOrganizationName("FreelanceTracker")

    # Set app icon
    from src.utils.resources import APP_ICON
    if os.path.exists(APP_ICON):
        app.setWindowIcon(QIcon(APP_ICON))

    # ------------------------------------------
    # 3. Load global theme / stylesheet
    # ------------------------------------------
    from src.ui.styles.theme import get_stylesheet
    app.setStyleSheet(get_stylesheet())
    print("[App] Theme loaded.")

    # ------------------------------------------
    # 4. Load settings
    # ------------------------------------------
    from src.utils.settings_manager import SettingsManager
    from src.utils.resources import SETTINGS_FILE

    settings = SettingsManager(SETTINGS_FILE)
    print(f"[App] Settings loaded - interval={settings.check_interval}s, "
          f"notifications={'ON' if settings.notifications_enabled else 'OFF'}")

    # ------------------------------------------
    # 5. Create and show the main window
    # ------------------------------------------
    from src.ui.main_window import MainWindow

    window = MainWindow(settings)
    window.show()
    print("[App] Main window displayed. Ready to monitor!")
    print("=" * 55)

    # ------------------------------------------
    # 6. Start the Qt event loop
    # ------------------------------------------
    exit_code = app.exec()

    # Release mutex on clean exit (Windows releases it automatically on
    # process termination, but being explicit is good practice)
    try:
        import ctypes
        if mutex_handle and mutex_handle != "UNKNOWN":
            ctypes.windll.kernel32.ReleaseMutex(mutex_handle)
            ctypes.windll.kernel32.CloseHandle(mutex_handle)
            print("[SingleInstance] Mutex released.")
    except Exception:
        pass

    print("[App] Application exited.")
    sys.exit(exit_code)


# ==========================================
# ENTRY POINT
# ==========================================

if __name__ == "__main__":
    main()