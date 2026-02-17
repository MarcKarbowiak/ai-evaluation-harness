param(
  [ValidateSet("mock","openai","azure")]
  [string]$Adapter = "mock",

  [string]$Dataset = "datasets\sample_tasks.jsonl",
  [string]$PromptPath  = "prompts\task_extraction\v1.md",
  [string]$SchemaPath  = "schemas\task_extraction.schema.json",

  # Quality gates (optional)
  [Nullable[double]]$MinSchemaValidRate = 1.0,
  [Nullable[double]]$MinAvgF1 = 0.8,

  # Baseline regression (optional)
  [string]$Baseline = "baselines\task_extraction.mock.baseline.json",
  [Nullable[double]]$MaxAvgF1Drop = 0.02,

  # Write baseline (optional)
  [switch]$WriteBaseline
)

$ErrorActionPreference = "Stop"

# Ensure we're running from repo root (where pyproject.toml lives)
if (!(Test-Path ".\pyproject.toml")) {
  throw "run.ps1 must be executed from the repo root (pyproject.toml not found)."
}

# Ensure venv exists
if (!(Test-Path ".\.venv\Scripts\Activate.ps1")) {
  Write-Host "Creating virtual environment (.venv)..." -ForegroundColor Cyan
  python -m venv .venv
}

# Activate venv
. .\.venv\Scripts\Activate.ps1

# Install dependencies + editable package
Write-Host "Installing package (editable)..." -ForegroundColor Cyan
pip install -e . | Out-Host

# Build command args
$argsList = @(
  "-m", "eval_harness.cli", "run",
  "--dataset", $Dataset,
  "--prompt",  $PromptPath,
  "--schema",  $SchemaPath,
  "--adapter", $Adapter,
  "--out",     "reports"
)

if ($MinSchemaValidRate -ne $null) { $argsList += @("--min-schema-valid-rate", "$MinSchemaValidRate") }
if ($MinAvgF1 -ne $null)           { $argsList += @("--min-avg-f1", "$MinAvgF1") }

# Baseline regression gates only if the baseline file exists and WriteBaseline is not set
if (-not $WriteBaseline) {
  if ($Baseline -and (Test-Path $Baseline)) {
    $argsList += @("--baseline", $Baseline)
    if ($MaxAvgF1Drop -ne $null) { $argsList += @("--max-avg-f1-drop", "$MaxAvgF1Drop") }
  } else {
    Write-Host "Baseline file not found ($Baseline). Skipping baseline regression check." -ForegroundColor Yellow
  }
}

# Write baseline if requested
if ($WriteBaseline) {
  # Ensure baselines folder exists
  $baselineDir = Split-Path $Baseline -Parent
  if ($baselineDir -and !(Test-Path $baselineDir)) { New-Item -ItemType Directory -Path $baselineDir | Out-Null }
  $argsList += @("--write-baseline", $Baseline)
}

Write-Host "Dataset: $Dataset"
Write-Host "Prompt:  $PromptPath"
Write-Host "Schema:  $SchemaPath"
Write-Host "Adapter: $Adapter"
Write-Host "Baseline:$Baseline"

if (!(Test-Path $Dataset)) { throw "Dataset not found: $Dataset" }
if (!(Test-Path $PromptPath)) { throw "Prompt not found: $PromptPath" }
if (!(Test-Path $SchemaPath)) { throw "Schema not found: $SchemaPath" }

Write-Host "Running eval harness..." -ForegroundColor Cyan
& python @argsList

if ($WriteBaseline -and !(Test-Path $Baseline)) {
  Write-Host "ERROR: Baseline was NOT created at: $Baseline" -ForegroundColor Red
  exit 1
}
