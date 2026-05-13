"""
project_card.py — Modern project feed card for CustomTkinter.
Shows platform badge, title, description, and timestamp.
Clicking opens the project link.
"""

import webbrowser
from datetime import datetime
import customtkinter as ctk

from src.ui.styles.colors import Colors, PLATFORM_COLORS

class ProjectCard(ctk.CTkFrame):
    def __init__(self, master, project: dict, **kwargs):
        super().__init__(
            master,
            corner_radius=12,
            fg_color=Colors.BG_CARD,
            border_width=1,
            border_color=Colors.BORDER_DEFAULT,
            **kwargs
        )
        self.project = project
        self.link = project.get("link", "")
        self.site = project.get("site", "Unknown")
        self.accent = PLATFORM_COLORS.get(self.site, Colors.CYAN)

        # Apply left border style by using a thin frame
        self.left_border = ctk.CTkFrame(self, width=4, corner_radius=0, fg_color=self.accent)
        self.left_border.pack(side="left", fill="y")
        
        self.content_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.content_frame.pack(side="left", fill="both", expand=True, padx=12, pady=10)

        self._build_ui()
        self._bind_click(self)

    def _build_ui(self):
        # Top Row: Badge + Timestamp
        top_row = ctk.CTkFrame(self.content_frame, fg_color="transparent")
        top_row.pack(fill="x", pady=(0, 5))

        badge = ctk.CTkLabel(
            top_row,
            text=self.site,
            font=("Segoe UI", 11, "bold"),
            text_color=self.accent,
            fg_color="transparent" # Ideally a faint background, but CTk doesn't support rgba well
        )
        badge.pack(side="left")

        ts = self.project.get("timestamp", datetime.now().strftime("%H:%M:%S"))
        time_label = ctk.CTkLabel(
            top_row,
            text=ts,
            font=("Segoe UI", 11),
            text_color=Colors.TEXT_MUTED
        )
        time_label.pack(side="right")

        # Title
        title = self.project.get("title", "Untitled Project")
        title_label = ctk.CTkLabel(
            self.content_frame,
            text=title,
            font=("Segoe UI", 14, "bold"),
            text_color=Colors.TEXT_PRIMARY,
            anchor="w",
            justify="left",
            wraplength=600
        )
        title_label.pack(fill="x")

        # Description
        desc = self.project.get("description", "")
        if desc:
            desc_truncated = desc[:120] + ("..." if len(desc) > 120 else "")
            desc_label = ctk.CTkLabel(
                self.content_frame,
                text=desc_truncated,
                font=("Segoe UI", 12),
                text_color=Colors.TEXT_SECONDARY,
                anchor="w",
                justify="left",
                wraplength=600
            )
            desc_label.pack(fill="x", pady=(2, 0))

    def _bind_click(self, widget):
        widget.bind("<Button-1>", self._on_click)
        widget.bind("<Enter>", self._on_enter)
        widget.bind("<Leave>", self._on_leave)
        for child in widget.winfo_children():
            self._bind_click(child)

    def _on_click(self, event):
        if self.link:
            try:
                webbrowser.open(self.link)
            except Exception:
                pass

    def _on_enter(self, event):
        self.configure(fg_color=Colors.BG_HOVER)

    def _on_leave(self, event):
        self.configure(fg_color=Colors.BG_CARD)
