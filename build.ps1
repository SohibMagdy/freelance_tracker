# ================================================================
#  Freelance Tracker PRO — PowerShell Build Script
#  Builds a standalone .exe using PyInstaller
# ================================================================

Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "  Building Freelance Tracker PRO..."     -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# --- Check Python ---
$pythonCmd = "python"
$pipCmd = "pip"
if (Test-Path "venv\Scripts\python.exe") {
    $pythonCmd = "venv\Scripts\python.exe"
    $pipCmd = "venv\Scripts\pip.exe"
}

try {
    $pythonVersion = & $pythonCmd --version 2>&1
    Write-Host "[OK] $pythonVersion" -ForegroundColor Green
} catch {
    Write-Host "[ERROR] Python is not installed or not in PATH." -ForegroundColor Red
    exit 1
}

# --- Check/Install PyInstaller ---
$pyinstallerCheck = & $pythonCmd -m PyInstaller --version 2>&1
if ($LASTEXITCODE -ne 0) {
    Write-Host "[INFO] Installing PyInstaller..." -ForegroundColor Yellow
    & $pipCmd install pyinstaller
}

# --- Clean old build artifacts ---
Write-Host "[1/4] Cleaning old build artifacts..." -ForegroundColor Yellow
if (Test-Path "build")  { Remove-Item -Recurse -Force "build" }
if (Test-Path "dist")   { Remove-Item -Recurse -Force "dist" }
Get-ChildItem -Filter "*.spec" | Remove-Item -Force -ErrorAction SilentlyContinue

# --- Install dependencies ---
Write-Host "[2/4] Installing dependencies..." -ForegroundColor Yellow
& $pipCmd install -r requirements.txt

# --- Build executable ---
Write-Host "[3/4] Building executable..." -ForegroundColor Yellow

$pyinstallerArgs = @(
    "--noconfirm"
    "--onedir"
    "--windowed"
    '--name', 'Freelance Tracker'
    '--icon', 'icons\FWT.ico'
    '--add-data', 'icons;icons'
    '--collect-all', 'customtkinter'
    '--collect-all', 'pystray'
    '--hidden-import', 'customtkinter'
    '--hidden-import', 'darkdetect'
    '--hidden-import', 'PySide6.QtWidgets'
    '--hidden-import', 'PySide6.QtCore'
    '--hidden-import', 'PySide6.QtGui'
    '--hidden-import', 'win11toast'
    '--hidden-import', 'requests'
    '--hidden-import', 'bs4'
    '--hidden-import', 'PIL'
    '--hidden-import', 'src.core.monitor'
    '--hidden-import', 'src.core.notifier'
    '--hidden-import', 'src.core.scrapers.base'
    '--hidden-import', 'src.core.scrapers.mostaql'
    '--hidden-import', 'src.core.scrapers.nafezly'
    '--hidden-import', 'src.core.scrapers.truelancer'
    '--hidden-import', 'src.ui.main_window'
    '--hidden-import', 'src.ui.title_bar'
    '--hidden-import', 'src.ui.sidebar'
    '--hidden-import', 'src.ui.pages.dashboard'
    '--hidden-import', 'src.ui.pages.settings'
    '--hidden-import', 'src.ui.widgets.animated_toggle'
    '--hidden-import', 'src.ui.widgets.glow_button'
    '--hidden-import', 'src.ui.widgets.platform_card'
    '--hidden-import', 'src.ui.widgets.project_card'
    '--hidden-import', 'src.ui.widgets.status_indicator'
    '--hidden-import', 'src.ui.styles.theme'
    '--hidden-import', 'src.utils.resources'
    '--hidden-import', 'src.utils.settings_manager'
    'Freelance Tracker.py'
)

& $pythonCmd -m PyInstaller @pyinstallerArgs

if ($LASTEXITCODE -ne 0) {
    Write-Host ""
    Write-Host "[ERROR] Build failed!" -ForegroundColor Red
    exit 1
}

# --- Done ---
Write-Host ""
Write-Host "[4/4] Build complete!" -ForegroundColor Green
Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "  Output: dist\Freelance Tracker\"       -ForegroundColor White
Write-Host "  Run:    dist\Freelance Tracker\Freelance Tracker.exe" -ForegroundColor White
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""
