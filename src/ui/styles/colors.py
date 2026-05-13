"""
colors.py — Central design system for the CustomTkinter GUI.
Curated dark-mode color palette with neon cyber-tech accents.
Includes startup validation to prevent Tkinter color rendering crashes.
"""

import re

class Colors:
    # Backgrounds
    BG_DARKEST   = "#060a13"
    BG_DARK      = "#0a0e17"
    BG_PRIMARY   = "#0f1420"
    BG_SECONDARY = "#141a2a"
    BG_ELEVATED  = "#1a2136"
    BG_CARD      = "#1e2640"
    BG_HOVER     = "#242e4a"
    BG_INPUT     = "#161d30"

    # Accents
    CYAN         = "#00d4ff"
    CYAN_DIM     = "#0099bb"
    PURPLE       = "#7c3aed"
    PURPLE_DIM   = "#5b21b6"
    BLUE         = "#3b82f6"
    BLUE_DIM     = "#2563eb"

    # Semantic
    GREEN        = "#10b981"
    RED          = "#ef4444"
    YELLOW       = "#f59e0b"
    ORANGE       = "#f97316"

    # Text
    TEXT_PRIMARY   = "#e8ecf4"
    TEXT_SECONDARY = "#8b95a8"
    TEXT_MUTED     = "#5a6478"
    TEXT_ACCENT    = "#00d4ff"

    # Borders
    BORDER_DEFAULT = "#2a3441"
    BORDER_HOVER   = "#3a4759"
    BORDER_SUBTLE  = "#222b36"

    # Platform-specific colors
    MOSTAQL_COLOR    = "#00d4ff"
    NAFEZLY_COLOR    = "#7c3aed"
    TRUELANCER_COLOR = "#3b82f6"


# ==========================================
# TKINTER COMPATIBILITY VALIDATION
# ==========================================

def validate_colors():
    """
    Validates all colors defined in the Colors class to ensure they are 
    compatible with Tkinter/CustomTkinter.
    Also validates that all Colors.* references in the codebase actually exist.
    """
    import os
    
    hex_pattern = re.compile(r"^#(?:[0-9a-fA-F]{3}){1,2}$")
    allowed_named = {"transparent", "black", "white", "gray", "red", "green", "blue"}
    
    # 1. Format Validation
    for key, value in Colors.__dict__.items():
        if not key.startswith("__") and isinstance(value, str):
            if value.lower() in allowed_named:
                continue
            if not hex_pattern.match(value):
                raise ValueError(
                    f"[Startup Validation Failed] Invalid color format in Colors.{key}: '{value}'. "
                    f"Tkinter requires #RRGGBB hex colors. rgba() and hsla() are strictly unsupported."
                )

    # 2. Missing Attribute Validation (scans codebase)
    src_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "..", "src"))
    if not os.path.exists(src_dir):
        return  # Skip if running built exe without source code
        
    for root, _, files in os.walk(src_dir):
        for file in files:
            if file.endswith(".py"):
                path = os.path.join(root, file)
                try:
                    with open(path, "r", encoding="utf-8") as f:
                        content = f.read()
                        matches = re.findall(r"Colors\.([A-Z0-9_]+)", content)
                        for attr in matches:
                            if attr.startswith("_"):
                                continue
                            if not hasattr(Colors, attr):
                                raise AttributeError(
                                    f"[Startup Validation Failed] Missing color attribute: 'Colors.{attr}' "
                                    f"referenced in {file} is not defined in colors.py."
                                )
                except Exception as e:
                    if isinstance(e, AttributeError):
                        raise e

# Run validation immediately on module load
validate_colors()

PLATFORM_COLORS = {
    "Mostaql":    Colors.MOSTAQL_COLOR,
    "Nafezly":    Colors.NAFEZLY_COLOR,
    "Truelancer": Colors.TRUELANCER_COLOR,
}

# Typography
FONT_FAMILY = "Segoe UI"
FONT_SIZE_SM = 12
FONT_SIZE_MD = 14
FONT_SIZE_LG = 16
FONT_SIZE_XL = 18
FONT_SIZE_2XL = 22
