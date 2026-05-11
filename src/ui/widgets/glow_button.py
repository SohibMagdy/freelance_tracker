"""
glow_button.py — Premium animated button with gradient background,
neon glow effect on hover, and smooth transitions.
"""

from PySide6.QtWidgets import QPushButton, QGraphicsDropShadowEffect
from PySide6.QtCore import (
    Qt, QPropertyAnimation, QEasingCurve, Property, QSize
)
from PySide6.QtGui import QColor, QFont, QIcon

from src.ui.styles.theme import Colors, ANIM_NORMAL, FONT_FAMILY


class GlowButton(QPushButton):
    """
    Stylish button with gradient background and animated glow effect.
    Supports two variants: 'primary' (cyan) and 'danger' (red/purple).
    """

    def __init__(
        self,
        text: str = "",
        variant: str = "primary",
        icon: QIcon = None,
        parent=None
    ):
        super().__init__(text, parent)
        self._variant = variant
        self._glow_intensity = 0.0
        self._pressed_scale = False

        if icon:
            self.setIcon(icon)
            self.setIconSize(QSize(18, 18))

        self.setFixedHeight(44)
        self.setMinimumWidth(160)
        self.setCursor(Qt.PointingHandCursor)
        self.setFont(QFont(FONT_FAMILY.split(",")[0].strip("' "), 13, QFont.DemiBold))

        # Setup glow effect
        self._shadow = QGraphicsDropShadowEffect(self)
        self._shadow.setBlurRadius(0)
        self._shadow.setOffset(0, 0)
        self._update_shadow_color()
        self.setGraphicsEffect(self._shadow)

        # Glow animation
        self._glow_anim = QPropertyAnimation(self, b"glow_intensity", self)
        self._glow_anim.setDuration(ANIM_NORMAL)
        self._glow_anim.setEasingCurve(QEasingCurve.InOutCubic)

        self._apply_style()

    # ==========================================
    # VARIANT COLORS
    # ==========================================

    def _get_colors(self):
        """Return (bg_start, bg_end, text, hover_start, hover_end, glow) for variant."""
        if self._variant == "danger":
            return (
                "#dc2626", "#9333ea",
                "#ffffff",
                "#ef4444", "#a855f7",
                QColor(239, 68, 68, 100),
            )
        else:  # primary
            return (
                "#0891b2", "#0284c7",
                "#ffffff",
                "#06b6d4", "#0ea5e9",
                QColor(0, 212, 255, 100),
            )

    def _update_shadow_color(self):
        colors = self._get_colors()
        self._shadow.setColor(colors[5])

    # ==========================================
    # ANIMATED GLOW PROPERTY
    # ==========================================

    def _get_glow(self) -> float:
        return self._glow_intensity

    def _set_glow(self, val: float) -> None:
        self._glow_intensity = val
        self._shadow.setBlurRadius(val * 30)
        self.update()

    glow_intensity = Property(float, _get_glow, _set_glow)

    # ==========================================
    # STYLING
    # ==========================================

    def _apply_style(self):
        colors = self._get_colors()
        bg_start, bg_end = colors[0], colors[1]
        text_color = colors[2]
        hover_start, hover_end = colors[3], colors[4]

        self.setStyleSheet(f"""
            QPushButton {{
                background: qlineargradient(
                    x1:0, y1:0, x2:1, y2:0,
                    stop:0 {bg_start},
                    stop:1 {bg_end}
                );
                color: {text_color};
                border: none;
                border-radius: 10px;
                padding: 0 24px;
                font-weight: 600;
                letter-spacing: 0.5px;
            }}
            QPushButton:hover {{
                background: qlineargradient(
                    x1:0, y1:0, x2:1, y2:0,
                    stop:0 {hover_start},
                    stop:1 {hover_end}
                );
            }}
            QPushButton:pressed {{
                background: qlineargradient(
                    x1:0, y1:0, x2:1, y2:0,
                    stop:0 {bg_start},
                    stop:1 {bg_end}
                );
                padding-top: 2px;
            }}
            QPushButton:disabled {{
                background: {Colors.BG_ELEVATED};
                color: {Colors.TEXT_MUTED};
            }}
        """)

    # ==========================================
    # EVENTS
    # ==========================================

    def enterEvent(self, event):
        self._glow_anim.stop()
        self._glow_anim.setStartValue(self._glow_intensity)
        self._glow_anim.setEndValue(1.0)
        self._glow_anim.start()
        super().enterEvent(event)

    def leaveEvent(self, event):
        self._glow_anim.stop()
        self._glow_anim.setStartValue(self._glow_intensity)
        self._glow_anim.setEndValue(0.0)
        self._glow_anim.start()
        super().leaveEvent(event)
