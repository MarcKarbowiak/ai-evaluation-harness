import time
from .base import ModelResult

class MockModel:
    name = "mock"

    def generate_structured(self, *, prompt: str, input_obj: dict) -> ModelResult:
        start = time.time()
        text = (input_obj.get("text") or "").lower()

        tasks = []
        if "send" in text and "email" in text:
            tasks.append({
                "title": "Send email",
                "assignee": "unknown",
                "due_date": None,
                "confidence": 0.6,
            })
        if "follow up" in text:
            tasks.append({
                "title": "Follow up",
                "assignee": "unknown",
                "due_date": None,
                "confidence": 0.55,
            })

        latency_ms = int((time.time() - start) * 1000)

        return ModelResult(
            output={"tasks": tasks},
            raw_text=None,
            latency_ms=latency_ms,
            usage={"mock_tokens": len(text.split())},
            cost_usd=0.0,
        )
