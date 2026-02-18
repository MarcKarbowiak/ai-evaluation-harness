from __future__ import annotations

from typing import Any, NotRequired, TypedDict


class ReportMeta(TypedDict):
    run_id: str
    started_at_utc: str
    adapter: str
    dataset_path: str
    prompt_path: str
    schema_path: str


class ReportSummary(TypedDict):
    run_id: str
    started_at_utc: str
    adapter: str
    total: int
    schema_valid_rate: float
    exact_match_rate: float
    avg_f1: float
    avg_latency_ms: float
    parse_error_count: int


class ReportResultRow(TypedDict):
    id: str
    schema_valid: bool
    schema_errors: list[str]
    exact_match: bool
    f1: float
    latency_ms: int
    usage: Any
    cost_usd: NotRequired[float | None]


class EvalReport(TypedDict):
    meta: ReportMeta
    summary: ReportSummary
    results: list[ReportResultRow]
