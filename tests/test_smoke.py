from eval_harness.core.runner import run_eval

def test_smoke(tmp_path):
    report = run_eval(
        "datasets/sample_tasks.jsonl",
        "prompts/task_extraction/v1.md",
        "schemas/task_extraction.schema.json"
    )
    assert report.endswith(".json")
