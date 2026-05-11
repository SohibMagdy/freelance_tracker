"""
settings.py — Settings page with configurable options.
Includes check interval slider, notification toggles, keyword filter,
and start-with-Windows toggle.
"""

import winreg
import sys
import os

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QSlider, QLineEdit, QFrame
)
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QFont

from src.ui.styles.theme import Colors, FONT_FAMILY
from src.ui.widgets.animated_toggle import AnimatedToggle


class SettingRow(QWidget):
    """A single setting row with label, description, and control widget."""

    def __init__(self, title: str, description: str, parent=None):
        super().__init__(parent)
        self._layout = QHBoxLayout(self)
        self._layout.setContentsMargins(0, 8, 0, 8)
        self._layout.setSpacing(16)

        # Text side
        text_layout = QVBoxLayout()
        text_layout.setSpacing(2)

        title_label = QLabel(title)
        title_label.setFont(QFont(
            FONT_FAMILY.split(",")[0].strip("' "), 13, QFont.DemiBold
        ))
        title_label.setStyleSheet(f"color: {Colors.TEXT_PRIMARY};")

        desc_label = QLabel(description)
        desc_label.setFont(QFont(
            FONT_FAMILY.split(",")[0].strip("' "), 11
        ))
        desc_label.setStyleSheet(f"color: {Colors.TEXT_MUTED};")
        desc_label.setWordWrap(True)

        text_layout.addWidget(title_label)
        text_layout.addWidget(desc_label)

        self._layout.addLayout(text_layout, stretch=1)

    def add_control(self, widget: QWidget):
        """Add a control widget to the right side."""
        self._layout.addWidget(widget, alignment=Qt.AlignRight | Qt.AlignVCenter)


