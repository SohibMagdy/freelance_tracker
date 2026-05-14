@echo off
REM ================================================================
REM  Freelance Tracker PRO — Windows Build Script
REM  Builds a standalone .exe using PyInstaller (CustomTkinter)
REM ================================================================

echo.
echo ========================================
echo  Building Freelance Tracker PRO...
echo ========================================
echo.

REM --- Check Python ---
if exist "venv\Scripts\python.exe" (
    set PYTHON_CMD=venv\Scripts\python.exe
    set PIP_CMD=venv\Scripts\pip.exe
) else (
    set PYTHON_CMD=python
    set PIP_CMD=pip
)

%PYTHON_CMD% --version >nul 2>&1
if errorlevel 1 (
    echo [ERROR] Python is not installed or not in PATH.
    pause
    exit /b 1
)

REM --- Check PyInstaller ---
%PYTHON_CMD% -m PyInstaller --version >nul 2>&1
if errorlevel 1 (
    echo [INFO] Installing PyInstaller...
    %PIP_CMD% install pyinstaller
)

REM --- Clean old build ---
echo [1/4] Cleaning old build artifacts...
if exist "build" rmdir /s /q "build"
if exist "dist" rmdir /s /q "dist"
if exist "*.spec" del /q "*.spec"

REM --- Install dependencies ---
echo [2/4] Installing dependencies...
%PIP_CMD% install -r requirements.txt

REM --- Build executable ---
echo [3/4] Building executable...
%PYTHON_CMD% -m PyInstaller ^
    --noconfirm ^
    --onefile ^
    --windowed ^
    --name "Freelance Tracker" ^
    --icon "icons\FWT.ico" ^
    --add-data "icons;icons" ^
    --collect-all "customtkinter" ^
    --collect-all "pystray" ^
    --hidden-import "customtkinter" ^
    --hidden-import "darkdetect" ^
    --hidden-import "win11toast" ^
    --hidden-import "requests" ^
    --hidden-import "bs4" ^
    --hidden-import "PIL" ^
    --hidden-import "src.core.monitor" ^
    --hidden-import "src.core.notifier" ^
    --hidden-import "src.core.scrapers.base" ^
    --hidden-import "src.core.scrapers.mostaql" ^
    --hidden-import "src.core.scrapers.nafezly" ^
    --hidden-import "src.core.scrapers.truelancer" ^
    --hidden-import "src.ui.main_window" ^
    --hidden-import "src.ui.sidebar" ^
    --hidden-import "src.ui.pages.dashboard" ^
    --hidden-import "src.ui.pages.settings" ^
    --hidden-import "src.ui.widgets.platform_card" ^
    --hidden-import "src.ui.widgets.project_card" ^
    --hidden-import "src.ui.styles.colors" ^
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
