"""
platform_card.py — Interactive platform card with toggle, logo, and glow accent.
Displays a freelance platform's logo, name, and on/off toggle.
"""

import os

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QGraphicsDropShadowEffect
)
from PySide6.QtCore import Qt, Signal, QSize
from PySide6.QtGui import QColor, QFont, QPixmap, QIcon

from src.ui.styles.theme import Colors, FONT_FAMILY
from src.ui.widgets.animated_toggle import AnimatedToggle


# Platform accent colors
PLATFORM_ACCENTS = {
    "mostaql":    Colors.CYAN,
    "nafezly":    Colors.PURPLE,
    "truelancer": Colors.BLUE,
}


class PlatformCard(QWidget):
    """
    Interactive card showing a platform's logo, name, and enable/disable toggle.
    Emits platform_toggled(key, enabled) when the toggle changes.
    """

    platform_toggled = Signal(str, bool)

    def __init__(
        self,
        key: str,
        name: str,
        logo_path: str = None,
        enabled: bool = True,
        parent=None,
    ):
        super().__init__(parent)
        self._key = key
        self._name = name
        self._accent = PLATFORM_ACCENTS.get(key, Colors.CYAN)
        self._enabled = enabled

        self.setFixedSize(180, 110)
        self._build_ui(logo_path)
        self._apply_style(hovered=False)

    def _build_ui(self, logo_path: str):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(14, 12, 14, 12)
        layout.setSpacing(8)

        # Top row: Logo + Name
        top = QHBoxLayout()
        top.setSpacing(10)

        if logo_path and os.path.exists(logo_path):
            logo_label = QLabel()
            icon = QIcon(logo_path)
            pixmap = icon.pixmap(28, 28)
            logo_label.setPixmap(pixmap)
            top.addWidget(logo_label)
        else:
            # Fallback icon character
            icon_label = QLabel("🌐")
            icon_label.setStyleSheet("font-size: 22px;")
            top.addWidget(icon_label)

        name_label = QLabel(self._name)
        name_label.setFont(QFont(
            FONT_FAMILY.split(",")[0].strip("' "), 13, QFont.DemiBold
        ))
        name_label.setStyleSheet(f"color: {Colors.TEXT_PRIMARY};")
        top.addWidget(name_label)
        top.addStretch()
        layout.addLayout(top)

        layout.addStretch()

        # Bottom row: status + toggle
        bottom = QHBoxLayout()
        bottom.setSpacing(8)

        self._status_label = QLabel("Enabled" if self._enabled else "Disabled")
        self._status_label.setFont(QFont(
            FONT_FAMILY.split(",")[0].strip("' "), 10
        ))
        self._status_label.setStyleSheet(
            f"color: {Colors.GREEN if self._enabled else Colors.TEXT_MUTED};"
        )
        bottom.addWidget(self._status_label)
        bottom.addStretch()

        self._toggle = AnimatedToggle(checked=self._enabled)
        self._toggle.toggled.connect(self._on_toggle)
        bottom.addWidget(self._toggle)

        layout.addLayout(bottom)

        # Glow shadow
        shadow = QGraphicsDropShadowEffect(self)
        shadow.setBlurRadius(0)
        shadow.setOffset(0, 0)
        shadow.setColor(QColor(self._accent))
        self.setGraphicsEffect(shadow)
        self._shadow = shadow

    def _on_toggle(self, enabled: bool):
        self._enabled = enabled
        self._status_label.setText("Enabled" if enabled else "Disabled")
        self._status_label.setStyleSheet(
            f"color: {Colors.GREEN if enabled else Colors.TEXT_MUTED};"
        )
        self.platform_toggled.emit(self._key, enabled)

    def _apply_style(self, hovered=False):
        ac = QColor(self._accent)
        border_alpha = 0.2 if hovered else 0.08
        bg = Colors.BG_HOVER if hovered else Colors.BG_CARD
        self.setStyleSheet(
            f"PlatformCard {{"
            f"  background-color: {bg};"
            f"  border: 1px solid rgba({ac.red()},{ac.green()},{ac.blue()},{border_alpha});"
            f"  border-radius: 14px;"
            f"}}"
        )

    def enterEvent(self, event):
        self._apply_style(hovered=True)
        self._shadow.setBlurRadius(20)
        super().enterEvent(event)

    def leaveEvent(self, event):
        self._apply_style(hovered=False)
        self._shadow.setBlurRadius(0)
        super().leaveEvent(event)
