"""
Freelance Tracker PRO — Premium CustomTkinter Desktop Application
========================================================
Main entry point. Initializes CustomTkinter, loads settings,
sets up crash logging, system tray, and starts the GUI event loop.
"""

import sys
import os
print("[Startup] Python initialized", flush=True)
import ctypes
import traceback
import threading
from datetime import datetime
import customtkinter as ctk
print("[Startup] Imports completed", flush=True)

# ==========================================
# UTF-8 CONSOLE SAFETY (Windows EXE builds)
# ==========================================
try:
    if hasattr(sys.stdout, 'reconfigure'):
        sys.stdout.reconfigure(encoding='utf-8', errors='replace')
    if hasattr(sys.stderr, 'reconfigure'):
        sys.stderr.reconfigure(encoding='utf-8', errors='replace')
    print("[Startup] Stdout/Stderr reconfigured", flush=True)
except Exception:
    import io
    if sys.stdout is None:
        sys.stdout = io.StringIO()
    if sys.stderr is None:
        sys.stderr = io.StringIO()

# ==========================================
# ENSURE PROJECT ROOT IS ON PYTHON PATH
# ==========================================
PROJECT_ROOT = os.path.dirname(os.path.abspath(__file__))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)
print("[Startup] sys.path configured", flush=True)

# ==========================================
# GLOBAL CRASH LOGGING
# ==========================================
LOGS_DIR = os.path.join(PROJECT_ROOT, "logs")
ERROR_LOG_FILE = os.path.join(LOGS_DIR, "error.log")

def setup_crash_logging():
    os.makedirs(LOGS_DIR, exist_ok=True)
    
    def handle_exception(exc_type, exc_value, exc_traceback):
        if issubclass(exc_type, KeyboardInterrupt):
            sys.__excepthook__(exc_type, exc_value, exc_traceback)
            return
            
        with open(ERROR_LOG_FILE, "a", encoding="utf-8") as f:
            f.write(f"\\n--- CRASH: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} ---\\n")
            traceback.print_exception(exc_type, exc_value, exc_traceback, file=f)
            
        print(f"[FATAL ERROR] An unexpected error occurred. Details written to {ERROR_LOG_FILE}", file=sys.stderr)
        
    def handle_thread_exception(args):
        with open(ERROR_LOG_FILE, "a", encoding="utf-8") as f:
            f.write(f"\\n--- THREAD CRASH: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} ---\\n")
            traceback.print_exception(args.exc_type, args.exc_value, args.exc_traceback, file=f)
            
        print(f"[FATAL ERROR] Thread crash. Details written to {ERROR_LOG_FILE}", file=sys.stderr)

    sys.excepthook = handle_exception
    threading.excepthook = handle_thread_exception

# ==========================================
# SINGLE-INSTANCE GUARD (Windows Mutex)
# ==========================================
def _acquire_single_instance_mutex():
    try:
        import ctypes.wintypes
        MUTEX_NAME = "FreelanceTrackerPRO_SingleInstance_Mutex_v2"
        handle = ctypes.windll.kernel32.CreateMutexW(None, True, MUTEX_NAME)
        last_error = ctypes.windll.kernel32.GetLastError()
        ERROR_ALREADY_EXISTS = 183
        if last_error == ERROR_ALREADY_EXISTS:
            if handle:
                ctypes.windll.kernel32.CloseHandle(handle)
            return None
        return handle
    except Exception as e:
        print(f"[SingleInstance] Mutex check failed (non-fatal): {e}")
        return "UNKNOWN"

# ==========================================
# SYSTEM TRAY (PyStray)
# ==========================================
def run_system_tray(app_window):
    """Run pystray system tray icon in a separate thread."""
    try:
        import pystray
        from PIL import Image
        from src.utils.resources import APP_ICON
        
        # Load icon
        if os.path.exists(APP_ICON):
            image = Image.open(APP_ICON)
        else:
            # Fallback 16x16 black image
            image = Image.new('RGB', (16, 16), color=(0, 0, 0))
        print("[Startup] Icons loaded")

        def show_window(icon, item):
            app_window.after(0, app_window.deiconify)

        def quit_app(icon, item):
            icon.stop()
            app_window.after(0, app_window.quit_app)

        menu = pystray.Menu(
            pystray.MenuItem('Show Window', show_window, default=True),
            pystray.MenuItem('Quit', quit_app)
        )

        icon = pystray.Icon("Freelance Tracker PRO", image, "Freelance Tracker PRO", menu)
        print("[Startup] Tray initialized")
        icon.run()
    except ImportError:
        print("[SystemTray] pystray or Pillow not installed. Tray disabled.")
    except Exception as e:
        print(f"[SystemTray] Failed to start system tray: {e}")


def main():
    """Application entry point."""
    setup_crash_logging()

    mutex_handle = _acquire_single_instance_mutex()
    print("[Startup] Mutex acquired", flush=True)
    if mutex_handle is None:
        print("[SingleInstance] [BLOCKED] Duplicate launch detected. Exiting immediately.", flush=True)
        sys.exit(0)

    print("=" * 55, flush=True)
    print("  FREELANCE TRACKER PRO (CustomTkinter) - Starting...", flush=True)
    print("=" * 55, flush=True)

    # Setup CustomTkinter Global Appearance
    ctk.set_appearance_mode("Dark")
    ctk.set_default_color_theme("blue")
    print("[Startup] CustomTkinter initialized", flush=True)

    # Load settings
    from src.utils.settings_manager import SettingsManager
    from src.utils.resources import SETTINGS_FILE
    settings = SettingsManager(SETTINGS_FILE)
    print(f"[App] Settings loaded - interval={settings.check_interval}s, "
          f"notifications={'ON' if settings.notifications_enabled else 'OFF'}", flush=True)

    # Create main window
    from src.ui.main_window import MainWindow
    print("[Startup] MainWindow class imported", flush=True)
    window = MainWindow(settings)
    print("[Startup] MainWindow created", flush=True)
    
    # Start System Tray in background
    tray_thread = threading.Thread(target=run_system_tray, args=(window,), daemon=True)
    tray_thread.start()

    # Determine startup visibility
    if settings.get("start_minimized", False):
        window.withdraw()
        print("[App] Started minimized to tray.")
    else:
        window.deiconify()
        print("[App] Main window displayed.")

    # Start mainloop (blocks until app exits)
    print("[Startup] Entering mainloop", flush=True)
    window.mainloop()

    # Cleanup
    try:
        if mutex_handle and mutex_handle != "UNKNOWN":
            ctypes.windll.kernel32.ReleaseMutex(mutex_handle)
            ctypes.windll.kernel32.CloseHandle(mutex_handle)
    except Exception:
        pass
    print("[App] Application exited.")

if __name__ == "__main__":
    main()