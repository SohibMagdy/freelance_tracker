"""
status_indicator.py — Animated pulsing status dot with ONLINE/OFFLINE label.
Features a smooth breathing glow animation.
"""

from PySide6.QtWidgets import QWidget, QHBoxLayout, QLabel
from PySide6.QtCore import (
    Qt, QPropertyAnimation, QEasingCurve, Property, QRectF, QTimer
)
from PySide6.QtGui import QPainter, QColor, QBrush, QPen, QFont, QRadialGradient

from src.ui.styles.theme import Colors, FONT_FAMILY


class StatusDot(QWidget):
    """Animated pulsing dot that glows when online."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedSize(24, 24)

        self._is_online = False
        self._pulse_value = 0.0

        # Pulse animation (breathing effect)
        self._pulse_anim = QPropertyAnimation(self, b"pulse", self)
        self._pulse_anim.setDuration(2000)
        self._pulse_anim.setStartValue(0.0)
        self._pulse_anim.setEndValue(1.0)
        self._pulse_anim.setEasingCurve(QEasingCurve.InOutSine)
        self._pulse_anim.setLoopCount(-1)  # infinite

    # ==========================================
    # PULSE PROPERTY
    # ==========================================

    def _get_pulse(self) -> float:
        return self._pulse_value

    def _set_pulse(self, val: float) -> None:
        self._pulse_value = val
        self.update()

    pulse = Property(float, _get_pulse, _set_pulse)

    # ==========================================
    # STATE
    # ==========================================

    def set_online(self, online: bool) -> None:
        """Set the online/offline state."""
        self._is_online = online
        if online:
            self._pulse_anim.start()
        else:
            self._pulse_anim.stop()
            self._pulse_value = 0.0
        self.update()

    # ==========================================
    # PAINT
    # ==========================================

    def paintEvent(self, event) -> None:
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)

        center_x = self.width() / 2
        center_y = self.height() / 2

        if self._is_online:
            color = QColor(Colors.GREEN)

            # Outer glow (pulsing)
            glow_radius = 10 + (self._pulse_value * 4)
            glow_color = QColor(Colors.GREEN)
            glow_color.setAlphaF(0.15 + (0.15 * self._pulse_value))

            gradient = QRadialGradient(center_x, center_y, glow_radius)
            gradient.setColorAt(0, glow_color)
            gradient.setColorAt(1, QColor(0, 0, 0, 0))

            painter.setPen(Qt.NoPen)
            painter.setBrush(QBrush(gradient))
            painter.drawEllipse(QRectF(
                center_x - glow_radius,
                center_y - glow_radius,
                glow_radius * 2,
                glow_radius * 2,
            ))

            # Inner dot
            dot_radius = 5
            painter.setBrush(QBrush(color))
            painter.drawEllipse(QRectF(
                center_x - dot_radius,
                center_y - dot_radius,
                dot_radius * 2,
                dot_radius * 2,
            ))

            # Bright center
            painter.setBrush(QBrush(QColor(255, 255, 255, 120)))
            painter.drawEllipse(QRectF(
                center_x - 2, center_y - 2, 4, 4
            ))

        else:
            # Offline — dim red dot
            color = QColor(Colors.RED)
            color.setAlphaF(0.5)

            dot_radius = 5
            painter.setPen(Qt.NoPen)
            painter.setBrush(QBrush(color))
            painter.drawEllipse(QRectF(
                center_x - dot_radius,
                center_y - dot_radius,
                dot_radius * 2,
                dot_radius * 2,
            ))

        painter.end()


class StatusIndicator(QWidget):
    """
    Combined status indicator with animated dot and label.
    Displays "MONITORING" (green) or "OFFLINE" (red).
    """

    def __init__(self, parent=None):
        super().__init__(parent)

        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(8)

        # Status dot
        self._dot = StatusDot()

        # Status label
        self._label = QLabel("OFFLINE")
        self._label.setFont(QFont(
            FONT_FAMILY.split(",")[0].strip("' "), 12, QFont.Bold
        ))
        self._label.setStyleSheet(f"color: {Colors.RED}; letter-spacing: 2px;")

        layout.addWidget(self._dot)
        layout.addWidget(self._label)
        layout.addStretch()

    def set_online(self, online: bool) -> None:
        """Update the status display."""
        self._dot.set_online(online)
        if online:
            self._label.setText("MONITORING")
            self._label.setStyleSheet(
                f"color: {Colors.GREEN}; letter-spacing: 2px;"
            )
        else:
            self._label.setText("OFFLINE")
            self._label.setStyleSheet(
                f"color: {Colors.RED}; letter-spacing: 2px;"
            )
