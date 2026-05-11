"""
project_card.py — Modern project feed card with platform color-coded border,
clickable title, and fade-in animation.
"""

import webbrowser
from datetime import datetime

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QGraphicsDropShadowEffect, QGraphicsOpacityEffect
)
from PySide6.QtCore import (
    Qt, QPropertyAnimation, QEasingCurve, QTimer
)
from PySide6.QtGui import QColor, QFont, QCursor

from src.ui.styles.theme import Colors, PLATFORM_COLORS, FONT_FAMILY


class ProjectCard(QWidget):
    """
    Stylish project card for the live monitoring feed.
    Shows platform badge, title, description, and timestamp.
    Clicking opens the project link.
    """

    def __init__(self, project: dict, parent=None):
        super().__init__(parent)
        self._project = project
        self._link = project.get("link", "")
        self._site = project.get("site", "Unknown")
        self._accent = PLATFORM_COLORS.get(self._site, Colors.CYAN)

        self.setCursor(Qt.PointingHandCursor)
        self.setMinimumHeight(80)
        self.setMaximumHeight(120)

        # Fade-in animation
        self._opacity_effect = QGraphicsOpacityEffect(self)
        self._opacity_effect.setOpacity(0.0)
        self.setGraphicsEffect(self._opacity_effect)

        self._fade_anim = QPropertyAnimation(self._opacity_effect, b"opacity", self)
        self._fade_anim.setDuration(400)
        self._fade_anim.setStartValue(0.0)
        self._fade_anim.setEndValue(1.0)
        self._fade_anim.setEasingCurve(QEasingCurve.OutCubic)

        self._build_ui()
        self._apply_style(hovered=False)

        # Start fade-in after a brief delay
        QTimer.singleShot(50, self._fade_anim.start)

    def _build_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 12, 16, 12)
        layout.setSpacing(6)

        # Top row: platform badge + timestamp
        top = QHBoxLayout()
        top.setSpacing(8)

        badge = QLabel(self._site)
        badge.setFont(QFont(FONT_FAMILY.split(",")[0].strip("' "), 10, QFont.Bold))
        ac = QColor(self._accent)
        badge.setStyleSheet(
            f"color: {self._accent}; "
            f"background: rgba({ac.red()},{ac.green()},{ac.blue()},0.12); "
            f"padding: 3px 10px; border-radius: 6px;"
        )

        ts = self._project.get("timestamp", datetime.now().strftime("%H:%M:%S"))
        time_label = QLabel(ts)
        time_label.setFont(QFont(FONT_FAMILY.split(",")[0].strip("' "), 10))
        time_label.setStyleSheet(f"color: {Colors.TEXT_MUTED};")

        top.addWidget(badge)
        top.addStretch()
        top.addWidget(time_label)
        layout.addLayout(top)

        # Title
        title = self._project.get("title", "Untitled Project")
        title_label = QLabel(title)
        title_label.setFont(QFont(FONT_FAMILY.split(",")[0].strip("' "), 13, QFont.DemiBold))
        title_label.setStyleSheet(f"color: {Colors.TEXT_PRIMARY};")
        title_label.setWordWrap(True)
        title_label.setMaximumHeight(40)
        layout.addWidget(title_label)

        # Description (truncated)
        desc = self._project.get("description", "")
        if desc:
            desc_label = QLabel(desc[:120] + ("..." if len(desc) > 120 else ""))
            desc_label.setFont(QFont(FONT_FAMILY.split(",")[0].strip("' "), 11))
            desc_label.setStyleSheet(f"color: {Colors.TEXT_SECONDARY};")
            desc_label.setWordWrap(True)
            desc_label.setMaximumHeight(32)
            layout.addWidget(desc_label)

    def _apply_style(self, hovered=False):
        ac = QColor(self._accent)
        border_alpha = 0.25 if hovered else 0.1
        bg = Colors.BG_HOVER if hovered else Colors.BG_CARD
        self.setStyleSheet(
            f"ProjectCard {{"
            f"  background-color: {bg};"
            f"  border-left: 3px solid {self._accent};"
            f"  border-top: 1px solid rgba({ac.red()},{ac.green()},{ac.blue()},{border_alpha});"
            f"  border-right: 1px solid rgba({ac.red()},{ac.green()},{ac.blue()},{border_alpha});"
            f"  border-bottom: 1px solid rgba({ac.red()},{ac.green()},{ac.blue()},{border_alpha});"
            f"  border-radius: 12px;"
            f"}}"
        )

    def enterEvent(self, event):
        self._apply_style(hovered=True)
        super().enterEvent(event)

    def leaveEvent(self, event):
        self._apply_style(hovered=False)
        super().leaveEvent(event)

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton and self._link:
            webbrowser.open(self._link)
        super().mousePressEvent(event)
