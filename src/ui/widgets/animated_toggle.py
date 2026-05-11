"""
animated_toggle.py — iOS-style animated toggle switch widget.
Features smooth knob slide animation and color transitions.
"""

from PySide6.QtWidgets import QWidget
from PySide6.QtCore import (
    Qt, QPropertyAnimation, QEasingCurve, Property, QRectF, Signal
)
from PySide6.QtGui import QPainter, QColor, QBrush, QPen

from src.ui.styles.theme import Colors, ANIM_NORMAL


class AnimatedToggle(QWidget):
    """
    Custom toggle switch with smooth animation.
    Emits toggled(bool) when the state changes.
    """

    toggled = Signal(bool)

    def __init__(self, parent=None, checked: bool = False):
        super().__init__(parent)
        self.setFixedSize(48, 26)
        self.setCursor(Qt.PointingHandCursor)

        self._checked = checked
        self._knob_x = 24.0 if checked else 4.0
        self._bg_opacity = 1.0 if checked else 0.0

        # Animation for knob position
        self._knob_anim = QPropertyAnimation(self, b"knob_position", self)
        self._knob_anim.setDuration(ANIM_NORMAL)
        self._knob_anim.setEasingCurve(QEasingCurve.InOutCubic)

        # Animation for background color
        self._bg_anim = QPropertyAnimation(self, b"bg_opacity", self)
        self._bg_anim.setDuration(ANIM_NORMAL)
        self._bg_anim.setEasingCurve(QEasingCurve.InOutCubic)

    # ==========================================
    # PROPERTIES FOR ANIMATION
    # ==========================================

    def _get_knob_position(self) -> float:
        return self._knob_x

    def _set_knob_position(self, pos: float) -> None:
        self._knob_x = pos
        self.update()

    knob_position = Property(
        float, _get_knob_position, _set_knob_position
    )

    def _get_bg_opacity(self) -> float:
        return self._bg_opacity

    def _set_bg_opacity(self, val: float) -> None:
        self._bg_opacity = val
        self.update()

    bg_opacity = Property(
        float, _get_bg_opacity, _set_bg_opacity
    )

    # ==========================================
    # STATE
    # ==========================================

    @property
    def checked(self) -> bool:
        return self._checked

    @checked.setter
    def checked(self, value: bool) -> None:
        if self._checked != value:
            self._checked = value
            self._animate_to_state(value)
            self.toggled.emit(value)

    def setChecked(self, value: bool) -> None:
        """Set state without emitting signal (for initialization)."""
        self._checked = value
        self._knob_x = 24.0 if value else 4.0
        self._bg_opacity = 1.0 if value else 0.0
        self.update()

    def _animate_to_state(self, checked: bool) -> None:
        """Animate knob and background to the new state."""
        # Knob slide
        self._knob_anim.stop()
        self._knob_anim.setStartValue(self._knob_x)
        self._knob_anim.setEndValue(24.0 if checked else 4.0)
        self._knob_anim.start()

        # Background fade
        self._bg_anim.stop()
        self._bg_anim.setStartValue(self._bg_opacity)
        self._bg_anim.setEndValue(1.0 if checked else 0.0)
        self._bg_anim.start()

    # ==========================================
    # EVENTS
    # ==========================================

    def mousePressEvent(self, event) -> None:
        if event.button() == Qt.LeftButton:
            self.checked = not self._checked

    def paintEvent(self, event) -> None:
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)

        w, h = self.width(), self.height()
        radius = h / 2

        # Track background (inactive → active gradient)
        inactive_color = QColor(Colors.BG_ELEVATED)
        active_color = QColor(Colors.CYAN)

        # Interpolate between inactive and active colors
        r = int(inactive_color.red()   + (active_color.red()   - inactive_color.red())   * self._bg_opacity)
        g = int(inactive_color.green() + (active_color.green() - inactive_color.green()) * self._bg_opacity)
        b = int(inactive_color.blue()  + (active_color.blue()  - inactive_color.blue())  * self._bg_opacity)
        track_color = QColor(r, g, b)

        painter.setPen(Qt.NoPen)
        painter.setBrush(QBrush(track_color))
        painter.drawRoundedRect(QRectF(0, 0, w, h), radius, radius)

        # Subtle border
        border_color = QColor(Colors.CYAN)
        border_color.setAlphaF(0.2 * self._bg_opacity)
        painter.setPen(QPen(border_color, 1))
        painter.setBrush(Qt.NoBrush)
        painter.drawRoundedRect(QRectF(0.5, 0.5, w - 1, h - 1), radius, radius)

        # Knob
        knob_size = h - 8
        knob_y = 4.0
        painter.setPen(Qt.NoPen)

        # Knob shadow
        shadow_color = QColor(0, 0, 0, 40)
        painter.setBrush(QBrush(shadow_color))
        painter.drawEllipse(QRectF(self._knob_x, knob_y + 1, knob_size, knob_size))

        # Knob body
        painter.setBrush(QBrush(QColor("#ffffff")))
        painter.drawEllipse(QRectF(self._knob_x, knob_y, knob_size, knob_size))

        painter.end()
