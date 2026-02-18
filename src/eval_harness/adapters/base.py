from dataclasses import dataclass
from typing import Any, Dict, Protocol


@dataclass(frozen=True)
class ModelResult:
    output: Dict[str, Any]
    raw_text: str | None
    latency_ms: int
    usage: Dict[str, Any] | None = None
    cost_usd: float | None = None


class ModelAdapter(Protocol):
    name: str

    def generate_structured(self, *, prompt: str, input_obj: Dict[str, Any]) -> ModelResult: ...
