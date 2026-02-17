param(
  [string]$PytestArgs = "-q"
)

$ErrorActionPreference = "Stop"

# Ensure we're running from repo root
if (!(Test-Path ".\pyproject.toml")) {
  throw "test.ps1 must be executed from the repo root (pyproject.toml not found)."
}

# Ensure venv exists
if (!(Test-Path ".\.venv\Scripts\Activate.ps1")) {
  Write-Host "Creating virtual environment (.venv)..." -ForegroundColor Cyan
  python -m venv .venv
}

# Activate venv
. .\.venv\Scripts\Activate.ps1

# Install package + test dependency
Write-Host "Installing package (editable)..." -ForegroundColor Cyan
pip install -e . | Out-Host

Write-Host "Ensuring pytest is installed..." -ForegroundColor Cyan
pip install pytest | Out-Host

# Run tests (python -m avoids PATH/script issues on Windows)
Write-Host "Running tests..." -ForegroundColor Cyan
python -m pytest $PytestArgs
