"""
theme.py — Central design system for the Freelance Tracker GUI.
Contains color palette, typography, and the full QSS stylesheet.
Cyber-tech SaaS aesthetic with glassmorphism, neon accents, and dark mode.
"""


# ==========================================
# COLOR PALETTE
# ==========================================

class Colors:
    """Curated dark-mode color palette with neon cyber-tech accents."""

    # Backgrounds (darkest → lightest)
    BG_DARKEST   = "#060a13"
    BG_DARK      = "#0a0e17"
    BG_PRIMARY   = "#0f1420"
    BG_SECONDARY = "#141a2a"
    BG_ELEVATED  = "#1a2136"
    BG_CARD      = "#1e2640"
    BG_HOVER     = "#242e4a"
    BG_INPUT     = "#161d30"

    # Glass (semi-transparent for glassmorphism)
    GLASS_BG     = "rgba(15, 20, 35, 0.85)"
    GLASS_BORDER = "rgba(255, 255, 255, 0.06)"
    GLASS_HOVER  = "rgba(25, 35, 60, 0.9)"

    # Neon accents
    CYAN         = "#00d4ff"
    CYAN_DIM     = "#0099bb"
    CYAN_GLOW    = "rgba(0, 212, 255, 0.3)"
    PURPLE       = "#7c3aed"
    PURPLE_DIM   = "#5b21b6"
    PURPLE_GLOW  = "rgba(124, 58, 237, 0.3)"
    BLUE         = "#3b82f6"
    BLUE_DIM     = "#2563eb"
    BLUE_GLOW    = "rgba(59, 130, 246, 0.3)"

    # Semantic
    GREEN        = "#10b981"
    GREEN_GLOW   = "rgba(16, 185, 129, 0.4)"
    RED          = "#ef4444"
    RED_GLOW     = "rgba(239, 68, 68, 0.3)"
    YELLOW       = "#f59e0b"
    ORANGE       = "#f97316"

    # Text
    TEXT_PRIMARY   = "#e8ecf4"
    TEXT_SECONDARY = "#8b95a8"
    TEXT_MUTED     = "#5a6478"
    TEXT_ACCENT    = "#00d4ff"

    # Borders
    BORDER_SUBTLE  = "rgba(255, 255, 255, 0.05)"
    BORDER_DEFAULT = "rgba(255, 255, 255, 0.08)"
    BORDER_HOVER   = "rgba(255, 255, 255, 0.12)"
    BORDER_ACCENT  = "rgba(0, 212, 255, 0.4)"

    # Platform-specific colors
    MOSTAQL_COLOR    = "#00d4ff"
    NAFEZLY_COLOR    = "#7c3aed"
    TRUELANCER_COLOR = "#3b82f6"


# ==========================================
# PLATFORM COLORS MAP
# ==========================================

PLATFORM_COLORS = {
    "Mostaql":    Colors.MOSTAQL_COLOR,
    "Nafezly":    Colors.NAFEZLY_COLOR,
    "Truelancer": Colors.TRUELANCER_COLOR,
}


# ==========================================
# TYPOGRAPHY
# ==========================================

FONT_FAMILY = "'Segoe UI', 'Inter', 'SF Pro Display', 'Helvetica Neue', sans-serif"
FONT_SIZE_XS = "11px"
FONT_SIZE_SM = "12px"
FONT_SIZE_MD = "13px"
FONT_SIZE_LG = "15px"
FONT_SIZE_XL = "18px"
FONT_SIZE_2XL = "22px"
FONT_SIZE_3XL = "28px"


# ==========================================
# ANIMATION TIMING
# ==========================================

ANIM_FAST = 150       # ms
ANIM_NORMAL = 250     # ms
ANIM_SLOW = 400       # ms
ANIM_VERY_SLOW = 600  # ms


# ==========================================
# GLOBAL STYLESHEET
# ==========================================

