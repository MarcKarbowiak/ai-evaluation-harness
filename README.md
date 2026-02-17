# AI Evaluation Harness (Minimal, Production-Minded)

[![CI](https://github.com/marckarbowiak/ai-evaluation-harness/actions/workflows/ci.yml/badge.svg)](https://github.com/marckarbowiak/ai-evaluation-harness/actions/workflows/ci.yml)

A lightweight evaluation harness for LLM features that produce **structured outputs (JSON)**.

It provides **schema validation**, **regression scoring**, **quality gates**, and **baseline regression checks** so you can treat AI features like production software: measurable, repeatable, and safe to ship.

---

## What this harness is for

AI-powered features (extraction, classification, summarization-to-JSON, etc.) regress easily when:

- prompts change
- models are upgraded
- temperature / decoding settings change
- RAG/retrieval or chunking changes
- schemas evolve

This harness helps you detect regressions early by running a consistent dataset through a prompt+model and measuring:

- **Schema validity** (output must conform to JSON schema)
- **Correctness metrics** (e.g., exact match / F1)
- **Run metadata** (latency, usage/cost placeholders)
- **Baseline regression** (compare against “known good” results)

---

## Features

### Core
- **Dataset-driven evaluation** (`datasets/*.jsonl`)
- **Prompt versioning** (`prompts/<capability>/vN.md`)
- **JSON Schema enforcement** (`schemas/*.schema.json`)
- **Metrics** (exact match + F1 on extracted task titles)
- **Run reports** written to `reports/` (JSON)

### Quality gates
- Fail the run (exit code 2) if metrics drop below thresholds:
  - `--min-schema-valid-rate`
  - `--min-exact-match-rate`
  - `--min-avg-f1`

### Baseline regression checks
- Compare current run metrics against a committed baseline:
  - `--baseline baselines/...json`
  - `--max-avg-f1-drop` (and similar options)

### Model adapters
- `mock` adapter: deterministic, offline, CI-safe
- `openai` / `azure` adapters (OpenAI-compatible v1): realistic runs against OpenAI or Azure OpenAI / Azure AI Foundry endpoints

---

## Repository layout

```text
ai-evaluation-harness/
  .github/workflows/ci.yml
  baselines/
  datasets/
  prompts/
  reports/
  schemas/
  src/eval_harness/
  tests/
  run.ps1
```

---

flowchart LR
  D["Dataset<br/>(JSONL)"] --> R["Runner"]
  P["Prompt<br/>(vN)"] --> R
  R --> A["Adapter<br/>mock/openai/azure"]
  A --> O["Output<br/>(JSON)"]

  S["JSON Schema"] --> V["Schema Validation"]
  O --> V

  O --> M["Scoring<br/>Exact match + F1"]
  V --> M

  B["Baseline"] --> G["Regression Gates"]
  M --> G

  G --> RPT["Report<br/>(JSON)"]

---

## Quickstart (Windows / PowerShell)

This repo includes a PowerShell wrapper (`run.ps1`) that:
- ensures a local venv exists (`.venv`)
- activates it
- installs the package in editable mode
- runs the harness with quality gates
- optionally enforces baseline regression checks

### Run (mock adapter, CI-safe)
From repo root:

```powershell
.\run.ps1
```

This uses:
- `Adapter = mock`
- default sample dataset/prompt/schema
- quality gates (schema validity + avg F1)

---

## `run.ps1` options (all supported parameters)

You can override inputs, gates, baseline, and adapter.

### Parameters

| Parameter | Default | Description |
|---|---:|---|
| `-Adapter` | `mock` | `mock`, `openai`, or `azure` |
| `-Dataset` | `datasets\sample_tasks.jsonl` | JSONL evaluation dataset |
| `-Prompt` | `prompts\task_extraction\v1.md` | Prompt file used for evaluation |
| `-Schema` | `schemas\task_extraction.schema.json` | JSON schema enforced on outputs |
| `-MinSchemaValidRate` | `1.0` | Fail if schema-valid rate below this |
| `-MinAvgF1` | `0.8` | Fail if average F1 below this |
| `-Baseline` | `baselines\task_extraction.mock.baseline.json` | Baseline summary/report to compare against |
| `-MaxAvgF1Drop` | `0.02` | Allowed regression vs baseline (absolute delta) |
| `-WriteBaseline` | (switch) | Writes current summary to baseline path |

> Notes
> - If the baseline file **does not exist** and `-WriteBaseline` is not set, `run.ps1` will **skip** baseline regression checks.
> - Baselines are **never** updated automatically; baseline updates are explicit via `-WriteBaseline`.

---

## Example commands

### 1) Run with defaults

```powershell
.\run.ps1
```

### 2) Run with stricter gates

```powershell
.\run.ps1 -MinAvgF1 0.9 -MinSchemaValidRate 1.0
```

### 3) Use a different dataset/prompt/schema

```powershell
.\run.ps1 `
  -Dataset "datasets\my_cases.jsonl" `
  -Prompt  "prompts\task_extraction\v2.md" `
  -Schema  "schemas\task_extraction.schema.json"
```

### 4) Create or update the baseline (explicit)

```powershell
.\run.ps1 -WriteBaseline
```

This writes a summary JSON to:

- `baselines\task_extraction.mock.baseline.json`

Commit that file to version-control the expected performance.

### 5) Run with baseline regression checks (prevent degradation)

If the baseline exists, this will fail if the current average F1 drops by more than the allowed delta.

```powershell
.\run.ps1 -Baseline "baselines\task_extraction.mock.baseline.json" -MaxAvgF1Drop 0.02
```

### 6) Run against Azure OpenAI / Foundry (real model)

Set env vars, then run:

```powershell
$env:AZURE_OPENAI_API_KEY="..."
$env:AZURE_OPENAI_BASE_URL="https://YOUR-RESOURCE.openai.azure.com/openai/v1/"
$env:AZURE_OPENAI_MODEL="YOUR_MODEL_OR_DEPLOYMENT"

.\run.ps1 -Adapter azure
```

### 7) Run against OpenAI public endpoint (real model)

```powershell
$env:OPENAI_API_KEY="..."
$env:OPENAI_MODEL="gpt-4.1-mini"  # example
# optional:
# $env:OPENAI_BASE_URL="https://api.openai.com/v1"

.\run.ps1 -Adapter openai
```

---

## Baselines: what they are and why they matter

### What is a baseline?
A baseline is a **version-controlled “known good” reference** for the evaluation summary (or a full report).

It represents:
- acceptable output quality
- measured on a fixed dataset
- for a specific capability (e.g., task extraction)

### Why use baselines?
Quality gates (`--min-avg-f1`, etc.) ensure you meet a minimum bar.

Baselines ensure you **don’t silently degrade** over time even if you remain above the minimum bar.

Example:
- Minimum avg F1 is 0.80
- Baseline avg F1 is 0.92

A change that drops you to 0.83 technically passes the minimum gate, but it’s a regression.

Baseline regression checks catch this.

### How baseline regression prevents degradation
When you run with:

- `--baseline baselines/...json`
- `--max-avg-f1-drop 0.02`

the harness will fail if:

`current_avg_f1 < baseline_avg_f1 - 0.02`

This keeps quality from drifting down slowly.

---

## When to update the baseline (important)

Update the baseline **only** when you intentionally accept a new quality level.

### Good reasons to update baseline
- You improved a prompt and quality measurably improved
- You expanded the schema and updated expected outputs accordingly
- You changed the dataset intentionally (new edge cases) and the new baseline reflects the expanded coverage
- You switched models intentionally and want to treat the new behavior as the standard

### Bad reasons to update baseline
- “The build is failing and I want it green”
- “Quality got worse but it’s still above the minimum”

Baseline updates should be treated like test snapshot updates:
- deliberate
- reviewed
- justified in the PR description

---

## Recommended baseline workflow

1. **Add/adjust dataset cases** (especially edge cases)
2. Run locally with real adapter (optional) and mock adapter (required)
3. If changes are intended and acceptable:
   - run `-WriteBaseline`
   - commit baseline changes
4. Keep CI enforcing:
   - minimum gates
   - baseline regression tolerances

---

## CI behavior

- CI always runs:
  - unit tests
  - mock adapter quality gate
  - uploads `reports/` as artifacts

- The Azure “real gate” job runs only if required secrets are configured in the repo.

---

## Notes on extending this harness

Common next steps (kept intentionally out of v1):
- per-tag thresholds (happy-path vs edge-case)
- baseline diff report (per-case regressions)
- cost caps (max tokens / max cost per run)
- multi-prompt comparisons (A/B)

If you add those, keep the same philosophy: small, auditable, and easy to embed into product repos.

