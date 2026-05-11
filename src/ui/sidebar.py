"""
sidebar.py — Navigation sidebar with icon buttons and active indicator.
Features glassmorphic styling and animated active state.
"""

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QPushButton, QLabel
)
from PySide6.QtCore import Qt, Signal, QSize
from PySide6.QtGui import QFont, QColor

from src.ui.styles.theme import Colors, FONT_FAMILY


class SidebarButton(QPushButton):
    """Navigation button with icon and active state indicator."""

    def __init__(self, icon_char: str, label: str, parent=None):
        super().__init__(parent)
        self._icon_char = icon_char
        self._label = label
        self._active = False

        self.setFixedSize(56, 52)
        self.setCursor(Qt.PointingHandCursor)
        self.setToolTip(label)
        self.setText(icon_char)
        self.setFont(QFont(FONT_FAMILY.split(",")[0].strip("' "), 18))
        self._apply_style()

    @property
    def active(self) -> bool:
        return self._active

    @active.setter
    def active(self, value: bool) -> None:
        self._active = value
        self._apply_style()

    def _apply_style(self):
        if self._active:
            self.setStyleSheet(f"""
                QPushButton {{
                    background: rgba(0, 212, 255, 0.08);
                    color: {Colors.CYAN};
                    border: none;
                    border-left: 3px solid {Colors.CYAN};
                    border-radius: 0px;
                    padding-left: 0px;
                    font-size: 18px;
                }}
            """)
        else:
            self.setStyleSheet(f"""
                QPushButton {{
                    background: transparent;
                    color: {Colors.TEXT_MUTED};
                    border: none;
                    border-radius: 8px;
                    font-size: 18px;
                }}
                QPushButton:hover {{
                    background: {Colors.BG_HOVER};
                    color: {Colors.TEXT_SECONDARY};
                }}
            """)


class Sidebar(QWidget):
    """
    Vertical icon navigation sidebar.
    Emits page_changed(int) when a navigation item is clicked.
    """

    page_changed = Signal(int)

    # Page indices
    PAGE_DASHBOARD = 0
    PAGE_SETTINGS = 1

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedWidth(60)

        self.setStyleSheet(f"""
            Sidebar {{
                background-color: {Colors.BG_DARKEST};
                border-right: 1px solid {Colors.BORDER_SUBTLE};
            }}
        """)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(2, 12, 2, 12)
        layout.setSpacing(4)
        layout.setAlignment(Qt.AlignTop)

        # Navigation buttons
        self._buttons = []

        btn_dashboard = SidebarButton("🏠", "Dashboard")
        btn_settings = SidebarButton("⚙", "Settings")

        self._buttons = [btn_dashboard, btn_settings]

        for i, btn in enumerate(self._buttons):
            btn.clicked.connect(lambda checked, idx=i: self._on_click(idx))
            layout.addWidget(btn, alignment=Qt.AlignCenter)

        layout.addStretch()

        # Version label at bottom
        version = QLabel("v2.0")
        version.setFont(QFont(FONT_FAMILY.split(",")[0].strip("' "), 9))
        version.setStyleSheet(f"color: {Colors.TEXT_MUTED};")
        version.setAlignment(Qt.AlignCenter)
        layout.addWidget(version)

        # Set initial active
        self._set_active(0)

    def _on_click(self, index: int):
        self._set_active(index)
        self.page_changed.emit(index)

    def _set_active(self, index: int):
        for i, btn in enumerate(self._buttons):
            btn.active = (i == index)
