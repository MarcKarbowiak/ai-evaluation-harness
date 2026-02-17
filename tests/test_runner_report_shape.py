import json
from pathlib import Path

from eval_harness.core.runner import run_eval


def test_runner_writes_report_and_summary(tmp_path):
    report_path, summary = run_eval(
        "datasets/sample_tasks.jsonl",
        "prompts/task_extraction/v1.md",
        "schemas/task_extraction.schema.json",
        adapter_name="mock",
        out_dir=str(tmp_path),
    )

    assert report_path.endswith(".json")
    assert summary["total"] > 0
    assert summary["adapter"] == "mock"

    report_obj = json.loads(Path(report_path).read_text(encoding="utf-8"))
    assert "meta" in report_obj
    assert "summary" in report_obj
    assert "results" in report_obj

    assert report_obj["summary"]["total"] == summary["total"]
    assert isinstance(report_obj["results"], list)
    assert len(report_obj["results"]) == summary["total"]
