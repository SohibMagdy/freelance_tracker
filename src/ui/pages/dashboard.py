"""
dashboard.py — Main monitoring dashboard page for CustomTkinter.
"""

from datetime import datetime
import customtkinter as ctk

from src.ui.styles.colors import Colors
from src.ui.widgets.platform_card import PlatformCard
from src.ui.widgets.project_card import ProjectCard

class DashboardPage(ctk.CTkFrame):
    def __init__(self, master, settings, on_start, on_stop, **kwargs):
        super().__init__(
            master, 
            fg_color=Colors.BG_DARK,
            **kwargs
        )
        self.settings = settings
        self.on_start_callback = on_start
        self.on_stop_callback = on_stop
        
        self.project_count = 0
        self.start_time = None
        
        self._build_ui()
        self._update_uptime()

    def _build_ui(self):
        # Container with margins
        self.container = ctk.CTkFrame(self, fg_color="transparent")
        self.container.pack(fill="both", expand=True, padx=28, pady=20)

        # ======== STATUS BAR ========
        status_bar = ctk.CTkFrame(self.container, fg_color="transparent")
        status_bar.pack(fill="x", pady=(0, 20))

        # Status Indicator
        self.status_label = ctk.CTkLabel(
            status_bar,
            text="● OFFLINE",
            font=("Segoe UI", 12, "bold"),
            text_color=Colors.TEXT_MUTED
        )
        self.status_label.pack(side="left")

        # Uptime
        self.uptime_label = ctk.CTkLabel(
            status_bar,
            text="⏱ 00:00:00",
            font=("Segoe UI", 12),
            text_color=Colors.TEXT_SECONDARY
        )
        self.uptime_label.pack(side="right", padx=(20, 0))

        # Project count
        self.count_label = ctk.CTkLabel(
            status_bar,
            text="📦 0 projects",
            font=("Segoe UI", 12),
            text_color=Colors.TEXT_SECONDARY
        )
        self.count_label.pack(side="right")

        # ======== SECTION: PLATFORMS ========
        section_label = ctk.CTkLabel(
            self.container,
            text="PLATFORMS",
            font=("Segoe UI", 12, "bold"),
            text_color=Colors.TEXT_MUTED
        )
        section_label.pack(anchor="w", pady=(0, 10))

        cards_frame = ctk.CTkFrame(self.container, fg_color="transparent")
        cards_frame.pack(fill="x", pady=(0, 20))

        platforms_config = self.settings.get("platforms", {})

        self.card_mostaql = PlatformCard(
            cards_frame, "mostaql", "Mostaql", enabled=platforms_config.get("mostaql", True),
            on_toggle=self._on_platform_toggle
        )
        self.card_mostaql.pack(side="left", padx=(0, 14))

        self.card_nafezly = PlatformCard(
            cards_frame, "nafezly", "Nafezly", enabled=platforms_config.get("nafezly", True),
            on_toggle=self._on_platform_toggle
        )
        self.card_nafezly.pack(side="left", padx=(0, 14))

        self.card_truelancer = PlatformCard(
            cards_frame, "truelancer", "Truelancer", enabled=platforms_config.get("truelancer", True),
            on_toggle=self._on_platform_toggle
        )
        self.card_truelancer.pack(side="left")

        # ======== CONTROL BUTTONS ========
        controls = ctk.CTkFrame(self.container, fg_color="transparent")
        controls.pack(fill="x", pady=(0, 20))

        self.btn_start = ctk.CTkButton(
            controls,
            text="▶ Start Monitoring",
            font=("Segoe UI", 14, "bold"),
            fg_color=Colors.CYAN_DIM,
            hover_color=Colors.CYAN,
            text_color=Colors.BG_DARKEST,
            command=self._on_start
        )
        self.btn_start.pack(side="left", padx=(0, 14))

        self.btn_stop = ctk.CTkButton(
            controls,
            text="■ Stop Monitoring",
            font=("Segoe UI", 14, "bold"),
            fg_color=Colors.RED,
            hover_color="#dc2626", # darker red
            text_color=Colors.TEXT_PRIMARY,
            command=self._on_stop,
            state="disabled"
        )
        self.btn_stop.pack(side="left")

        # ======== LIVE FEED ========
        feed_header = ctk.CTkFrame(self.container, fg_color="transparent")
        feed_header.pack(fill="x", pady=(0, 10))

        feed_label = ctk.CTkLabel(
            feed_header,
            text="LIVE FEED",
            font=("Segoe UI", 12, "bold"),
            text_color=Colors.TEXT_MUTED
        )
        feed_label.pack(side="left")

        # Scrollable area for projects
        self.feed_scroll = ctk.CTkScrollableFrame(
            self.container,
            fg_color="transparent",
            scrollbar_button_color=Colors.BG_HOVER,
            scrollbar_button_hover_color=Colors.TEXT_MUTED
        )
        self.feed_scroll.pack(fill="both", expand=True)

        self.empty_label = ctk.CTkLabel(
            self.feed_scroll,
            text="Waiting for projects...\nStart monitoring to see new projects appear here",
            font=("Segoe UI", 14),
            text_color=Colors.TEXT_MUTED,
            justify="center"
        )
        self.empty_label.pack(pady=40)
        
        # Track inserted cards to manage memory
        self.cards = []

    def _on_platform_toggle(self, key: str, enabled: bool):
        self.settings.set_platform_enabled(key, enabled)
        # Assuming the monitor will pick up changes or we signal it via parent
        # In this refactor, we'll let the main_window handle the live update if needed

    def _on_start(self):
        self.btn_start.configure(state="disabled")
        self.btn_stop.configure(state="normal")
        self.status_label.configure(text="● ONLINE", text_color=Colors.GREEN)
        self.empty_label.configure(text="Scanning for projects...\nNew projects will appear here")
        self.start_time = datetime.now()
        
        if self.on_start_callback:
            self.on_start_callback()

    def _on_stop(self):
        self.btn_start.configure(state="normal")
        self.btn_stop.configure(state="disabled")
        self.status_label.configure(text="● OFFLINE", text_color=Colors.TEXT_MUTED)
        self.empty_label.configure(text="Waiting for projects...\nStart monitoring to see new projects appear here")
        self.start_time = None
        
        if self.on_stop_callback:
            self.on_stop_callback()

    def add_project(self, project: dict):
        if self.project_count == 0:
            self.empty_label.pack_forget()

        card = ProjectCard(self.feed_scroll, project)
        # To insert at the top in CTk, we just pack it at the top. 
        # But pack_configure inside CTkScrollableFrame might act like append. 
        # So we pack before other children if possible, but tkinter's pack doesn't easily support 'insert at top'.
        # For simplicity, we just pack it at the top by rebuilding layout or using insert.
        # Actually, `pack(before=widget)` exists in standard tkinter!
        if self.cards:
            card.pack(fill="x", pady=(0, 10), before=self.cards[0])
        else:
            card.pack(fill="x", pady=(0, 10))
            
        self.cards.insert(0, card)
        self.project_count += 1
        
        # Limit to 100 cards
        if len(self.cards) > 100:
            oldest = self.cards.pop()
            oldest.destroy()

    def update_total_count(self, count: int):
        self.count_label.configure(text=f"📦 {count} projects")

    def _update_uptime(self):
        if self.start_time:
            delta = datetime.now() - self.start_time
            hours, remainder = divmod(int(delta.total_seconds()), 3600)
            minutes, seconds = divmod(remainder, 60)
            self.uptime_label.configure(text=f"⏱ {hours:02d}:{minutes:02d}:{seconds:02d}")
            
        # Schedule next update
        self.after(1000, self._update_uptime)

    def set_offline(self):
        self._on_stop()

    def get_enabled_platforms(self) -> list:
        platforms = self.settings.get("platforms", {})
        return [k for k, v in platforms.items() if v]
