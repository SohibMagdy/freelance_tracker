"""
main_window.py — Main application window with frameless design.
Composes the title bar, sidebar, dashboard, and settings pages,
and manages the MonitorThread lifecycle with full state management.
"""

import os
from datetime import datetime

from PySide6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QStackedWidget, QSystemTrayIcon, QMenu, QApplication,
    QGraphicsDropShadowEffect
)
from PySide6.QtCore import Qt, Slot, QTimer
from PySide6.QtGui import QIcon, QAction, QColor

from src.ui.title_bar import TitleBar
from src.ui.sidebar import Sidebar
from src.ui.pages.dashboard import DashboardPage
from src.ui.pages.settings import SettingsPage
from src.ui.styles.theme import Colors
from src.core.monitor import MonitorThread
from src.utils.settings_manager import SettingsManager
from src.utils.resources import APP_ICON


class MainWindow(QMainWindow):
    """
    Frameless main window that integrates all UI components
    and manages the background monitoring thread.
    """

    def __init__(self, settings: SettingsManager, parent=None):
        super().__init__(parent)
        self._settings = settings
        self._monitor: MonitorThread = None
        self._is_monitoring = False

        # ==========================================
        # WINDOW SETUP
        # ==========================================

        self.setWindowTitle("Freelance Tracker PRO")
        self.setMinimumSize(960, 620)
        self.resize(1100, 720)
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.Window)
        self.setAttribute(Qt.WA_TranslucentBackground, False)

        # Window icon
        if os.path.exists(APP_ICON):
            self.setWindowIcon(QIcon(APP_ICON))

        # ==========================================
        # BUILD UI
        # ==========================================

        central = QWidget()
        central.setObjectName("CentralWidget")
        central.setStyleSheet(f"""
            #CentralWidget {{
                background-color: {Colors.BG_DARK};
                border: 1px solid {Colors.BORDER_SUBTLE};
                border-radius: 10px;
            }}
        """)
        self.setCentralWidget(central)

        root_layout = QVBoxLayout(central)
        root_layout.setContentsMargins(0, 0, 0, 0)
        root_layout.setSpacing(0)

        # Title bar
        self._title_bar = TitleBar()
        self._title_bar.minimize_clicked.connect(self.showMinimized)
        self._title_bar.maximize_clicked.connect(self._toggle_maximize)
        self._title_bar.close_clicked.connect(self.close)
        root_layout.addWidget(self._title_bar)

        # Body: sidebar + stacked pages
        body = QHBoxLayout()
        body.setContentsMargins(0, 0, 0, 0)
        body.setSpacing(0)

        self._sidebar = Sidebar()
        self._sidebar.page_changed.connect(self._switch_page)
        body.addWidget(self._sidebar)

        # Page stack
        self._pages = QStackedWidget()
        self._dashboard = DashboardPage(self._settings)
        self._settings_page = SettingsPage(self._settings)

        self._pages.addWidget(self._dashboard)      # index 0
        self._pages.addWidget(self._settings_page)   # index 1

        body.addWidget(self._pages, stretch=1)
        root_layout.addLayout(body, stretch=1)

        # ==========================================
        # CONNECT SIGNALS
        # ==========================================

        # Dashboard signals
        self._dashboard.start_monitoring.connect(self._start_monitoring)
        self._dashboard.stop_monitoring.connect(self._stop_monitoring)
        self._dashboard.platform_toggled.connect(self._on_platform_toggled)

        # Settings signals
        self._settings_page.settings_changed.connect(self._on_settings_changed)

        # ==========================================
        # SYSTEM TRAY
        # ==========================================

        self._tray = None
        self._setup_tray()

        print("[App] Main window initialized successfully.")
        print(f"[App] Settings loaded from: {self._settings._filepath}")

    # ==========================================
    # PAGE NAVIGATION
    # ==========================================

    @Slot(int)
    def _switch_page(self, index: int):
        self._pages.setCurrentIndex(index)

    # ==========================================
    # WINDOW CONTROLS
    # ==========================================

    def _toggle_maximize(self):
        if self.isMaximized():
            self.showNormal()
        else:
            self.showMaximized()

    # ==========================================
    # MONITORING ENGINE
    # ==========================================

    @Slot()
    def _start_monitoring(self):
        """Start the background monitoring thread."""
        if self._is_monitoring:
            print("[App] Monitor already running - ignoring duplicate start.")
            return

        # Create a fresh thread each time (QThread cannot be restarted)
        self._monitor = MonitorThread(self)

        # Gather settings
        enabled_platforms = self._dashboard.get_enabled_platforms()
        check_interval = self._settings.check_interval
        notifications_enabled = self._settings.notifications_enabled
        keyword_filter = self._settings.keyword_list

        self._monitor.configure(
            enabled_platforms=enabled_platforms,
            check_interval=check_interval,
            notifications_enabled=notifications_enabled,
            keyword_filter=keyword_filter,
        )

        # Connect thread signals to GUI slots
        self._monitor.new_project.connect(self._on_new_project)
        self._monitor.status_changed.connect(self._on_status_changed)
        self._monitor.error_occurred.connect(self._on_error)
        self._monitor.cycle_complete.connect(self._on_cycle_complete)
        self._monitor.finished.connect(self._on_monitor_finished)

        self._monitor.start()
        self._is_monitoring = True

        print("=" * 50)
        print(f"[App] Monitoring STARTED at {datetime.now().strftime('%H:%M:%S')}")
        print(f"[App] Platforms: {enabled_platforms}")
        print(f"[App] Interval: {check_interval}s")
        print("=" * 50)

    @Slot()
    def _stop_monitoring(self):
        """Stop the background monitoring thread gracefully."""
        if not self._is_monitoring or not self._monitor:
            print("[App] No active monitor to stop.")
            return

        print(f"[App] Stopping monitor at {datetime.now().strftime('%H:%M:%S')}...")
        self._monitor.stop()
        # Don't block the GUI — the finished signal will handle cleanup

    @Slot()
    def _on_monitor_finished(self):
        """Called when the monitor thread finishes execution."""
        self._is_monitoring = False
        self._dashboard.set_offline()
        print("[App] Monitor thread finished and cleaned up.")

    # ==========================================
    # MONITOR SIGNAL HANDLERS
    # ==========================================

    @Slot(dict)
    def _on_new_project(self, project: dict):
        """Handle a new project found by the monitor."""
        site = project.get("site", "?")
        title = project.get("title", "?")
        print(f"[Feed] NEW from {site}: {title}")
        self._dashboard.add_project(project)

        # Show tray notification balloon
        if self._tray and self._tray.isVisible():
            self._tray.showMessage(
                f"{site} - New Project",
                title,
                QSystemTrayIcon.Information,
                3000
            )

    @Slot(str)
    def _on_status_changed(self, status: str):
        """Handle monitoring status changes."""
        print(f"[App] Status changed: {status}")

    @Slot(str)
    def _on_error(self, error_msg: str):
        """Handle scraper errors."""
        print(f"[Error] {error_msg}")

    @Slot(int)
    def _on_cycle_complete(self, total_count: int):
        """Handle completion of a scrape cycle."""
        self._dashboard.update_total_count(total_count)

    # ==========================================
    # PLATFORM / SETTINGS UPDATES
    # ==========================================

    @Slot(str, bool)
    def _on_platform_toggled(self, key: str, enabled: bool):
        """Update monitor when a platform is toggled."""
        status = "ENABLED" if enabled else "DISABLED"
        print(f"[App] Platform {key} {status}")

        if self._is_monitoring and self._monitor:
            platforms = self._dashboard.get_enabled_platforms()
            self._monitor.update_platforms(platforms)

    @Slot()
    def _on_settings_changed(self):
        """Apply settings changes to the running monitor."""
        print("[App] Settings updated.")

        if self._is_monitoring and self._monitor:
            self._monitor.update_interval(self._settings.check_interval)
            self._monitor.update_notifications(
                notifications=self._settings.notifications_enabled,
            )

    # ==========================================
    # SYSTEM TRAY
    # ==========================================

    def _setup_tray(self):
        """Create system tray icon with context menu."""
        if not os.path.exists(APP_ICON):
            return

        self._tray = QSystemTrayIcon(QIcon(APP_ICON), self)
        self._tray.setToolTip("Freelance Tracker PRO")

        tray_menu = QMenu()
        tray_menu.setStyleSheet(f"""
            QMenu {{
                background-color: {Colors.BG_SECONDARY};
                border: 1px solid {Colors.BORDER_DEFAULT};
                border-radius: 8px; padding: 4px;
            }}
            QMenu::item {{
                padding: 8px 24px; border-radius: 4px;
                color: {Colors.TEXT_PRIMARY};
            }}
            QMenu::item:selected {{
                background-color: {Colors.BG_HOVER};
            }}
        """)

        show_action = QAction("Show Window", self)
        show_action.triggered.connect(self._tray_show)

        quit_action = QAction("Quit", self)
        quit_action.triggered.connect(self._tray_quit)

        tray_menu.addAction(show_action)
        tray_menu.addSeparator()
        tray_menu.addAction(quit_action)

        self._tray.setContextMenu(tray_menu)
        self._tray.activated.connect(self._on_tray_activated)
        self._tray.show()

    def _tray_show(self):
        self.showNormal()
        self.activateWindow()
        self.raise_()

    def _tray_quit(self):
        self._shutdown()
        QApplication.quit()

    def _on_tray_activated(self, reason):
        if reason == QSystemTrayIcon.DoubleClick:
            self._tray_show()

    # ==========================================
    # APPLICATION LIFECYCLE
    # ==========================================

    def _shutdown(self):
        """Clean shutdown: stop monitor, save settings, hide tray."""
        print("[App] Shutting down...")

        # Stop monitoring thread
        if self._is_monitoring and self._monitor:
            self._monitor.stop()
            if not self._monitor.wait(3000):
                print("[App] Warning: Monitor thread did not stop within 3s.")
                self._monitor.terminate()
                self._monitor.wait(1000)

        # Hide tray icon
        if self._tray:
            self._tray.hide()

        # Save settings on exit
        self._settings.save()
        print("[App] Settings saved. Goodbye!")

    def closeEvent(self, event):
        """Handle window close — shutdown gracefully."""
        self._shutdown()
        event.accept()