class Divider(QFrame):
    """Subtle horizontal divider line."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFrameShape(QFrame.HLine)
        self.setFixedHeight(1)
        self.setStyleSheet(f"background: {Colors.BORDER_SUBTLE}; border: none;")


class SettingsPage(QWidget):
    """
    Application settings page with all configurable options.
    Auto-saves changes to the settings manager.
    """

    settings_changed = Signal()

    def __init__(self, settings, parent=None):
        super().__init__(parent)
        self._settings = settings
        self._build_ui()

    def _build_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(28, 20, 28, 20)
        layout.setSpacing(8)

        # Header
        header = QLabel("Settings")
        header.setFont(QFont(
            FONT_FAMILY.split(",")[0].strip("' "), 22, QFont.Bold
        ))
        header.setStyleSheet(f"color: {Colors.TEXT_PRIMARY};")
        layout.addWidget(header)

        subtitle = QLabel("Configure monitoring behavior and preferences")
        subtitle.setFont(QFont(
            FONT_FAMILY.split(",")[0].strip("' "), 12
        ))
        subtitle.setStyleSheet(f"color: {Colors.TEXT_MUTED}; margin-bottom: 12px;")
        layout.addWidget(subtitle)

        # ======== MONITORING SECTION ========
        section_monitor = QLabel("MONITORING")
        section_monitor.setFont(QFont(
            FONT_FAMILY.split(",")[0].strip("' "), 10, QFont.Bold
        ))
        section_monitor.setStyleSheet(
            f"color: {Colors.TEXT_MUTED}; letter-spacing: 2px; margin-top: 12px;"
        )
        layout.addWidget(section_monitor)
        layout.addWidget(Divider())

        # Check interval slider
        interval_row = SettingRow(
            "Check Interval",
            "How often to check for new projects (seconds)"
        )

        interval_container = QVBoxLayout()
        interval_container.setSpacing(4)

        self._interval_slider = QSlider(Qt.Horizontal)
        self._interval_slider.setRange(10, 120)
        self._interval_slider.setValue(self._settings.check_interval)
        self._interval_slider.setFixedWidth(200)
        self._interval_slider.setTickPosition(QSlider.NoTicks)

        self._interval_value = QLabel(f"{self._settings.check_interval}s")
        self._interval_value.setFont(QFont(
            FONT_FAMILY.split(",")[0].strip("' "), 12, QFont.Bold
        ))
        self._interval_value.setStyleSheet(f"color: {Colors.CYAN};")
        self._interval_value.setAlignment(Qt.AlignCenter)
        self._interval_value.setFixedWidth(200)

        self._interval_slider.valueChanged.connect(self._on_interval_changed)

        interval_container.addWidget(self._interval_slider)
        interval_container.addWidget(self._interval_value)

        interval_widget = QWidget()
        interval_widget.setLayout(interval_container)
        interval_row.add_control(interval_widget)
        layout.addWidget(interval_row)

        # ======== NOTIFICATIONS SECTION ========
        section_notif = QLabel("NOTIFICATIONS")
        section_notif.setFont(QFont(
            FONT_FAMILY.split(",")[0].strip("' "), 10, QFont.Bold
        ))
        section_notif.setStyleSheet(
            f"color: {Colors.TEXT_MUTED}; letter-spacing: 2px; margin-top: 16px;"
        )
        layout.addWidget(section_notif)
        layout.addWidget(Divider())

        # Desktop notifications toggle
        notif_row = SettingRow(
            "Desktop Notifications",
            "Show Windows toast notifications for new projects"
        )
        self._notif_toggle = AnimatedToggle(
            checked=self._settings.notifications_enabled
        )
        self._notif_toggle.toggled.connect(
            lambda v: self._save("notifications_enabled", v)
        )
        notif_row.add_control(self._notif_toggle)
        layout.addWidget(notif_row)



        # ======== FILTER SECTION ========
        section_filter = QLabel("FILTERS")
        section_filter.setFont(QFont(
            FONT_FAMILY.split(",")[0].strip("' "), 10, QFont.Bold
        ))
        section_filter.setStyleSheet(
            f"color: {Colors.TEXT_MUTED}; letter-spacing: 2px; margin-top: 16px;"
        )
        layout.addWidget(section_filter)
        layout.addWidget(Divider())

        # Keyword filter
        keyword_row = SettingRow(
            "Keyword Filter",
            "Only show projects matching these keywords (comma-separated, leave empty for all)"
        )
        self._keyword_input = QLineEdit()
        self._keyword_input.setPlaceholderText("e.g. python, react, design")
        self._keyword_input.setText(self._settings.keyword_filter)
        self._keyword_input.setFixedWidth(260)
        self._keyword_input.editingFinished.connect(self._on_keyword_changed)
        keyword_row.add_control(self._keyword_input)
        layout.addWidget(keyword_row)

        # ======== SYSTEM SECTION ========
        section_sys = QLabel("SYSTEM")
        section_sys.setFont(QFont(
            FONT_FAMILY.split(",")[0].strip("' "), 10, QFont.Bold
        ))
        section_sys.setStyleSheet(
            f"color: {Colors.TEXT_MUTED}; letter-spacing: 2px; margin-top: 16px;"
        )
        layout.addWidget(section_sys)
        layout.addWidget(Divider())

        # Start with Windows
        startup_row = SettingRow(
            "Start with Windows",
            "Automatically launch Freelance Tracker when Windows starts"
        )
        self._startup_toggle = AnimatedToggle(
            checked=self._settings.get("start_with_windows", False)
        )
        self._startup_toggle.toggled.connect(self._on_startup_toggle)
        startup_row.add_control(self._startup_toggle)
        layout.addWidget(startup_row)

        # Start minimized
        minimized_row = SettingRow(
            "Start Minimized",
            "Launch minimized to system tray"
        )
        self._minimized_toggle = AnimatedToggle(
            checked=self._settings.get("start_minimized", False)
        )
        self._minimized_toggle.toggled.connect(
            lambda v: self._save("start_minimized", v)
        )
        minimized_row.add_control(self._minimized_toggle)
        layout.addWidget(minimized_row)

        layout.addStretch()

    # ==========================================
    # HANDLERS
    # ==========================================

    def _on_interval_changed(self, value: int):
        self._interval_value.setText(f"{value}s")
        self._settings.check_interval = value
        self.settings_changed.emit()

    def _on_keyword_changed(self):
        self._settings.set("keyword_filter", self._keyword_input.text().strip())
        self.settings_changed.emit()

    def _on_startup_toggle(self, enabled: bool):
        self._save("start_with_windows", enabled)
        self._set_windows_startup(enabled)

    def _save(self, key: str, value):
        self._settings.set(key, value)
        self.settings_changed.emit()

    # ==========================================
    # WINDOWS STARTUP REGISTRY
    # ==========================================

    def _set_windows_startup(self, enable: bool):
        """Add or remove the app from Windows startup via registry."""
        key_path = r"Software\Microsoft\Windows\CurrentVersion\Run"
        app_name = "FreelanceTracker"

        try:
            key = winreg.OpenKey(
                winreg.HKEY_CURRENT_USER, key_path,
                0, winreg.KEY_SET_VALUE
            )

            if enable:
                exe_path = sys.executable
                script_path = os.path.abspath(
                    os.path.join(os.path.dirname(__file__), "..", "..", "..", "Freelance Tracker.py")
                )
                winreg.SetValueEx(
                    key, app_name, 0, winreg.REG_SZ,
                    f'"{exe_path}" "{script_path}"'
                )
            else:
                try:
                    winreg.DeleteValue(key, app_name)
                except FileNotFoundError:
                    pass

            winreg.CloseKey(key)

        except Exception as e:
            print(f"[Settings] Failed to modify startup: {e}")
