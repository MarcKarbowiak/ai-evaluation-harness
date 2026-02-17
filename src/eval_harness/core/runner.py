from __future__ import annotations

import json
import os
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Tuple

from eval_harness.adapters.mock import MockModel
from eval_harness.adapters.openai_v1 import OpenAIV1Model
from eval_harness.core.dataset import load_jsonl
from eval_harness.core.metrics import exact_match, f1_for_titles
from eval_harness.core.schemas import load_schema, validate_or_errors


def _now_utc_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _require_env(name: str) -> str:
    v = os.environ.get(name, "").strip()
    if not v:
        raise ValueError(f"Missing required environment variable: {name}")
    return v


def _build_adapter(adapter_name: str):
    """
    Adapter factory.

    - mock: offline deterministic adapter (CI-safe)
    - openai: OpenAI public endpoint via OpenAI SDK
    - azure: Azure OpenAI / Foundry OpenAI-compatible v1 endpoint via OpenAI SDK
    """
    if adapter_name == "mock":
        return MockModel()

    if adapter_name == "openai":
        api_key = _require_env("OPENAI_API_KEY")
        model = _require_env("OPENAI_MODEL")
        base_url = os.environ.get("OPENAI_BASE_URL", "").strip() or None  # optional
        return OpenAIV1Model(api_key=api_key, model=model, base_url=base_url)

    if adapter_name == "azure":
        api_key = _require_env("AZURE_OPENAI_API_KEY")
        model = _require_env("AZURE_OPENAI_MODEL")
        base_url = _require_env("AZURE_OPENAI_BASE_URL")
        return OpenAIV1Model(api_key=api_key, model=model, base_url=base_url)

    raise ValueError(f"Unknown adapter: {adapter_name}. Expected one of: mock, openai, azure")


def _jsonable_usage(usage: Any) -> Any:
    """
    Normalize usage objects (some SDKs return Pydantic models or custom objects).
    """
    if usage is None:
        return None
    if isinstance(usage, (dict, list, str, int, float, bool)):
        return usage
    if hasattr(usage, "model_dump"):
        try:
            return usage.model_dump()
        except Exception:
            pass
    if hasattr(usage, "__dict__"):
        try:
            return dict(usage.__dict__)
        except Exception:
            pass
    return str(usage)


def run_eval(
    dataset_path: str,
    prompt_path: str,
    schema_path: str,
    adapter_name: str = "mock",
    out_dir: str = "reports",
) -> Tuple[str, Dict[str, Any]]:
    """
    Run an evaluation over a JSONL dataset using a prompt + JSON schema.

    Returns:
      (report_path, summary_dict)

    Notes:
    - mock adapter is deterministic and should remain the default for CI
    - openai/azure adapters allow realistic runs with environment variables
    """
    cases = load_jsonl(dataset_path)
    prompt = Path(prompt_path).read_text(encoding="utf-8")
    validator = load_schema(schema_path)
    adapter = _build_adapter(adapter_name)

    run_id = f"run-{uuid.uuid4().hex[:8]}"
    started_at_utc = _now_utc_iso()

    results: list[dict] = []
    parse_error_count = 0

    for c in cases:
        model_result = adapter.generate_structured(prompt=prompt, input_obj=c.input)

        output = model_result.output or {}
        if isinstance(output, dict) and output.get("_parse_error") is True:
            parse_error_count += 1

        schema_ok, schema_errors = validate_or_errors(validator, output)

        em = exact_match(output, c.expected)
        f1 = f1_for_titles(output, c.expected)

        results.append(
            {
                "id": c.id,
                "schema_valid": schema_ok,
                "schema_errors": schema_errors,
                "exact_match": em,
                "f1": f1,
                "latency_ms": model_result.latency_ms,
                "usage": _jsonable_usage(getattr(model_result, "usage", None)),
                "cost_usd": getattr(model_result, "cost_usd", None),
            }
        )

    total = len(results)
    denom = total if total > 0 else 1

    summary: Dict[str, Any] = {
        "run_id": run_id,
        "started_at_utc": started_at_utc,
        "adapter": adapter_name,
        "total": total,
        "schema_valid_rate": sum(1 for r in results if r["schema_valid"]) / denom,
        "exact_match_rate": sum(1 for r in results if r["exact_match"]) / denom,
        "avg_f1": (sum(r["f1"] for r in results) / denom) if total else 0.0,
        "avg_latency_ms": (sum(r["latency_ms"] for r in results) / denom) if total else 0.0,
        "parse_error_count": parse_error_count,
    }

    report = {
        "meta": {
            "run_id": run_id,
            "started_at_utc": started_at_utc,
            "adapter": adapter_name,
            "dataset_path": dataset_path,
            "prompt_path": prompt_path,
            "schema_path": schema_path,
        },
        "summary": summary,
        "results": results,
    }

    Path(out_dir).mkdir(parents=True, exist_ok=True)
    out_path = Path(out_dir) / f"{run_id}.json"
    out_path.write_text(
        json.dumps(report, indent=2, ensure_ascii=False),
        encoding="utf-8",
    )

    return str(out_path), summary
