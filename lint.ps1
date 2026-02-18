param(
  [string]$RuffArgs = ""
)

$ErrorActionPreference = "Stop"

# Ensure we're running from repo root
if (!(Test-Path ".\pyproject.toml")) {
  throw "lint.ps1 must be executed from the repo root (pyproject.toml not found)."
}

# Ensure venv exists
if (!(Test-Path ".\.venv\Scripts\Activate.ps1")) {
  Write-Host "Creating virtual environment (.venv)..." -ForegroundColor Cyan
  python -m venv .venv
}

# Activate venv
. .\.venv\Scripts\Activate.ps1

# Install package + dev dependencies (ruff)
Write-Host "Installing package + dev deps (editable)..." -ForegroundColor Cyan
pip install -e ".[dev]" | Out-Host

Write-Host "Running Ruff lint..." -ForegroundColor Cyan
python -m ruff check . $RuffArgs

Write-Host "Running Ruff format check..." -ForegroundColor Cyan
python -m ruff format --check .
