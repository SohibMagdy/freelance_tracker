<p align="center">
  <img src="icons/FWT.ico" alt="Freelance Tracker PRO" width="100" />
</p>

<h1 align="center">Freelance Tracker PRO</h1>

<p align="center">
  <strong>Real-time freelance project monitoring with native Windows notifications.</strong>
</p>

<p align="center">
  <img src="https://img.shields.io/badge/python-3.10+-3776AB?style=for-the-badge&logo=python&logoColor=white" alt="Python 3.10+" />
  <img src="https://img.shields.io/badge/PySide6-6.5+-41CD52?style=for-the-badge&logo=qt&logoColor=white" alt="PySide6" />
  <img src="https://img.shields.io/badge/platform-Windows_10%2F11-0078D6?style=for-the-badge&logo=windows&logoColor=white" alt="Windows" />
  <img src="https://img.shields.io/badge/license-MIT-blue?style=for-the-badge" alt="License" />
  <img src="https://img.shields.io/badge/build-PyInstaller-orange?style=for-the-badge&logo=pyinstaller&logoColor=white" alt="PyInstaller" />
</p>

<p align="center">
  <img src="https://img.shields.io/badge/status-Production_Ready-brightgreen?style=flat-square" alt="Status" />
  <img src="https://img.shields.io/badge/notifications-Native_Windows-informational?style=flat-square" alt="Notifications" />
  <img src="https://img.shields.io/badge/architecture-Modular-blueviolet?style=flat-square" alt="Architecture" />
</p>

---

## Overview

**Freelance Tracker PRO** is a premium desktop application that monitors leading freelance platforms in real-time and instantly notifies you when new projects matching your interests are posted. Built with Python and PySide6, it features a modern cyber-tech dark UI, native Windows 10/11 toast notifications with clickable links, and a fully threaded background engine that never blocks the interface.

Stop refreshing freelance websites manually. Let Freelance Tracker PRO watch them for you.

---

## Supported Platforms

| Platform | Type | Engine |
|----------|------|--------|
| **Mostaql** | Arabic Freelance Marketplace | HTTP + BeautifulSoup4 |
| **Nafezly** | Arabic Freelance Marketplace | HTTP + BeautifulSoup4 |
| **Truelancer** | International Freelance Platform | Playwright (Headless Browser) |

> More platforms can be added by implementing the `BaseScraper` interface.

---

## Features

### Core
- **Real-Time Monitoring** - Configurable polling interval (10-120 seconds) with intelligent deduplication
- **Native Windows Notifications** - Toast notifications with platform-specific icons and native sound
- **Clickable Notifications** - Click any notification to open the project URL directly in your default browser
- **Background Monitoring** - Fully threaded engine runs in the background without freezing the UI
- **Multi-Platform Scraping** - Simultaneous monitoring of multiple freelance platforms

### Interface
- **Cyber-Tech Dark Mode UI** - Premium glassmorphism design with gradient accents and micro-animations
- **Frameless Window** - Custom title bar with minimize, maximize, and close controls
- **System Tray Support** - Minimize to tray, double-click to restore, tray context menu
- **Platform Toggle Cards** - Enable/disable individual platforms with animated toggle switches
- **Live Project Feed** - Real-time scrolling feed of discovered projects with platform color coding
- **Status Dashboard** - Live uptime counter, project count, and online/offline status indicator

### Technical
- **Settings Persistence** - JSON-based configuration with thread-safe read/write
- **Playwright Integration** - Headless browser scraping for JavaScript-rendered platforms
- **Single-Instance Guard** - Windows mutex prevents duplicate app launches
- **PyInstaller Compatible** - Builds to a standalone `.exe` with all assets bundled
- **Clean Modular Architecture** - Separated core engine, UI layer, and utilities
- **Keyword Filtering** - Optional keyword-based project filtering

---

## Screenshots

> Add your screenshots below.

<!--
<p align="center">
  <img src="docs/screenshots/dashboard.png" alt="Dashboard" width="800" />
</p>

<p align="center">
  <img src="docs/screenshots/notification.png" alt="Notification" width="400" />
</p>

<p align="center">
  <img src="docs/screenshots/settings.png" alt="Settings" width="800" />
</p>
-->

| Dashboard | Settings | Notification |
|-----------|----------|-------------|
| *Screenshot here* | *Screenshot here* | *Screenshot here* |

---

## Architecture

```
Freelance Tracker PRO
├── Presentation Layer (PySide6)
│   ├── MainWindow         Frameless window, page routing, tray
│   ├── TitleBar            Custom title bar with window controls
│   ├── Sidebar             Navigation with active page indicator
│   ├── DashboardPage       Live feed, stats, monitoring controls
│   └── SettingsPage        Configuration panel
│
├── Core Engine
│   ├── MonitorThread       QThread-based polling engine
│   ├── Notifier            Subprocess-based toast notifications
│   └── Scrapers            Platform-specific data extractors
│       ├── BaseScraper     Abstract interface
│       ├── MostaqlScraper  HTTP + BS4
│       ├── NafezlyScraper  HTTP + BS4
│       └── TruelancerScraper  Playwright headless browser
│
└── Utilities
    ├── SettingsManager     Thread-safe JSON persistence
    └── Resources           Asset path resolver (dev + frozen)
```

### Data Flow

