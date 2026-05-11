@echo off
REM ================================================================
REM  Freelance Tracker PRO — Windows Build Script
REM  Builds a standalone .exe using PyInstaller
REM ================================================================

echo.
echo ========================================
echo  Building Freelance Tracker PRO...
echo ========================================
echo.

REM --- Check Python ---
python --version >nul 2>&1
if errorlevel 1 (
    echo [ERROR] Python is not installed or not in PATH.
    pause
    exit /b 1
)

REM --- Check PyInstaller ---
python -m PyInstaller --version >nul 2>&1
if errorlevel 1 (
    echo [INFO] Installing PyInstaller...
    pip install pyinstaller
)

REM --- Clean old build ---
echo [1/4] Cleaning old build artifacts...
if exist "build" rmdir /s /q "build"
if exist "dist" rmdir /s /q "dist"
if exist "*.spec" del /q "*.spec"

REM --- Install dependencies ---
echo [2/4] Installing dependencies...
pip install -r requirements.txt

REM --- Build executable ---
echo [3/4] Building executable...
python -m PyInstaller ^
    --noconfirm ^
    --onedir ^
    --windowed ^
    --name "Freelance Tracker" ^
    --icon "icons\FWT.ico" ^
    --add-data "icons;icons" ^
    --add-data "settings.json;." ^
    --hidden-import "PySide6.QtWidgets" ^
    --hidden-import "PySide6.QtCore" ^
    --hidden-import "PySide6.QtGui" ^
    --hidden-import "win11toast" ^
    --hidden-import "requests" ^
    --hidden-import "bs4" ^
    --hidden-import "src.core.monitor" ^
    --hidden-import "src.core.notifier" ^
    --hidden-import "src.core.scrapers.base" ^
    --hidden-import "src.core.scrapers.mostaql" ^
    --hidden-import "src.core.scrapers.nafezly" ^
    --hidden-import "src.core.scrapers.truelancer" ^
    --hidden-import "src.ui.main_window" ^
    --hidden-import "src.ui.title_bar" ^
    --hidden-import "src.ui.sidebar" ^
    --hidden-import "src.ui.pages.dashboard" ^
    --hidden-import "src.ui.pages.settings" ^
    --hidden-import "src.ui.widgets.animated_toggle" ^
    --hidden-import "src.ui.widgets.glow_button" ^
    --hidden-import "src.ui.widgets.platform_card" ^
    --hidden-import "src.ui.widgets.project_card" ^
    --hidden-import "src.ui.widgets.status_indicator" ^
    --hidden-import "src.ui.styles.theme" ^
    --hidden-import "src.utils.resources" ^
    --hidden-import "src.utils.settings_manager" ^
    "Freelance Tracker.py"

if errorlevel 1 (
    echo.
    echo [ERROR] Build failed!
    pause
    exit /b 1
)

REM --- Done ---
echo.
echo [4/4] Build complete!
echo.
echo ========================================
echo  Output: dist\Freelance Tracker\
echo  Run:    dist\Freelance Tracker\Freelance Tracker.exe
echo ========================================
echo.
pause
