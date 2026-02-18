from __future__ import annotations

from collections.abc import Mapping, Sequence
from typing import Any


def normalize_usage(usage: Any) -> Any:
    """Return a JSON-serializable representation of provider usage objects.

    Adapters should call this so the runner can treat `ModelResult.usage` as
    already JSON-ready.
    """
    return _to_jsonable(usage)


def _to_jsonable(value: Any) -> Any:
    if value is None:
        return None

    if isinstance(value, (str, int, float, bool)):
        return value

    if isinstance(value, Mapping):
        return {str(k): _to_jsonable(v) for k, v in value.items()}

    # Avoid treating strings/bytes as Sequences here.
    if isinstance(value, Sequence) and not isinstance(value, (str, bytes, bytearray)):
        return [_to_jsonable(v) for v in value]

    if hasattr(value, "model_dump"):
        try:
            return _to_jsonable(value.model_dump())
        except Exception:
            pass

    if hasattr(value, "__dict__"):
        try:
            return _to_jsonable(dict(value.__dict__))
        except Exception:
            pass

    return str(value)
