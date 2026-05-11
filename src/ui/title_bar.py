"""
title_bar.py — Custom frameless title bar with app icon, name,
and window control buttons (minimize, maximize, close).
"""

import os
from PySide6.QtWidgets import (
    QWidget, QHBoxLayout, QLabel, QPushButton
)
from PySide6.QtCore import Qt, QSize, Signal
from PySide6.QtGui import QFont, QPixmap, QColor, QIcon

from src.ui.styles.theme import Colors, FONT_FAMILY
from src.utils.resources import APP_ICON


class TitleBarButton(QPushButton):
    """Window control button with hover effects."""

    def __init__(self, text: str, hover_color: str, parent=None):
        super().__init__(text, parent)
        self._hover_color = hover_color
        self.setFixedSize(36, 28)
        self.setCursor(Qt.PointingHandCursor)
        self.setStyleSheet(f"""
            QPushButton {{
                background: transparent;
                color: {Colors.TEXT_SECONDARY};
                border: none;
                border-radius: 6px;
                font-size: 13px;
                font-weight: bold;
            }}
            QPushButton:hover {{
                background: {hover_color};
                color: {Colors.TEXT_PRIMARY};
            }}
        """)


class TitleBar(QWidget):
    """
    Custom title bar for a frameless window.
    Provides minimize, maximize, and close buttons with drag-to-move.
    """

    minimize_clicked = Signal()
    maximize_clicked = Signal()
    close_clicked = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedHeight(42)
        self._drag_pos = None

        self.setStyleSheet(f"""
            TitleBar {{
                background-color: {Colors.BG_DARKEST};
                border-bottom: 1px solid {Colors.BORDER_SUBTLE};
            }}
        """)

        layout = QHBoxLayout(self)
        layout.setContentsMargins(12, 0, 8, 0)
        layout.setSpacing(10)

        # App icon (from .ico file)
        if os.path.exists(APP_ICON):
            icon_label = QLabel()
            icon = QIcon(APP_ICON)
            pixmap = icon.pixmap(22, 22)
            icon_label.setPixmap(pixmap)
            layout.addWidget(icon_label)

        # App name
        title = QLabel("Freelance Tracker")
        title.setFont(QFont(
            FONT_FAMILY.split(",")[0].strip("' "), 12, QFont.Bold
        ))
        title.setStyleSheet(
            f"color: {Colors.TEXT_PRIMARY}; letter-spacing: 0.5px;"
        )
        layout.addWidget(title)

        # Subtitle
        subtitle = QLabel("PRO")
        subtitle.setFont(QFont(
            FONT_FAMILY.split(",")[0].strip("' "), 8, QFont.Bold
        ))
        subtitle.setStyleSheet(
            f"color: {Colors.CYAN}; "
            f"background: rgba(0,212,255,0.1); "
            f"padding: 2px 6px; border-radius: 4px;"
        )
        layout.addWidget(subtitle)

        layout.addStretch()

        # Window controls
        self._btn_min = TitleBarButton("─", Colors.BG_HOVER)
        self._btn_max = TitleBarButton("□", Colors.BG_HOVER)
        self._btn_close = TitleBarButton("✕", "#dc2626")

        self._btn_min.clicked.connect(self.minimize_clicked.emit)
        self._btn_max.clicked.connect(self.maximize_clicked.emit)
        self._btn_close.clicked.connect(self.close_clicked.emit)

        layout.addWidget(self._btn_min)
        layout.addWidget(self._btn_max)
        layout.addWidget(self._btn_close)

    # ==========================================
    # DRAG TO MOVE
    # ==========================================

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self._drag_pos = event.globalPosition().toPoint()
        super().mousePressEvent(event)

    def mouseMoveEvent(self, event):
        if self._drag_pos and event.buttons() & Qt.LeftButton:
            window = self.window()
            if window:
                delta = event.globalPosition().toPoint() - self._drag_pos
                window.move(window.pos() + delta)
                self._drag_pos = event.globalPosition().toPoint()
        super().mouseMoveEvent(event)

    def mouseReleaseEvent(self, event):
        self._drag_pos = None
        super().mouseReleaseEvent(event)

    def mouseDoubleClickEvent(self, event):
        self.maximize_clicked.emit()
        super().mouseDoubleClickEvent(event)
