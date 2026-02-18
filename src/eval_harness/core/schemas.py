from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from jsonschema import Draft202012Validator


def load_schema(path: str) -> Draft202012Validator:
    schema = json.loads(Path(path).read_text(encoding="utf-8"))
    return Draft202012Validator(schema)


def validate_or_errors(
    validator: Draft202012Validator, output: dict[str, Any]
) -> tuple[bool, list[str]]:
    # Deterministic ordering for stable reports and easier debugging.
    errors = sorted(
        validator.iter_errors(output),
        key=lambda e: (getattr(e, "json_path", "") or "", e.message),
    )
    return len(errors) == 0, [e.message for e in errors]
