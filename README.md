# AI Evaluation Harness (Minimal, Production-Minded)

A lightweight evaluation harness for LLM features that produce **structured outputs** (JSON).
Designed for:
- regression testing prompts + models
- schema validation
- deterministic scoring where possible
- repeatable runs with traceability (latency, token/cost placeholders)

This repo intentionally avoids being “framework-heavy”.
It’s meant to be embedded into product repos or used as a standalone quality gate.

---

## What this supports (v1)
- Prompt versioning (simple registry)
- JSON Schema validation
- Exact-match / key-level metrics for structured outputs
- Run reports (JSON) + run metadata
- Offline-friendly by default (MockModel adapter)
- CI-ready

---

## Quickstart

### 1) Setup
```bash
make venv
source .venv/bin/activate
make install
