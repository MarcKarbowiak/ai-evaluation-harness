# AI Evaluation Harness (Minimal, Production-Minded)

A lightweight evaluation harness for LLM features that produce structured outputs (JSON).
Designed for regression testing, schema validation, deterministic scoring, and CI integration.

## Features
- Prompt versioning
- JSON Schema validation
- Structured output scoring (exact match + F1 on task titles)
- Offline mock adapter (CI friendly)
- JSON run reports

## Quickstart

```bash
python -m venv .venv
source .venv/bin/activate
pip install -e .
eval-harness run --dataset datasets/sample_tasks.jsonl   --prompt prompts/task_extraction/v1.md   --schema schemas/task_extraction.schema.json   --adapter mock
```
