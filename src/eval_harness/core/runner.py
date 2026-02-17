import json
import uuid
from pathlib import Path
from eval_harness.adapters.mock import MockModel
from eval_harness.core.dataset import load_jsonl
from eval_harness.core.metrics import exact_match, f1_for_titles
from eval_harness.core.schemas import load_schema, validate_or_errors

ADAPTERS = {"mock": MockModel}

def run_eval(dataset_path, prompt_path, schema_path, adapter_name="mock", out_dir="reports"):
    cases = load_jsonl(dataset_path)
    prompt = Path(prompt_path).read_text(encoding="utf-8")
    validator = load_schema(schema_path)
    adapter = ADAPTERS[adapter_name]()

    results = []
    for c in cases:
        result = adapter.generate_structured(prompt=prompt, input_obj=c.input)
        ok, errors = validate_or_errors(validator, result.output)
        results.append({
            "id": c.id,
            "schema_valid": ok,
            "exact_match": exact_match(result.output, c.expected),
            "f1": f1_for_titles(result.output, c.expected),
            "latency_ms": result.latency_ms,
        })

    summary = {
        "total": len(results),
        "schema_valid_rate": sum(r["schema_valid"] for r in results)/len(results),
        "exact_match_rate": sum(r["exact_match"] for r in results)/len(results),
        "avg_f1": sum(r["f1"] for r in results)/len(results),
    }

    run_id = f"run-{uuid.uuid4().hex[:8]}"
    Path(out_dir).mkdir(exist_ok=True)
    out_path = Path(out_dir) / f"{run_id}.json"
    out_path.write_text(json.dumps({"summary": summary, "results": results}, indent=2))
    return str(out_path)