```
MonitorThread (QThread)
    │
    ├── Scraper.scrape()  →  [project list]
    │
    ├── Deduplication     →  filter seen projects
    │
    ├── Keyword Filter    →  match user keywords
    │
    ├── Signal: new_project(dict)  →  DashboardPage (GUI update)
    │
    └── Notifier.notify(project)
         │
         └── subprocess  →  toast() + webbrowser.open(url)
```

---

## Technologies

| Technology | Purpose |
|-----------|---------|
| **Python 3.10+** | Core language |
| **PySide6** | Qt6-based GUI framework |
| **Requests** | HTTP client for web scraping |
| **BeautifulSoup4** | HTML parsing and data extraction |
| **Playwright** | Headless browser for JS-rendered pages |
| **win11toast** | Native Windows 10/11 toast notifications |
| **PyInstaller** | Standalone `.exe` packaging |

---

## Installation

### Prerequisites

- Python 3.10 or higher
- Windows 10/11
- Git

### Setup

```bash
# 1. Clone the repository
git clone https://github.com/yourusername/freelance-tracker-pro.git
cd freelance-tracker-pro

# 2. Create a virtual environment
python -m venv venv

# 3. Activate the virtual environment
venv\Scripts\activate

# 4. Install dependencies
pip install -r requirements.txt

# 5. Install Playwright browsers (required for Truelancer)
playwright install chromium

# 6. Run the application
python "Freelance Tracker.py"
```

---

## Build

Build a standalone Windows executable using PyInstaller:

```bash
# Option A: Using the batch script
build.bat

# Option B: Using PowerShell
.\build.ps1
```

The packaged application will be output to:

```
dist\Freelance Tracker\Freelance Tracker.exe
```

> The build bundles all icons, settings, and dependencies into a single distributable folder. No Python installation required on the target machine.

---

## Project Structure

```
freelance-tracker-pro/
│
├── Freelance Tracker.py        # Application entry point
├── requirements.txt            # Python dependencies
├── build.bat                   # Windows batch build script
├── build.ps1                   # PowerShell build script
├── settings.json               # User settings (auto-generated)
│
├── icons/                      # Application and platform icons
│   ├── FWT.ico                 # Main application icon
│   ├── mostaql.ico
│   ├── nafezly.ico
│   ├── kafiil.ico
│   ├── khamsat.ico
│   └── freelanceyard.ico
│
└── src/
    ├── __init__.py
    │
    ├── core/                   # Business logic layer
    │   ├── monitor.py          # QThread monitoring engine
    │   ├── notifier.py         # Windows toast notification handler
    │   └── scrapers/
    │       ├── base.py         # Abstract scraper interface
    │       ├── mostaql.py      # Mostaql scraper (HTTP + BS4)
    │       ├── nafezly.py      # Nafezly scraper (HTTP + BS4)
    │       └── truelancer.py   # Truelancer scraper (Playwright)
    │
    ├── ui/                     # Presentation layer
    │   ├── main_window.py      # Main application window
    │   ├── title_bar.py        # Custom frameless title bar
    │   ├── sidebar.py          # Navigation sidebar
    │   ├── pages/
    │   │   ├── dashboard.py    # Dashboard page
    │   │   └── settings.py     # Settings page
    │   ├── widgets/
    │   │   ├── animated_toggle.py
    │   │   ├── glow_button.py
    │   │   ├── platform_card.py
    │   │   ├── project_card.py
    │   │   └── status_indicator.py
    │   └── styles/
    │       ├── __init__.py
    │       └── theme.py        # Design system (colors, fonts)
    │
    └── utils/                  # Shared utilities
        ├── resources.py        # Asset path resolver
        └── settings_manager.py # JSON settings persistence
```

---

## Configuration

Settings are stored in `settings.json` and can be modified through the Settings page in the GUI:

| Setting | Default | Range | Description |
|---------|---------|-------|-------------|
| `check_interval` | `20` | 10-120s | Polling interval between scrape cycles |
| `notifications_enabled` | `true` | on/off | Enable/disable Windows toast notifications |
| `enabled_platforms` | all | per-platform | Toggle individual platform monitoring |
| `keyword_filter` | `[]` | list | Filter projects by keywords |

---

## Adding a New Platform

1. Create a new scraper in `src/core/scrapers/`:

```python
from src.core.scrapers.base import BaseScraper

class NewPlatformScraper(BaseScraper):
    def scrape(self) -> list:
        # Return list of dicts with: site, title, description, link
        ...
```

2. Register it in `src/core/monitor.py`:

```python
SCRAPER_REGISTRY = {
    ...
    "newplatform": NewPlatformScraper,
}
```

3. Add a platform icon to `icons/` and register it in `src/core/notifier.py`.

---

## Credits

<table>
  <tr>
    <td align="center">
      <strong>ENG Sohib Magdy</strong><br/>
      <em>Creator & Lead Developer & Cyber Security Engineer </em><br/>
      <sub>Architecture, GUI Design, Scraping Engine, Notification System</sub>
    </td>
  </tr>
</table>

---

## License

This project is licensed under the **MIT License**.

```
MIT License

Copyright (c) 2026 Sohib Magdy

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
```

---

<p align="center">
  <strong>Freelance Tracker PRO</strong> &mdash; Never miss a project again.
</p>

<p align="center">
  Built with precision by <strong>Sohib Magdy</strong>
</p>

<p align="center">
  <sub>Made with Python, PySide6, and a passion for automation.</sub>
</p>
