"""
platform_card.py — Interactive platform card with toggle, logo, and glow accent for CustomTkinter.
Displays a freelance platform's logo, name, and on/off toggle.
"""

import customtkinter as ctk
from typing import Callable

from src.ui.styles.colors import Colors, PLATFORM_COLORS

class PlatformCard(ctk.CTkFrame):
    def __init__(
        self,
        master,
        key: str,
        name: str,
        logo_path: str = None,
        enabled: bool = True,
        on_toggle: Callable[[str, bool], None] = None,
        **kwargs
    ):
        super().__init__(
            master,
            width=180,
            height=110,
            corner_radius=14,
            fg_color=Colors.BG_CARD,
            border_width=1,
            border_color=Colors.BORDER_DEFAULT,
            **kwargs
        )
        self.pack_propagate(False)
        self.grid_propagate(False)
        
        self.key = key
        self.platform_name = name
        self.accent = PLATFORM_COLORS.get(name, Colors.CYAN)
        self.enabled = enabled
        self.on_toggle_callback = on_toggle

        self._build_ui(logo_path)
        self._apply_style()

    def _build_ui(self, logo_path: str):
        # Top Row: Icon + Name
        top_frame = ctk.CTkFrame(self, fg_color="transparent")
        top_frame.pack(side="top", fill="x", padx=14, pady=(12, 0))

        # We skip the complex image loading for now, use a colored dot or text as fallback if pillow image fails
        icon_label = ctk.CTkLabel(top_frame, text="🌐", font=("Segoe UI", 22), text_color=self.accent)
        icon_label.pack(side="left", padx=(0, 10))

        name_label = ctk.CTkLabel(
            top_frame, 
            text=self.platform_name, 
            font=("Segoe UI", 14, "bold"),
            text_color=Colors.TEXT_PRIMARY
        )
        name_label.pack(side="left")

        # Bottom Row: Status + Toggle
        bottom_frame = ctk.CTkFrame(self, fg_color="transparent")
        bottom_frame.pack(side="bottom", fill="x", padx=14, pady=(0, 12))

        self.status_label = ctk.CTkLabel(
            bottom_frame,
            text="Enabled" if self.enabled else "Disabled",
            font=("Segoe UI", 12),
            text_color=Colors.GREEN if self.enabled else Colors.TEXT_MUTED
        )
        self.status_label.pack(side="left")

        self.toggle = ctk.CTkSwitch(
            bottom_frame,
            text="",
            width=40,
            progress_color=self.accent,
            button_color=Colors.TEXT_PRIMARY,
            button_hover_color=Colors.TEXT_PRIMARY,
            command=self._on_toggle
        )
        if self.enabled:
            self.toggle.select()
        else:
            self.toggle.deselect()
            
        self.toggle.pack(side="right")

    def _on_toggle(self):
        self.enabled = self.toggle.get() == 1
        self.status_label.configure(
            text="Enabled" if self.enabled else "Disabled",
            text_color=Colors.GREEN if self.enabled else Colors.TEXT_MUTED
        )
        self._apply_style()
        if self.on_toggle_callback:
            self.on_toggle_callback(self.key, self.enabled)

    def _apply_style(self):
        if self.enabled:
            self.configure(border_color=self.accent)
        else:
            self.configure(border_color=Colors.BORDER_DEFAULT)
