from __future__ import annotations

import re
import time
from typing import Any, Dict, List, Optional

from .base import ModelResult


class MockModel:
    """
    Deterministic offline adapter used for CI + harness development.

    Design goals:
    - repeatable outputs (no randomness)
    - lightweight (no external deps)
    - "good enough" coverage for the included dataset + common phrasing
    - schema-compliant structured JSON output

    This is NOT meant to be a smart NLP system. It is a predictable stand-in for real models.
    """

    name = "mock"

    # Verbs that commonly indicate actionable tasks
    _VERBS = [
        "send",
        "follow up",
        "draft",
        "review",
        "update",
        "investigate",
        "prepare",
        "confirm",
        "schedule",
        "book",
        "file",
        "read",
        "check",
        "deploy",
    ]

    # Normalize some verbs/phrases into nicer titles
    _TITLE_NORMALIZATIONS = [
        (r"\bjira\b", "Jira"),
        (r"\breadme\b", "README"),
        (r"\bpipeline\b", "pipeline"),
        (r"\blegal\b", "legal"),
        (r"\bfinance\b", "finance"),
        (r"\brelease notes\b", "release notes"),
        (r"\bonboarding\b", "onboarding"),
        (r"\bproposal\b", "proposal"),
        (r"\bdocument\b", "document"),
        (r"\bemail\b", "email"),
        (r"\bcall\b", "call"),
    ]

    _DUE_DATE_RE = re.compile(r"\b(20\d{2}-\d{2}-\d{2})\b")

    # Simple patterns for assignee extraction (deterministic)
    _ASSIGNEE_PATTERNS = [
        # "Marc will prepare the release notes"
        re.compile(r"\b(?P<who>[A-Z][a-z]+)\s+will\s+(?P<rest>.+?)(?:[.\n]|$)"),
        # "Nina to file the reimbursement"
        re.compile(r"\b(?P<who>[A-Z][a-z]+)\s+to\s+(?P<rest>.+?)(?:[.\n]|$)"),
        # "Marc: draft the client summary"
        re.compile(r"\b(?P<who>[A-Z][a-z]+)\s*:\s*(?P<rest>.+?)(?:[.\n]|$)"),
        # "Sarah, can you review it"
        re.compile(r"\b(?P<who>[A-Z][a-z]+)\s*,\s*can you\s+(?P<rest>.+?)(?:[.\n]|$)"),
        # "Everyone: read the updated policy"
        re.compile(r"\b(?P<who>Everyone)\s*:\s*(?P<rest>.+?)(?:[.\n]|$)", re.IGNORECASE),
    ]

    def generate_structured(self, *, prompt: str, input_obj: Dict[str, Any]) -> ModelResult:
        start = time.time()
        text = (input_obj.get("text") or "").strip()

        # Early exits for explicit non-task cues (keep deterministic and conservative)
        lowered = text.lower()
        if any(
            phrase in lowered
            for phrase in ["no action items", "just brainstorming", "status update only"]
        ):
            latency_ms = int((time.time() - start) * 1000)
            return ModelResult(
                output={"tasks": []},
                raw_text=None,
                latency_ms=latency_ms,
                usage={"mock_tokens": len(lowered.split())},
                cost_usd=0.0,
            )

        due_date = self._extract_due_date(text)

        candidates: List[Dict[str, Any]] = []

        # 1) Extract assignee-scoped segments first (strong signal)
        for who, segment, strength in self._extract_assignee_segments(text):
            tasks = self._extract_tasks_from_segment(
                segment, who=who, due_date=due_date, strength=strength
            )
            candidates.extend(tasks)

        # 2) Extract generic tasks from full text (weaker signal)
        candidates.extend(
            self._extract_tasks_from_segment(text, who=None, due_date=due_date, strength="weak")
        )

        # 3) Dedupe by normalized title
        deduped = self._dedupe_tasks(candidates)

        latency_ms = int((time.time() - start) * 1000)
        return ModelResult(
            output={"tasks": deduped},
            raw_text=None,
            latency_ms=latency_ms,
            usage={"mock_tokens": len(lowered.split())},
            cost_usd=0.0,
        )

    def _extract_due_date(self, text: str) -> Optional[str]:
        m = self._DUE_DATE_RE.search(text)
        return m.group(1) if m else None

    def _extract_assignee_segments(self, text: str) -> List[tuple[str, str, str]]:
        """
        Return (assignee, segment_text, strength)
        strength drives confidence deterministically.
        """
        segments: List[tuple[str, str, str]] = []
        for pat in self._ASSIGNEE_PATTERNS:
            for m in pat.finditer(text):
                who = m.group("who").strip()
                rest = m.group("rest").strip()

                # Strength heuristic:
                # - "will/to" patterns are strong
                # - "can you" is medium
                # - ":" is medium
                src = m.group(0).lower()
                if " will " in src or " to " in src:
                    strength = "strong"
                elif "can you" in src:
                    strength = "medium"
                else:
                    strength = "medium"

                segments.append((who, rest, strength))
        return segments

    def _extract_tasks_from_segment(
        self,
        segment: str,
        *,
        who: Optional[str],
        due_date: Optional[str],
        strength: str,
    ) -> List[Dict[str, Any]]:
        seg = segment.strip()

        tasks: List[Dict[str, Any]] = []

        # Split on common separators but keep deterministic
        parts = re.split(r"[;\n]|(?:\s+\d+\)\s+)|(?:\s+\d+\.\s+)", seg)
        parts = [p.strip() for p in parts if p.strip()]

        for p in parts:
            p_low = p.lower()

            verb = self._find_first_verb(p_low)
            if not verb:
                continue

            title = self._make_title(p, verb=verb)
            assignee = who if who else self._infer_assignee_fallback(seg)

            conf = self._confidence_for(
                strength=strength, verb=verb, has_assignee=bool(assignee and assignee != "unknown")
            )

            tasks.append(
                {
                    "title": title,
                    "assignee": assignee or "unknown",
                    "due_date": due_date,
                    "confidence": conf,
                }
            )

        return tasks

    def _find_first_verb(self, text_lower: str) -> Optional[str]:
        # Prioritize multi-word verbs
        if "follow up" in text_lower:
            return "follow up"
        for v in self._VERBS:
            if v in text_lower:
                return v
        return None

    def _infer_assignee_fallback(self, text: str) -> Optional[str]:
        """
        Conservative fallback:
        - if text contains 'Marc:' etc., patterns already handle it
        - if 'everyone' appears, use Everyone
        - otherwise None
        """
        low = text.lower()
        if "everyone" in low:
            return "Everyone"
        return None

    def _make_title(self, raw: str, *, verb: str) -> str:
        """
        Deterministic title shaping:
        - keep it short
        - normalize common tokens
        """
        s = raw.strip()

        # remove polite prefixes
        s = re.sub(
            r"^\s*(please|can you|could you|let's|next steps:|action items:|action:)\s*",
            "",
            s,
            flags=re.IGNORECASE,
        )

        # normalize whitespace
        s = re.sub(r"\s+", " ", s).strip()

        # If verb is present, try to keep from verb onward
        idx = s.lower().find(verb)
        if idx >= 0:
            s = s[idx:]

        # Remove trailing filler
        s = re.sub(
            r"\b(just in case|at some point|if possible|not urgent)\b.*$",
            "",
            s,
            flags=re.IGNORECASE,
        ).strip()

        # Basic normalization
        s_low = s.lower()
        for pat, repl in self._TITLE_NORMALIZATIONS:
            s_low = re.sub(pat, repl, s_low, flags=re.IGNORECASE)
        # Re-capitalize first letter
        title = s_low[:1].upper() + s_low[1:] if s_low else "Task"

        # A few deterministic tidy rules
        title = title.replace("Jira", "Jira").replace("Readme", "README")
        title = re.sub(r"[.]+$", "", title).strip()

        # If title is too generic, expand slightly
        if title.lower() in {"send email", "send the email"} and "client" in raw.lower():
            title = "Send email to client"

        return title

    def _confidence_for(self, *, strength: str, verb: str, has_assignee: bool) -> float:
        base = 0.55
        if strength == "strong":
            base = 0.82
        elif strength == "medium":
            base = 0.72
        elif strength == "weak":
            base = 0.60

        # Slight deterministic adjustments
        if verb == "follow up":
            base -= 0.05
        if has_assignee:
            base += 0.03

        # Clamp
        if base < 0.0:
            base = 0.0
        if base > 1.0:
            base = 1.0
        return round(base, 2)

    def _dedupe_tasks(self, tasks: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        seen = {}
        for t in tasks:
            key = re.sub(r"\s+", " ", (t.get("title") or "").strip().lower())
            if not key:
                continue
            # Keep the higher-confidence one deterministically
            if key not in seen or float(t.get("confidence", 0.0)) > float(
                seen[key].get("confidence", 0.0)
            ):
                seen[key] = t
        # Stable output ordering: by title
        return [seen[k] for k in sorted(seen.keys())]
