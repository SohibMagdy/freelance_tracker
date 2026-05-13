"""
settings.py — Settings page with configurable options for CustomTkinter.
Includes check interval slider, notification toggles, keyword filter,
and start-with-Windows toggle.
"""

import winreg
import sys
import os
import customtkinter as ctk

from src.ui.styles.colors import Colors

class SettingRow(ctk.CTkFrame):
    """A single setting row with label, description, and control widget."""

    def __init__(self, master, title: str, description: str, **kwargs):
        super().__init__(master, fg_color="transparent", **kwargs)
        
        # Text side
        text_frame = ctk.CTkFrame(self, fg_color="transparent")
        text_frame.pack(side="left", fill="x", expand=True, pady=8)

        title_label = ctk.CTkLabel(
            text_frame, 
            text=title, 
            font=("Segoe UI", 16, "bold"), 
            text_color=Colors.TEXT_PRIMARY,
            anchor="w"
        )
        title_label.pack(fill="x")

        desc_label = ctk.CTkLabel(
            text_frame, 
            text=description, 
            font=("Segoe UI", 12), 
            text_color=Colors.TEXT_MUTED,
            anchor="w",
            wraplength=400,
            justify="left"
        )
        desc_label.pack(fill="x")

        # Control side
        self.control_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.control_frame.pack(side="right", fill="y", padx=(20, 0))

    def add_control(self, widget: ctk.CTkBaseClass):
        """Add a control widget to the right side."""
        widget.pack(in_=self.control_frame, side="right", anchor="e")


class Divider(ctk.CTkFrame):
    """Subtle horizontal divider line."""
    def __init__(self, master, **kwargs):
        super().__init__(master, height=1, fg_color=Colors.BORDER_SUBTLE, corner_radius=0, **kwargs)


