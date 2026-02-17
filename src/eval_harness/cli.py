from __future__ import annotations

import argparse
import sys
from typing import Optional

from eval_harness.core.runner import run_eval


def _check_threshold(name: str, actual: float, minimum: Optional[float]) -> list[str]:
    if minimum is None:
        return []
    if actual < minimum:
        return [f"{name} {actual:.3f} < {minimum:.3f}"]
    return []


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

    # Quality gates (optional)
    run.add_argument(
        "--min-schema-valid-rate",
        type=float,
        default=None,
        help="Fail if schema_valid_rate is below this threshold (0..1).",
    )
    run.add_argument(
        "--min-exact-match-rate",
        type=float,
        default=None,
        help="Fail if exact_match_rate is below this threshold (0..1).",
    )
    run.add_argument(
        "--min-avg-f1",
        type=float,
        default=None,
        help="Fail if avg_f1 is below this threshold (0..1).",
    )
    run.add_argument(
        "--fail-on-empty",
        action="store_true",
        help="Fail if the dataset contains zero cases.",
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
        failures += _check_threshold(
            "avg_f1",
            float(summary.get("avg_f1", 0.0)),
            args.min_avg_f1,
        )

        if failures:
            print("QUALITY GATE FAILED:")
            for f in failures:
                print(f" - {f}")
            sys.exit(2)
