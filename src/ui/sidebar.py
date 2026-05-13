"""
sidebar.py — Navigation sidebar with icon buttons and active indicator for CustomTkinter.
"""

import customtkinter as ctk
from typing import Callable

from src.ui.styles.colors import Colors


class SidebarButton(ctk.CTkButton):
    """Navigation button with icon and active state indicator."""

    def __init__(self, master, icon_char: str, command: Callable, **kwargs):
        super().__init__(
            master, 
            text=icon_char,
            width=50, 
            height=50,
            corner_radius=8,
            fg_color="transparent",
            text_color=Colors.TEXT_MUTED,
            hover_color=Colors.BG_HOVER,
            font=("Segoe UI", 24),
            command=command,
            **kwargs
        )
        self.active = False
        
    def set_active(self, active: bool):
        self.active = active
        if active:
            self.configure(
                fg_color="#0c2438",  # Tkinter compatible dark cyan-tinted hex
                text_color=Colors.CYAN,
            )
        else:
            self.configure(
                fg_color="transparent",
                text_color=Colors.TEXT_MUTED,
            )


class Sidebar(ctk.CTkFrame):
    """
    Vertical icon navigation sidebar.
    Calls on_page_change(int) when a navigation item is clicked.
    """
    
    PAGE_DASHBOARD = 0
    PAGE_SETTINGS = 1

    def __init__(self, master, on_page_change: Callable[[int], None], **kwargs):
        super().__init__(
            master,
            width=65,
            corner_radius=0,
            fg_color=Colors.BG_DARKEST,
            border_color=Colors.BORDER_DEFAULT,
            border_width=0, # No border to keep it clean, maybe right border using a separate frame
            **kwargs
        )
        self.on_page_change = on_page_change
        
        # Right border line (to simulate border-right)
        self.border_line = ctk.CTkFrame(self, width=1, fg_color=Colors.BORDER_DEFAULT, corner_radius=0)
        self.border_line.pack(side="right", fill="y")
        
        # Container for buttons
        self.btn_container = ctk.CTkFrame(self, fg_color="transparent")
        self.btn_container.pack(side="top", fill="both", expand=True)

        # Dashboard Button
        self.btn_dashboard = SidebarButton(self.btn_container, "🏠", command=lambda: self._on_click(self.PAGE_DASHBOARD))
        self.btn_dashboard.pack(pady=(20, 5), padx=5)
        
        # Settings Button
        self.btn_settings = SidebarButton(self.btn_container, "⚙", command=lambda: self._on_click(self.PAGE_DASHBOARD + 1))
        self.btn_settings.pack(pady=5, padx=5)
        
        self.buttons = [self.btn_dashboard, self.btn_settings]
        
        # Version Label
        self.version_label = ctk.CTkLabel(
            self.btn_container, 
            text="v2.0", 
            text_color=Colors.TEXT_MUTED,
            font=("Segoe UI", 11)
        )
        self.version_label.pack(side="bottom", pady=(5, 20))
        
        self._set_active(0)
        
    def _on_click(self, index: int):
        self._set_active(index)
        if self.on_page_change:
            self.on_page_change(index)
            
    def _set_active(self, index: int):
        for i, btn in enumerate(self.buttons):
            btn.set_active(i == index)
