import sys

import pytest

from eval_harness.cli import main


def test_cli_quality_gate_fails(monkeypatch):
    # Make it impossible to pass: avg_f1 must be 1.1 (out of range)
    argv = [
        "eval-harness",
        "run",
        "--dataset",
        "datasets/sample_tasks.jsonl",
        "--prompt",
        "prompts/task_extraction/v1.md",
        "--schema",
        "schemas/task_extraction.schema.json",
        "--adapter",
        "mock",
        "--min-schema-valid-rate",
        "1.0",
        "--min-avg-f1",
        "1.1",
        "--out",
        "reports",
    ]
    monkeypatch.setattr(sys, "argv", argv)

    with pytest.raises(SystemExit) as ex:
        main()

    assert ex.value.code == 2


def test_cli_quality_gate_passes(monkeypatch, tmp_path):
    argv = [
        "eval-harness",
        "run",
        "--dataset",
        "datasets/sample_tasks.jsonl",
        "--prompt",
        "prompts/task_extraction/v1.md",
        "--schema",
        "schemas/task_extraction.schema.json",
        "--adapter",
        "mock",
        "--min-schema-valid-rate",
        "1.0",
        "--min-avg-f1",
        "0.0",
        "--out",
        str(tmp_path),
    ]
    monkeypatch.setattr(sys, "argv", argv)

    # Should not raise SystemExit
    main()
