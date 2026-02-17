from eval_harness.core.runner import run_eval


def test_smoke(tmp_path):
    report_path, summary = run_eval(
        "datasets/sample_tasks.jsonl",
        "prompts/task_extraction/v1.md",
        "schemas/task_extraction.schema.json",
        adapter_name="mock",
        out_dir=str(tmp_path),
    )

    assert report_path.endswith(".json")
    assert summary["total"] > 0
    assert 0.0 <= summary["schema_valid_rate"] <= 1.0
    assert 0.0 <= summary["avg_f1"] <= 1.0
