"""
main_window.py — Main application window using CustomTkinter.
Composes the sidebar, dashboard, and settings pages,
and manages the MonitorThread lifecycle with full state management.
"""

import os
from datetime import datetime
import customtkinter as ctk

from src.ui.sidebar import Sidebar
from src.ui.pages.dashboard import DashboardPage
from src.ui.pages.settings import SettingsPage
from src.ui.styles.colors import Colors
from src.core.monitor import MonitorThread
from src.utils.settings_manager import SettingsManager
from src.utils.resources import APP_ICON


class MainWindow(ctk.CTk):
    """
    Main window that integrates all UI components
    and manages the background monitoring thread.
    """

    def __init__(self, settings: SettingsManager):
        super().__init__()
        self.settings = settings
        self.monitor: MonitorThread = None
        self.is_monitoring = False

        # ==========================================
        # WINDOW SETUP
        # ==========================================
        self.title("Freelance Tracker PRO")
        self.geometry("1100x720")
        self.minsize(960, 620)
        
        # Use native Windows dark title bar by configuring the window background
        self.configure(fg_color=Colors.BG_DARK)
        
        # Window icon (CustomTkinter uses standard tkinter iconbitmap or iconphoto)
        if os.path.exists(APP_ICON):
            try:
                self.iconbitmap(APP_ICON)
            except Exception as e:
                print(f"[App] Could not set icon: {e}")

        # ==========================================
        # BUILD UI
        # ==========================================
        
        # Root layout using pack
        self.sidebar = Sidebar(self, on_page_change=self._switch_page)
        self.sidebar.pack(side="left", fill="y")
        
        # Container for pages
        self.pages_container = ctk.CTkFrame(self, fg_color="transparent")
        self.pages_container.pack(side="right", fill="both", expand=True)

        # Pages
        self.dashboard = DashboardPage(
            self.pages_container, 
            self.settings,
            on_start=self._start_monitoring,
            on_stop=self._stop_monitoring
        )
        self.settings_page = SettingsPage(
            self.pages_container, 
            self.settings,
            on_settings_changed=self._on_settings_changed
        )
        
        # Show Dashboard initially
        self.dashboard.pack(fill="both", expand=True)
        self.current_page = self.dashboard

        # Intercept window close
        self.protocol("WM_DELETE_WINDOW", self._on_closing)
        
        print("[App] Main window initialized successfully.")
        print(f"[App] Settings loaded from: {self.settings._filepath}")

    # ==========================================
    # PAGE NAVIGATION
    # ==========================================

    def _switch_page(self, index: int):
        self.current_page.pack_forget()
        
        if index == Sidebar.PAGE_DASHBOARD:
            self.dashboard.pack(fill="both", expand=True)
            self.current_page = self.dashboard
        elif index == Sidebar.PAGE_SETTINGS:
            self.settings_page.pack(fill="both", expand=True)
            self.current_page = self.settings_page

    # ==========================================
    # MONITORING ENGINE
    # ==========================================

    def _start_monitoring(self):
        """Start the background monitoring thread."""
        if self.is_monitoring:
            print("[App] Monitor already running - ignoring duplicate start.")
            return

        self.monitor = MonitorThread()

        # Gather settings
        enabled_platforms = self.dashboard.get_enabled_platforms()
        check_interval = self.settings.check_interval
        notifications_enabled = self.settings.notifications_enabled
        keyword_filter = self.settings.keyword_list

        self.monitor.configure(
            enabled_platforms=enabled_platforms,
            check_interval=check_interval,
            notifications_enabled=notifications_enabled,
            keyword_filter=keyword_filter,
        )

        # Connect thread callbacks to GUI methods
        self.monitor.on_new_project = self._queue_new_project
        self.monitor.on_status_changed = self._queue_status_changed
        self.monitor.on_error_occurred = self._queue_error
        self.monitor.on_cycle_complete = self._queue_cycle_complete
        self.monitor.on_finished = self._queue_monitor_finished

        self.monitor.start()
        self.is_monitoring = True

        print("=" * 50)
        print(f"[App] Monitoring STARTED at {datetime.now().strftime('%H:%M:%S')}")
        print(f"[App] Platforms: {enabled_platforms}")
        print(f"[App] Interval: {check_interval}s")
        print("=" * 50)

    def _stop_monitoring(self):
        """Stop the background monitoring thread gracefully."""
        if not self.is_monitoring or not self.monitor:
            print("[App] No active monitor to stop.")
            return

        print(f"[App] Stopping monitor at {datetime.now().strftime('%H:%M:%S')}...")
        self.monitor.stop()
        # Don't block the GUI — the on_finished callback will handle cleanup

    # ==========================================
    # MONITOR CALLBACK HANDLERS (Thread-Safe via .after)
    # ==========================================

    def _queue_new_project(self, project: dict):
        self.after(0, lambda: self._on_new_project(project))

    def _on_new_project(self, project: dict):
        site = project.get("site", "?")
        title = project.get("title", "?")
        print(f"[Feed] NEW from {site}: {title}")
        self.dashboard.add_project(project)

    def _queue_status_changed(self, status: str):
        self.after(0, lambda: self._on_status_changed(status))

    def _on_status_changed(self, status: str):
        print(f"[App] Status changed: {status}")

    def _queue_error(self, error_msg: str):
        self.after(0, lambda: self._on_error(error_msg))

    def _on_error(self, error_msg: str):
        print(f"[Error] {error_msg}")

    def _queue_cycle_complete(self, total_count: int):
        self.after(0, lambda: self._on_cycle_complete(total_count))

    def _on_cycle_complete(self, total_count: int):
        self.dashboard.update_total_count(total_count)

    def _queue_monitor_finished(self):
        self.after(0, self._on_monitor_finished)

    def _on_monitor_finished(self):
        self.is_monitoring = False
        self.dashboard.set_offline()
        print("[App] Monitor thread finished and cleaned up.")

    # ==========================================
    # PLATFORM / SETTINGS UPDATES
    # ==========================================

    def _on_settings_changed(self):
        """Apply settings changes to the running monitor."""
        print("[App] Settings updated.")
        
        if self.is_monitoring and self.monitor:
            platforms = self.dashboard.get_enabled_platforms()
            self.monitor.update_platforms(platforms)
            self.monitor.update_interval(self.settings.check_interval)
            self.monitor.update_notifications(notifications=self.settings.notifications_enabled)

    # ==========================================
    # APPLICATION LIFECYCLE
    # ==========================================

    def _on_closing(self):
        """Handle window close."""
        self.withdraw()  # Hide window to system tray
        
    def quit_app(self):
        """Clean shutdown: stop monitor, save settings, exit."""
        print("[App] Shutting down...")
        self.withdraw()

        # Stop monitoring thread
        if self.is_monitoring and self.monitor:
            self.monitor.stop()
            self.monitor.join(timeout=3.0)

        # Save settings on exit
        self.settings.save()
        print("[App] Settings saved. Goodbye!")
        self.quit()
