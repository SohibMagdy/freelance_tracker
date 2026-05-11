"""
dashboard.py — Main monitoring dashboard page.
Contains platform cards, control buttons, status indicator, live project feed,
animated empty states, and loading indicators.
"""

from datetime import datetime

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QScrollArea, QFrame, QSizePolicy, QGraphicsOpacityEffect
)
from PySide6.QtCore import (
    Qt, Signal, QTimer, QPropertyAnimation, QEasingCurve, QRectF
)
from PySide6.QtGui import QFont, QColor, QPainter, QBrush, QPen

from src.ui.styles.theme import Colors, FONT_FAMILY, ANIM_SLOW
from src.ui.widgets.status_indicator import StatusIndicator
from src.ui.widgets.platform_card import PlatformCard
from src.ui.widgets.project_card import ProjectCard
from src.ui.widgets.glow_button import GlowButton
from src.utils.resources import MOSTAQL_ICON, NAFEZLY_ICON


# ==========================================
# LOADING SPINNER WIDGET
# ==========================================

class LoadingSpinner(QWidget):
    """Animated pulsing ring spinner."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedSize(36, 36)
        self._angle = 0
        self._timer = QTimer(self)
        self._timer.timeout.connect(self._tick)

    def start(self):
        self._timer.start(20)
        self.show()

    def stop(self):
        self._timer.stop()
        self.hide()

    def _tick(self):
        self._angle = (self._angle + 4) % 360
        self.update()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)

        cx, cy = self.width() / 2, self.height() / 2
        radius = 14

        # Background ring
        painter.setPen(QPen(QColor(Colors.BG_ELEVATED), 3))
        painter.setBrush(Qt.NoBrush)
        painter.drawEllipse(QRectF(cx - radius, cy - radius, radius * 2, radius * 2))

        # Spinning arc
        pen = QPen(QColor(Colors.CYAN), 3, Qt.SolidLine, Qt.RoundCap)
        painter.setPen(pen)
        painter.drawArc(
            QRectF(cx - radius, cy - radius, radius * 2, radius * 2),
            self._angle * 16, 90 * 16
        )
        painter.end()


# ==========================================
# ANIMATED EMPTY STATE
# ==========================================

class EmptyState(QWidget):
    """
    Stylish animated placeholder shown when no projects are in the feed.
    Features a pulsing icon and animated dots.
    """

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setMinimumHeight(200)
        self._dot_count = 0

        layout = QVBoxLayout(self)
        layout.setAlignment(Qt.AlignCenter)
        layout.setSpacing(12)

        # Animated icon
        self._icon = QLabel("📡")
        self._icon.setStyleSheet("font-size: 42px; background: transparent;")
        self._icon.setAlignment(Qt.AlignCenter)
        layout.addWidget(self._icon)

        # Pulsing opacity on the icon
        self._icon_opacity = QGraphicsOpacityEffect(self._icon)
        self._icon_opacity.setOpacity(1.0)
        self._icon.setGraphicsEffect(self._icon_opacity)

        self._pulse_anim = QPropertyAnimation(self._icon_opacity, b"opacity", self)
        self._pulse_anim.setDuration(2000)
        self._pulse_anim.setStartValue(0.4)
        self._pulse_anim.setEndValue(1.0)
        self._pulse_anim.setEasingCurve(QEasingCurve.InOutSine)
        self._pulse_anim.setLoopCount(-1)
        self._pulse_anim.start()

        # Title
        self._title = QLabel("Waiting for projects...")
        self._title.setFont(QFont(
            FONT_FAMILY.split(",")[0].strip("' "), 15, QFont.DemiBold
        ))
        self._title.setStyleSheet(f"color: {Colors.TEXT_SECONDARY}; background: transparent;")
        self._title.setAlignment(Qt.AlignCenter)
        layout.addWidget(self._title)

        # Subtitle with animated dots
        self._subtitle = QLabel("Start monitoring to see new projects appear here")
        self._subtitle.setFont(QFont(
            FONT_FAMILY.split(",")[0].strip("' "), 12
        ))
        self._subtitle.setStyleSheet(f"color: {Colors.TEXT_MUTED}; background: transparent;")
        self._subtitle.setAlignment(Qt.AlignCenter)
        layout.addWidget(self._subtitle)

        # Animated dots timer
        self._dots_timer = QTimer(self)
        self._dots_timer.timeout.connect(self._update_dots)

    def set_monitoring(self, active: bool):
        """Switch between idle and monitoring text."""
        if active:
            self._title.setText("Scanning for projects")
            self._subtitle.setText("New projects will appear here automatically")
            self._dots_timer.start(500)
        else:
            self._title.setText("Waiting for projects...")
            self._subtitle.setText("Start monitoring to see new projects appear here")
            self._dots_timer.stop()

    def _update_dots(self):
        self._dot_count = (self._dot_count + 1) % 4
        dots = "." * self._dot_count
        self._title.setText(f"Scanning for projects{dots}")


# ==========================================
# DASHBOARD PAGE
# ==========================================

class DashboardPage(QWidget):
    """
    Main dashboard showing platform selection, monitoring controls,
    status indicator, and live project feed with empty/loading states.
    """

    start_monitoring = Signal()
    stop_monitoring = Signal()
    platform_toggled = Signal(str, bool)

    def __init__(self, settings, parent=None):
        super().__init__(parent)
        self._settings = settings
        self._project_count = 0
        self._start_time = None
        self._is_loading = False
        self._uptime_timer = QTimer(self)
        self._uptime_timer.timeout.connect(self._update_uptime)

        self._build_ui()

    def _build_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(28, 20, 28, 20)
        layout.setSpacing(20)

        # ======== STATUS BAR ========
        status_bar = QHBoxLayout()
        status_bar.setSpacing(20)

        self._status = StatusIndicator()
        status_bar.addWidget(self._status)

        status_bar.addStretch()

        # Loading spinner (hidden by default)
        self._spinner = LoadingSpinner()
        self._spinner.hide()
        status_bar.addWidget(self._spinner)

        # Uptime
        uptime_container = QHBoxLayout()
        uptime_container.setSpacing(6)
        uptime_icon = QLabel("⏱")
        uptime_icon.setStyleSheet(f"color: {Colors.TEXT_MUTED}; font-size: 14px;")
        self._uptime_label = QLabel("00:00:00")
        self._uptime_label.setFont(QFont(
            FONT_FAMILY.split(",")[0].strip("' "), 12
        ))
        self._uptime_label.setStyleSheet(f"color: {Colors.TEXT_SECONDARY};")
        uptime_container.addWidget(uptime_icon)
        uptime_container.addWidget(self._uptime_label)
        status_bar.addLayout(uptime_container)

        # Project count
        count_container = QHBoxLayout()
        count_container.setSpacing(6)
        count_icon = QLabel("📦")
        count_icon.setStyleSheet("font-size: 14px;")
        self._count_label = QLabel("0 projects")
        self._count_label.setFont(QFont(
            FONT_FAMILY.split(",")[0].strip("' "), 12
        ))
        self._count_label.setStyleSheet(f"color: {Colors.TEXT_SECONDARY};")
        count_container.addWidget(count_icon)
        count_container.addWidget(self._count_label)
        status_bar.addLayout(count_container)

        layout.addLayout(status_bar)

        # ======== SECTION: PLATFORMS ========
        section_label = QLabel("PLATFORMS")
        section_label.setFont(QFont(
            FONT_FAMILY.split(",")[0].strip("' "), 10, QFont.Bold
        ))
        section_label.setStyleSheet(
            f"color: {Colors.TEXT_MUTED}; "
            f"letter-spacing: 2px;"
        )
        layout.addWidget(section_label)

        # Platform cards row
        cards_row = QHBoxLayout()
        cards_row.setSpacing(14)

        platforms_config = self._settings.get("platforms", {})

        self._card_mostaql = PlatformCard(
            "mostaql", "Mostaql", MOSTAQL_ICON,
            enabled=platforms_config.get("mostaql", True)
        )
        self._card_nafezly = PlatformCard(
            "nafezly", "Nafezly", NAFEZLY_ICON,
            enabled=platforms_config.get("nafezly", True)
        )
        self._card_truelancer = PlatformCard(
            "truelancer", "Truelancer", None,
            enabled=platforms_config.get("truelancer", True)
        )

        for card in [self._card_mostaql, self._card_nafezly, self._card_truelancer]:
            card.platform_toggled.connect(self._on_platform_toggle)
            cards_row.addWidget(card)

        cards_row.addStretch()
        layout.addLayout(cards_row)

        # ======== CONTROL BUTTONS ========
        controls = QHBoxLayout()
        controls.setSpacing(14)

        self._btn_start = GlowButton("▶  Start Monitoring", variant="primary")
        self._btn_stop = GlowButton("■  Stop Monitoring", variant="danger")
        self._btn_stop.setEnabled(False)

        self._btn_start.clicked.connect(self._on_start)
        self._btn_stop.clicked.connect(self._on_stop)

        controls.addWidget(self._btn_start)
        controls.addWidget(self._btn_stop)
        controls.addStretch()

        layout.addLayout(controls)

        # ======== LIVE FEED ========
        feed_header = QHBoxLayout()
        feed_label = QLabel("LIVE FEED")
        feed_label.setFont(QFont(
            FONT_FAMILY.split(",")[0].strip("' "), 10, QFont.Bold
        ))
        feed_label.setStyleSheet(
            f"color: {Colors.TEXT_MUTED}; letter-spacing: 2px;"
        )
        feed_header.addWidget(feed_label)

        self._feed_count = QLabel("0 new")
        self._feed_count.setFont(QFont(
            FONT_FAMILY.split(",")[0].strip("' "), 10
        ))
        self._feed_count.setStyleSheet(
            f"color: {Colors.CYAN}; "
            f"background: rgba(0,212,255,0.08); "
            f"padding: 2px 8px; border-radius: 6px;"
        )
        feed_header.addWidget(self._feed_count)
        feed_header.addStretch()

        layout.addLayout(feed_header)

        # Scroll area for project cards
        self._scroll = QScrollArea()
        self._scroll.setWidgetResizable(True)
        self._scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self._scroll.setStyleSheet(
            "QScrollArea { border: none; background: transparent; }"
        )

        self._feed_container = QWidget()
        self._feed_layout = QVBoxLayout(self._feed_container)
        self._feed_layout.setContentsMargins(0, 0, 8, 0)
        self._feed_layout.setSpacing(10)
        self._feed_layout.setAlignment(Qt.AlignTop)

        # Empty state placeholder
        self._empty_state = EmptyState()
        self._feed_layout.addWidget(self._empty_state)

        self._scroll.setWidget(self._feed_container)
        layout.addWidget(self._scroll, stretch=1)

    # ==========================================
    # HANDLERS
    # ==========================================

    def _on_platform_toggle(self, key: str, enabled: bool):
        self._settings.set_platform_enabled(key, enabled)
        self.platform_toggled.emit(key, enabled)

    def _on_start(self):
        self._btn_start.setEnabled(False)
        self._btn_stop.setEnabled(True)
        self._status.set_online(True)
        self._start_time = datetime.now()
        self._uptime_timer.start(1000)

        # Show loading state
        self._spinner.start()
        self._is_loading = True
        self._empty_state.set_monitoring(True)

        self.start_monitoring.emit()

    def _on_stop(self):
        self._btn_start.setEnabled(True)
        self._btn_stop.setEnabled(False)
        self._status.set_online(False)
        self._uptime_timer.stop()

        # Reset loading state
        self._spinner.stop()
        self._is_loading = False
        self._empty_state.set_monitoring(False)

        self.stop_monitoring.emit()

    # ==========================================
    # PUBLIC API
    # ==========================================

    def add_project(self, project: dict):
        """Add a new project card to the live feed."""
        # Hide empty state on first project
        if self._project_count == 0:
            self._empty_state.hide()

        # Stop loading spinner after first batch arrives
        if self._is_loading:
            self._spinner.stop()
            self._is_loading = False

        card = ProjectCard(project)
        # Insert at top (after any hidden widgets)
        self._feed_layout.insertWidget(0, card)
        self._project_count += 1

        # Update feed counter
        self._feed_count.setText(f"{self._project_count} new")

        # Auto-scroll to top
        QTimer.singleShot(100, lambda: self._scroll.verticalScrollBar().setValue(0))

        # Limit visible cards to prevent memory issues
        if self._feed_layout.count() > 100:
            item = self._feed_layout.takeAt(self._feed_layout.count() - 1)
            if item and item.widget() and item.widget() is not self._empty_state:
                item.widget().deleteLater()

    def update_total_count(self, count: int):
        """Update the total projects counter."""
        self._count_label.setText(f"{count} projects")

        # End loading state when first cycle completes
        if self._is_loading:
            self._spinner.stop()
            self._is_loading = False

    def get_enabled_platforms(self) -> list:
        """Return list of enabled platform keys."""
        platforms = self._settings.get("platforms", {})
        return [k for k, v in platforms.items() if v]

    def _update_uptime(self):
        if self._start_time:
            delta = datetime.now() - self._start_time
            hours, remainder = divmod(int(delta.total_seconds()), 3600)
            minutes, seconds = divmod(remainder, 60)
            self._uptime_label.setText(f"{hours:02d}:{minutes:02d}:{seconds:02d}")

    def set_offline(self):
        """Called when monitor stops."""
        self._btn_start.setEnabled(True)
        self._btn_stop.setEnabled(False)
        self._status.set_online(False)
        self._uptime_timer.stop()
        self._spinner.stop()
        self._is_loading = False
        self._empty_state.set_monitoring(False)
