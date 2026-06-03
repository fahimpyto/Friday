param(
    [switch]$NoEnv
)

$ErrorActionPreference = "Stop"
$ProjectRoot = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location -LiteralPath $ProjectRoot

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "   Friday v0.1 - Setup Script (Windows)" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# --- Python check ---
$py = (Get-Command python -ErrorAction SilentlyContinue).Source
if (-not $py) {
    $py = (Get-Command python3 -ErrorAction SilentlyContinue).Source
}
if (-not $py) {
    Write-Host "[ERROR] Python not found. Install Python 3.10+ and try again." -ForegroundColor Red
    exit 1
}
Write-Host "[OK] Python: $((& $py --version 2>&1).Trim())" -ForegroundColor Green

# --- Virtual environment ---
if (-not (Test-Path -LiteralPath "venv")) {
    Write-Host "Creating virtual environment..." -ForegroundColor Yellow
    & $py -m venv venv
    if (-not $?) { exit 1 }
    Write-Host "[OK] venv/ created" -ForegroundColor Green
} else {
    Write-Host "[OK] venv/ already exists" -ForegroundColor Green
}

# --- Activate and install ---
$pip = Join-Path $ProjectRoot "venv\Scripts\pip.exe"
$python = Join-Path $ProjectRoot "venv\Scripts\python.exe"

Write-Host "Installing Python dependencies..." -ForegroundColor Yellow
& $pip install --upgrade pip
& $pip install -r requirements.txt
if (-not $?) { exit 1 }
Write-Host "[OK] Dependencies installed" -ForegroundColor Green

# --- .env file ---
if (-not (Test-Path -LiteralPath ".env")) {
    if (Test-Path -LiteralPath ".env.example") {
        Copy-Item -LiteralPath ".env.example" -Destination ".env"
        Write-Host "[WARN] .env created from .env.example. Edit it to add your OPENROUTER_API_KEY." -ForegroundColor Yellow
    }
} else {
    Write-Host "[OK] .env already exists" -ForegroundColor Green
}

# --- Tesseract check ---
$tesseract = (Get-Command tesseract -ErrorAction SilentlyContinue).Source
if ($tesseract) {
    Write-Host "[OK] Tesseract OCR found: $((& $tesseract --version 2>&1 | Select-Object -First 1).Trim())" -ForegroundColor Green
} else {
    Write-Host "[WARN] Tesseract OCR not found. Scanned PDFs will not work." -ForegroundColor Yellow
    Write-Host "       Download from: https://github.com/UB-Mannheim/tesseract/wiki" -ForegroundColor Yellow
    Write-Host "       Or install via Chocolatey: choco install tesseract" -ForegroundColor Yellow
}

Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "   Setup complete!" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "Activate the environment:" -ForegroundColor White
Write-Host "  .\venv\Scripts\Activate" -ForegroundColor Green
Write-Host ""
Write-Host "Start the agent:" -ForegroundColor White
Write-Host "  python -m src.main" -ForegroundColor Green
Write-Host "  (or: python src\main.py)" -ForegroundColor Green
Write-Host ""
Write-Host "Edit .env to set your OPENROUTER_API_KEY before running." -ForegroundColor Yellow
