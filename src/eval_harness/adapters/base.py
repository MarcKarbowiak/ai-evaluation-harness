from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Protocol


@dataclass(frozen=True)
class ModelResult:
    output: dict[str, Any]
    raw_text: str | None
    latency_ms: int
    # Adapters must normalize to JSON-serializable data.
    usage: Any | None = None
    cost_usd: float | None = None


class ModelAdapter(Protocol):
    name: str

    def generate_structured(self, *, prompt: str, input_obj: dict[str, Any]) -> ModelResult: ...
