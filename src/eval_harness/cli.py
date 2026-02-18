from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any, Optional

from eval_harness.core.runner import run_eval


def _check_threshold(name: str, actual: float, minimum: Optional[float]) -> list[str]:
    if minimum is None:
        return []
    if actual < minimum:
        return [f"{name} {actual:.3f} < {minimum:.3f}"]
    return []


def _load_baseline_summary(baseline_path: str) -> dict[str, Any]:
    """
    Baseline can be either:
    - a full report JSON (with 'summary' field), OR
    - a summary-only JSON (just the summary object)
    """
    obj = json.loads(Path(baseline_path).read_text(encoding="utf-8"))
    if isinstance(obj, dict) and "summary" in obj and isinstance(obj["summary"], dict):
        return obj["summary"]
    if isinstance(obj, dict) and "schema_valid_rate" in obj:
        return obj
    raise ValueError("Baseline JSON must be a report with 'summary' or a summary-only JSON.")


def _check_regression(
    *,
    baseline: dict[str, Any],
    current: dict[str, Any],
    max_schema_valid_drop: Optional[float],
    max_exact_match_drop: Optional[float],
    max_avg_f1_drop: Optional[float],
) -> list[str]:
    """
    Fail if current metric is worse than baseline by more than the allowed drop.
    Drops are absolute deltas (e.g. 0.02 means allow -2 percentage points).
    """
    failures: list[str] = []

    def getf(d: dict[str, Any], key: str) -> float:
        try:
            return float(d.get(key, 0.0))
        except Exception:
            return 0.0

    # Compare only if drop threshold is provided
    if max_schema_valid_drop is not None:
        b = getf(baseline, "schema_valid_rate")
        c = getf(current, "schema_valid_rate")
        if c < b - max_schema_valid_drop:
            failures.append(
                f"schema_valid_rate regressed: current {c:.3f} < baseline {b:.3f} - {max_schema_valid_drop:.3f}"
            )

    if max_exact_match_drop is not None:
        b = getf(baseline, "exact_match_rate")
        c = getf(current, "exact_match_rate")
        if c < b - max_exact_match_drop:
            failures.append(
                f"exact_match_rate regressed: current {c:.3f} < baseline {b:.3f} - {max_exact_match_drop:.3f}"
            )

    if max_avg_f1_drop is not None:
        b = getf(baseline, "avg_f1")
        c = getf(current, "avg_f1")
        if c < b - max_avg_f1_drop:
            failures.append(
                f"avg_f1 regressed: current {c:.3f} < baseline {b:.3f} - {max_avg_f1_drop:.3f}"
            )

    return failures


def main() -> None:
    parser = argparse.ArgumentParser(
        prog="eval-harness",
        description="Minimal LLM evaluation harness for structured outputs (schema + regression scoring)",
    )
    sub = parser.add_subparsers(dest="cmd", required=True)

    run = sub.add_parser("run", help="Run an evaluation")
    run.add_argument("--dataset", required=True, help="Path to JSONL dataset")
    run.add_argument("--prompt", required=True, help="Path to prompt markdown file")
    run.add_argument("--schema", required=True, help="Path to JSON schema file")
    run.add_argument("--adapter", default="mock", help="Adapter: mock | openai | azure")
    run.add_argument("--out", default="reports", help="Output directory for reports")

    # Quality gates (absolute thresholds)
    run.add_argument(
        "--min-schema-valid-rate",
        type=float,
        default=None,
        help="Fail if schema_valid_rate below this (0..1).",
    )
    run.add_argument(
        "--min-exact-match-rate",
        type=float,
        default=None,
        help="Fail if exact_match_rate below this (0..1).",
    )
    run.add_argument(
        "--min-avg-f1", type=float, default=None, help="Fail if avg_f1 below this (0..1)."
    )
    run.add_argument(
        "--fail-on-empty", action="store_true", help="Fail if dataset contains zero cases."
    )

    # Baseline regression gates
    run.add_argument("--baseline", default=None, help="Path to baseline JSON (report or summary).")
    run.add_argument(
        "--max-schema-valid-drop",
        type=float,
        default=None,
        help="Fail if schema_valid_rate drops vs baseline by more than this.",
    )
    run.add_argument(
        "--max-exact-match-drop",
        type=float,
        default=None,
        help="Fail if exact_match_rate drops vs baseline by more than this.",
    )
    run.add_argument(
        "--max-avg-f1-drop",
        type=float,
        default=None,
        help="Fail if avg_f1 drops vs baseline by more than this.",
    )

    # Baseline writer (optional convenience)
    run.add_argument(
        "--write-baseline",
        default=None,
        help="Write current summary to this JSON path (summary-only).",
    )

    args = parser.parse_args()

    if args.cmd == "run":
        report_path, summary = run_eval(
            dataset_path=args.dataset,
            prompt_path=args.prompt,
            schema_path=args.schema,
            adapter_name=args.adapter,
            out_dir=args.out,
        )

        print(f"Wrote report: {report_path}")
        print(
            "Summary:",
            f"total={summary.get('total')}, "
            f"schema_valid_rate={summary.get('schema_valid_rate'):.3f}, "
            f"exact_match_rate={summary.get('exact_match_rate'):.3f}, "
            f"avg_f1={summary.get('avg_f1'):.3f}, "
            f"avg_latency_ms={summary.get('avg_latency_ms'):.1f}",
        )

        failures: list[str] = []

        # Absolute threshold gates
        if args.fail_on_empty and int(summary.get("total", 0)) == 0:
            failures.append("dataset is empty (total=0)")

        failures += _check_threshold(
            "schema_valid_rate",
            float(summary.get("schema_valid_rate", 0.0)),
            args.min_schema_valid_rate,
        )
        failures += _check_threshold(
            "exact_match_rate",
            float(summary.get("exact_match_rate", 0.0)),
            args.min_exact_match_rate,
        )
        failures += _check_threshold("avg_f1", float(summary.get("avg_f1", 0.0)), args.min_avg_f1)

        # Baseline regression gates (optional)
        if args.baseline:
            baseline_summary = _load_baseline_summary(args.baseline)
            failures += _check_regression(
                baseline=baseline_summary,
                current=summary,
                max_schema_valid_drop=args.max_schema_valid_drop,
                max_exact_match_drop=args.max_exact_match_drop,
                max_avg_f1_drop=args.max_avg_f1_drop,
            )

        # Write baseline summary if requested
        if args.write_baseline:
            Path(args.write_baseline).parent.mkdir(parents=True, exist_ok=True)
            Path(args.write_baseline).write_text(json.dumps(summary, indent=2), encoding="utf-8")
            print(f"Wrote baseline summary: {args.write_baseline}")

        if failures:
            print("QUALITY GATE FAILED:")
            for f in failures:
                print(f" - {f}")
            sys.exit(2)


if __name__ == "__main__":
    main()
