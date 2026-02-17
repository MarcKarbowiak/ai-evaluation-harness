import os
import pytest

from eval_harness.core.runner import run_eval


def test_openai_adapter_requires_env(monkeypatch, tmp_path):
    # Clear env vars (simulate CI without secrets)
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    monkeypatch.delenv("OPENAI_MODEL", raising=False)
    monkeypatch.delenv("OPENAI_BASE_URL", raising=False)

    with pytest.raises(ValueError) as ex:
        run_eval(
            "datasets/sample_tasks.jsonl",
            "prompts/task_extraction/v1.md",
            "schemas/task_extraction.schema.json",
            adapter_name="openai",
            out_dir=str(tmp_path),
        )
    assert "OPENAI_API_KEY" in str(ex.value) or "OPENAI_MODEL" in str(ex.value)


def test_azure_adapter_requires_env(monkeypatch, tmp_path):
    monkeypatch.delenv("AZURE_OPENAI_API_KEY", raising=False)
    monkeypatch.delenv("AZURE_OPENAI_MODEL", raising=False)
    monkeypatch.delenv("AZURE_OPENAI_BASE_URL", raising=False)

    with pytest.raises(ValueError) as ex:
        run_eval(
            "datasets/sample_tasks.jsonl",
            "prompts/task_extraction/v1.md",
            "schemas/task_extraction.schema.json",
            adapter_name="azure",
            out_dir=str(tmp_path),
        )
    msg = str(ex.value)
    assert "AZURE_OPENAI_API_KEY" in msg or "AZURE_OPENAI_MODEL" in msg or "AZURE_OPENAI_BASE_URL" in msg
