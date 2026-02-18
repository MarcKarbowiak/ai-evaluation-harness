from __future__ import annotations

import json
import time
from typing import Any, Dict, Optional

from openai import OpenAI

from .base import ModelResult


class OpenAIV1Model:
    """
    OpenAI SDK adapter that can call:
    - OpenAI public API (default base_url)
    - Azure OpenAI / Azure AI Foundry 'OpenAI-compatible v1' endpoints via base_url

    It uses the Responses API (preferred) and expects the model to return valid JSON.
    """

    name = "openai_v1"

    def __init__(self, *, api_key: str, model: str, base_url: Optional[str] = None):
        if not api_key:
            raise ValueError("api_key is required")
        if not model:
            raise ValueError("model is required")

        # base_url optional:
        # - OpenAI: omit base_url (or use https://api.openai.com/v1)
        # - Azure/Foundry: set base_url to .../openai/v1/  (see README below)
        self.client = (
            OpenAI(api_key=api_key, base_url=base_url) if base_url else OpenAI(api_key=api_key)
        )
        self.model = model

    def generate_structured(self, *, prompt: str, input_obj: Dict[str, Any]) -> ModelResult:
        start = time.time()

        # Simple “prompt + input” shape; keep consistent for eval repeatability
        text = input_obj.get("text", "")
        composed = f"{prompt}\n\nInput:\n{text}"

        # Responses API is the unified API in OpenAI docs and is recommended in Azure docs too.
        resp = self.client.responses.create(
            model=self.model,
            input=composed,
            # Encourage strict JSON only
            text={"format": {"type": "json_object"}},
        )

        # Extract text output
        out_text = getattr(resp, "output_text", None) or ""
        try:
            parsed = json.loads(out_text)
        except Exception:
            # If model returns non-JSON, fail “structured” contract clearly
            parsed = {"_parse_error": True, "raw": out_text}

        latency_ms = int((time.time() - start) * 1000)

        # Usage/cost fields vary by provider; keep placeholders
        usage = getattr(resp, "usage", None)
        usage_dict = (
            usage.model_dump()
            if hasattr(usage, "model_dump")
            else (usage if isinstance(usage, dict) else None)
        )

        return ModelResult(
            output=parsed,
            raw_text=out_text,
            latency_ms=latency_ms,
            usage=usage_dict,
            cost_usd=None,
        )
