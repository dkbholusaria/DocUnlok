# DocUnlok - Windows Setup & Build Script
# Run from PowerShell: .\scripts\setup_and_build.ps1
# Produces a standalone dist\DocUnlok.exe (no installer).

$SCRIPT_DIR = $PSScriptRoot
$PROJECT_ROOT = Split-Path -Parent $SCRIPT_DIR

Write-Host ""
Write-Host "========================================================"
Write-Host "  DocUnlok - Setup & Build"
Write-Host "  $(Get-Date -Format 'yyyy-MM-dd HH:mm:ss')"
Write-Host "========================================================"
Write-Host ""

Set-Location $PROJECT_ROOT
Write-Host "  Working dir: $(Get-Location)"

$versionMatch = Select-String -Path "version.py" -Pattern '__version__\s*=\s*"(.+?)"'
$AppVersion = $versionMatch.Matches.Groups[1].Value
if (-not $AppVersion) { $AppVersion = "dev" }
Write-Host "  Version    : $AppVersion"

# ── Step 1: Create venv ───────────────────────────────────────────
Write-Host ""
Write-Host "--------------------------------------------------------"
Write-Host "[Step 1] Python virtual environment"
Write-Host "--------------------------------------------------------"

$VENV   = "$PROJECT_ROOT\.venv"
$PYTHON = "$VENV\Scripts\python.exe"
$PIP    = "$VENV\Scripts\pip.exe"

if (-not (Test-Path $PYTHON)) {
    Write-Host "  Creating new venv at $VENV ..."
    python -m venv $VENV
    if ($LASTEXITCODE -ne 0) { Write-Host "[Error] Failed to create virtual environment."; exit 1 }
} else {
    Write-Host "  Venv already exists - skipping creation."
}

# ── Step 2: Install dependencies ─────────────────────────────────
Write-Host ""
Write-Host "--------------------------------------------------------"
Write-Host "[Step 2] Installing dependencies"
Write-Host "--------------------------------------------------------"
& $PIP install -r requirements.txt
if ($LASTEXITCODE -ne 0) { Write-Host "[Error] pip install failed."; exit 1 }

Write-Host "  Installing build tools (nuitka, ordered-set, zstandard)..."
& $PIP install nuitka ordered-set zstandard
if ($LASTEXITCODE -ne 0) { Write-Host "[Error] Failed to install build tools."; exit 1 }
Write-Host "[OK] Dependencies installed."

# ── Step 3: Nuitka build ──────────────────────────────────────────
Write-Host ""
Write-Host "--------------------------------------------------------"
Write-Host "[Step 3] Nuitka compilation"
Write-Host "--------------------------------------------------------"
Write-Host "  Output: dist\DocUnlok.exe"
Write-Host ""

$iconArg = @()
if (Test-Path "resources\app_icon.ico") {
    $iconArg = @("--windows-icon-from-ico=resources\app_icon.ico")
}

& $PYTHON -m nuitka `
    --standalone `
    --onefile `
    --windows-console-mode=disable `
    --output-dir=dist `
    --output-filename=DocUnlok.exe `
    --enable-plugin=pyqt6 `
    --assume-yes-for-downloads `
    @iconArg `
    app.py

if ($LASTEXITCODE -ne 0) { Write-Host "[Error] Nuitka compilation failed."; exit 1 }

$exeSize = [math]::Round((Get-Item "dist\DocUnlok.exe").Length / 1MB, 1)
Write-Host ""
Write-Host "========================================================"
Write-Host "  Build complete! $(Get-Date -Format 'HH:mm:ss')"
Write-Host "========================================================"
Write-Host "  Executable: dist\DocUnlok.exe (${exeSize} MB)"
Write-Host "========================================================"
