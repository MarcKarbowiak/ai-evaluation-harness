param(
  [string]$PyrightArgs = ""
)

$ErrorActionPreference = "Stop"

# Ensure we're running from repo root
if (!(Test-Path ".\pyproject.toml")) {
  throw "typecheck.ps1 must be executed from the repo root (pyproject.toml not found)."
}

# Ensure venv exists
if (!(Test-Path ".\.venv\Scripts\Activate.ps1")) {
  Write-Host "Creating virtual environment (.venv)..." -ForegroundColor Cyan
  python -m venv .venv
}

# Activate venv
. .\.venv\Scripts\Activate.ps1

# Install package + dev dependencies (pyright)
Write-Host "Installing package + dev deps (editable)..." -ForegroundColor Cyan
pip install -e ".[dev]" | Out-Host

Write-Host "Running Pyright..." -ForegroundColor Cyan
python -m pyright $PyrightArgs