def get_stylesheet() -> str:
    """Generate the complete QSS stylesheet for the application."""
    return f"""
    /* ==========================================
       GLOBAL RESET & BASE
       ========================================== */

    * {{
        margin: 0;
        padding: 0;
        outline: none;
    }}

    QWidget {{
        font-family: {FONT_FAMILY};
        font-size: {FONT_SIZE_MD};
        color: {Colors.TEXT_PRIMARY};
        background-color: transparent;
    }}

    QMainWindow {{
        background-color: {Colors.BG_DARK};
    }}

    /* ==========================================
       SCROLL BARS
       ========================================== */

    QScrollBar:vertical {{
        background: transparent;
        width: 6px;
        margin: 4px 2px;
        border-radius: 3px;
    }}

    QScrollBar::handle:vertical {{
        background: {Colors.BG_HOVER};
        border-radius: 3px;
        min-height: 30px;
    }}

    QScrollBar::handle:vertical:hover {{
        background: {Colors.TEXT_MUTED};
    }}

    QScrollBar::add-line:vertical,
    QScrollBar::sub-line:vertical {{
        height: 0;
    }}

    QScrollBar::add-page:vertical,
    QScrollBar::sub-page:vertical {{
        background: transparent;
    }}

    QScrollBar:horizontal {{
        background: transparent;
        height: 6px;
        margin: 2px 4px;
        border-radius: 3px;
    }}

    QScrollBar::handle:horizontal {{
        background: {Colors.BG_HOVER};
        border-radius: 3px;
        min-width: 30px;
    }}

    /* ==========================================
       SCROLL AREA
       ========================================== */

    QScrollArea {{
        border: none;
        background: transparent;
    }}

    QScrollArea > QWidget > QWidget {{
        background: transparent;
    }}

    /* ==========================================
       LABELS
       ========================================== */

    QLabel {{
        background: transparent;
        border: none;
    }}

    /* ==========================================
       LINE EDIT / TEXT INPUT
       ========================================== */

    QLineEdit {{
        background-color: {Colors.BG_INPUT};
        border: 1px solid {Colors.BORDER_DEFAULT};
        border-radius: 8px;
        padding: 10px 14px;
        font-size: {FONT_SIZE_MD};
        color: {Colors.TEXT_PRIMARY};
        selection-background-color: {Colors.CYAN_DIM};
    }}

    QLineEdit:focus {{
        border-color: {Colors.CYAN};
    }}

    QLineEdit::placeholder {{
        color: {Colors.TEXT_MUTED};
    }}

    /* ==========================================
       SLIDER
       ========================================== */

    QSlider::groove:horizontal {{
        border: none;
        height: 4px;
        background: {Colors.BG_ELEVATED};
        border-radius: 2px;
    }}

    QSlider::handle:horizontal {{
        background: qlineargradient(
            x1:0, y1:0, x2:1, y2:1,
            stop:0 {Colors.CYAN},
            stop:1 {Colors.PURPLE}
        );
        border: none;
        width: 16px;
        height: 16px;
        margin: -6px 0;
        border-radius: 8px;
    }}

    QSlider::handle:horizontal:hover {{
        width: 18px;
        height: 18px;
        margin: -7px 0;
        border-radius: 9px;
    }}

    QSlider::sub-page:horizontal {{
        background: qlineargradient(
            x1:0, y1:0, x2:1, y2:0,
            stop:0 {Colors.CYAN},
            stop:1 {Colors.PURPLE}
        );
        border-radius: 2px;
    }}

    /* ==========================================
       TOOLTIPS
       ========================================== */

    QToolTip {{
        background-color: {Colors.BG_ELEVATED};
        color: {Colors.TEXT_PRIMARY};
        border: 1px solid {Colors.BORDER_DEFAULT};
        border-radius: 6px;
        padding: 6px 10px;
        font-size: {FONT_SIZE_SM};
    }}

    /* ==========================================
       MENU (system tray)
       ========================================== */

    QMenu {{
        background-color: {Colors.BG_SECONDARY};
        border: 1px solid {Colors.BORDER_DEFAULT};
        border-radius: 8px;
        padding: 4px;
    }}

    QMenu::item {{
        padding: 8px 24px;
        border-radius: 4px;
        color: {Colors.TEXT_PRIMARY};
    }}

    QMenu::item:selected {{
        background-color: {Colors.BG_HOVER};
    }}

    QMenu::separator {{
        height: 1px;
        background: {Colors.BORDER_DEFAULT};
        margin: 4px 8px;
    }}

    /* ==========================================
       STACKED WIDGET
       ========================================== */

    QStackedWidget {{
        background: transparent;
    }}

    /* ==========================================
       FRAME / CARD PANELS
       ========================================== */

    QFrame {{
        background: transparent;
        border: none;
    }}

    /* ==========================================
       SYSTEM TRAY ICON
       ========================================== */

    QSystemTrayIcon {{
        background: transparent;
    }}
    """

