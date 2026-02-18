from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any


@dataclass(frozen=True)
class DatasetCase:
    id: str
    input: dict[str, Any]
    expected: dict[str, Any]
    meta: dict[str, Any]


def load_jsonl(path: str) -> list[DatasetCase]:
    cases: list[DatasetCase] = []
    p = Path(path)
    with p.open("r", encoding="utf-8") as f:
        for idx, line in enumerate(f, start=1):
            if not line.strip():
                continue
            try:
                obj = json.loads(line)
            except json.JSONDecodeError as e:
                raise ValueError(f"Invalid JSONL at {p}:{idx}: {e.msg}") from e

            if not isinstance(obj, dict):
                raise ValueError(f"Invalid JSONL at {p}:{idx}: expected object")

            case_id = obj.get("id")
            if case_id is None or str(case_id).strip() == "":
                case_id = f"case-{idx}"

            try:
                input_obj = obj["input"]
            except KeyError as e:
                raise ValueError(
                    f"Invalid JSONL at {p}:{idx}: missing required field 'input'"
                ) from e

            if not isinstance(input_obj, dict):
                raise ValueError(f"Invalid JSONL at {p}:{idx}: 'input' must be an object")

            expected_obj = obj.get("expected", {})
            meta_obj = obj.get("meta", {})

            if not isinstance(expected_obj, dict):
                raise ValueError(f"Invalid JSONL at {p}:{idx}: 'expected' must be an object")
            if not isinstance(meta_obj, dict):
                raise ValueError(f"Invalid JSONL at {p}:{idx}: 'meta' must be an object")

            cases.append(
                DatasetCase(
                    id=str(case_id),
                    input=input_obj,
                    expected=expected_obj,
                    meta=meta_obj,
                )
            )

    return cases