class SettingsPage(ctk.CTkScrollableFrame):
    """
    Application settings page with all configurable options.
    Auto-saves changes to the settings manager.
    """

    def __init__(self, master, settings, on_settings_changed=None, **kwargs):
        super().__init__(
            master, 
            fg_color=Colors.BG_DARK,
            **kwargs
        )
        self.settings = settings
        self.on_settings_changed_callback = on_settings_changed
        self._build_ui()

    def _build_ui(self):
        # Header
        header = ctk.CTkLabel(
            self, 
            text="Settings", 
            font=("Segoe UI", 28, "bold"), 
            text_color=Colors.TEXT_PRIMARY,
            anchor="w"
        )
        header.pack(fill="x", padx=28, pady=(20, 0))

        subtitle = ctk.CTkLabel(
            self, 
            text="Configure monitoring behavior and preferences", 
            font=("Segoe UI", 14), 
            text_color=Colors.TEXT_MUTED,
            anchor="w"
        )
        subtitle.pack(fill="x", padx=28, pady=(0, 20))

        # ======== MONITORING SECTION ========
        self._add_section_header("MONITORING")

        interval_row = SettingRow(
            self,
            "Check Interval",
            "How often to check for new projects (seconds)"
        )
        
        interval_container = ctk.CTkFrame(interval_row.control_frame, fg_color="transparent")
        
        self.interval_slider = ctk.CTkSlider(
            interval_container, 
            from_=10, 
            to=120, 
            number_of_steps=110,
            width=200,
            progress_color=Colors.CYAN,
            button_color=Colors.TEXT_PRIMARY,
            command=self._on_interval_slider_changed
        )
        self.interval_slider.set(self.settings.check_interval)
        
        self.interval_value = ctk.CTkLabel(
            interval_container, 
            text=f"{self.settings.check_interval}s", 
            font=("Segoe UI", 14, "bold"), 
            text_color=Colors.CYAN,
            width=50
        )
        
        # We handle the release event to save, while sliding updates the label
        self.interval_slider.bind("<ButtonRelease-1>", self._on_interval_changed)
        
        self.interval_slider.pack(side="left", padx=5)
        self.interval_value.pack(side="left")
        
        interval_row.add_control(interval_container)
        interval_row.pack(fill="x", padx=28)

        # ======== NOTIFICATIONS SECTION ========
        self._add_section_header("NOTIFICATIONS")

        notif_row = SettingRow(
            self,
            "Desktop Notifications",
            "Show Windows toast notifications for new projects"
        )
        self.notif_toggle = ctk.CTkSwitch(
            notif_row.control_frame,
            text="",
            progress_color=Colors.CYAN,
            command=lambda: self._save("notifications_enabled", self.notif_toggle.get() == 1)
        )
        if self.settings.notifications_enabled:
            self.notif_toggle.select()
        notif_row.add_control(self.notif_toggle)
        notif_row.pack(fill="x", padx=28)

        # ======== FILTER SECTION ========
        self._add_section_header("FILTERS")

        keyword_row = SettingRow(
            self,
            "Keyword Filter",
            "Only show projects matching these keywords (comma-separated, leave empty for all)"
        )
        self.keyword_input = ctk.CTkEntry(
            keyword_row.control_frame,
            width=260,
            placeholder_text="e.g. python, react, design",
            border_color=Colors.BORDER_DEFAULT,
            fg_color=Colors.BG_INPUT
        )
        self.keyword_input.insert(0, self.settings.keyword_filter)
        # Bind focus out and enter key to save
        self.keyword_input.bind("<FocusOut>", self._on_keyword_changed)
        self.keyword_input.bind("<Return>", self._on_keyword_changed)
        
        keyword_row.add_control(self.keyword_input)
        keyword_row.pack(fill="x", padx=28)

        # ======== SYSTEM SECTION ========
        self._add_section_header("SYSTEM")

        startup_row = SettingRow(
            self,
            "Start with Windows",
            "Automatically launch Freelance Tracker when Windows starts"
        )
        self.startup_toggle = ctk.CTkSwitch(
            startup_row.control_frame,
            text="",
            progress_color=Colors.CYAN,
            command=self._on_startup_toggle
        )
        if self.settings.get("start_with_windows", False):
            self.startup_toggle.select()
        startup_row.add_control(self.startup_toggle)
        startup_row.pack(fill="x", padx=28)

        minimized_row = SettingRow(
            self,
            "Start Minimized",
            "Launch minimized to system tray"
        )
        self.minimized_toggle = ctk.CTkSwitch(
            minimized_row.control_frame,
            text="",
            progress_color=Colors.CYAN,
            command=lambda: self._save("start_minimized", self.minimized_toggle.get() == 1)
        )
        if self.settings.get("start_minimized", False):
            self.minimized_toggle.select()
        minimized_row.add_control(self.minimized_toggle)
        minimized_row.pack(fill="x", padx=28, pady=(0, 20))

    def _add_section_header(self, text: str):
        section_lbl = ctk.CTkLabel(
            self,
            text=text,
            font=("Segoe UI", 12, "bold"),
            text_color=Colors.TEXT_MUTED,
            anchor="w"
        )
        section_lbl.pack(fill="x", padx=28, pady=(15, 5))
        Divider(self).pack(fill="x", padx=28, pady=(0, 10))

    # ==========================================
    # HANDLERS
    # ==========================================

    def _on_interval_slider_changed(self, value):
        self.interval_value.configure(text=f"{int(value)}s")

    def _on_interval_changed(self, event):
        value = int(self.interval_slider.get())
        self.settings.check_interval = value
        if self.on_settings_changed_callback:
            self.on_settings_changed_callback()

    def _on_keyword_changed(self, event):
        self.settings.set("keyword_filter", self.keyword_input.get().strip())
        if self.on_settings_changed_callback:
            self.on_settings_changed_callback()

    def _on_startup_toggle(self):
        enabled = self.startup_toggle.get() == 1
        self._save("start_with_windows", enabled)
        self._set_windows_startup(enabled)

    def _save(self, key: str, value):
        self.settings.set(key, value)
        if self.on_settings_changed_callback:
            self.on_settings_changed_callback()

    # ==========================================
    # WINDOWS STARTUP REGISTRY
    # ==========================================

    def _set_windows_startup(self, enable: bool):
        key_path = r"Software\Microsoft\Windows\CurrentVersion\Run"
        app_name = "FreelanceTracker"

        try:
            key = winreg.OpenKey(
                winreg.HKEY_CURRENT_USER, key_path,
                0, winreg.KEY_SET_VALUE
            )

            if enable:
                exe_path = sys.executable
                if getattr(sys, 'frozen', False):
                    script_path = sys.executable
                else:
                    script_path = os.path.abspath(
                        os.path.join(os.path.dirname(__file__), "..", "..", "..", "Freelance Tracker.py")
                    )
                
                # If frozen, just point to the exe, if dev, use python + script
                if getattr(sys, 'frozen', False):
                    winreg.SetValueEx(key, app_name, 0, winreg.REG_SZ, f'"{script_path}"')
                else:
                    winreg.SetValueEx(key, app_name, 0, winreg.REG_SZ, f'"{exe_path}" "{script_path}"')
            else:
                try:
                    winreg.DeleteValue(key, app_name)
                except FileNotFoundError:
                    pass

            winreg.CloseKey(key)

        except Exception as e:
            print(f"[Settings] Failed to modify startup: {e}")
