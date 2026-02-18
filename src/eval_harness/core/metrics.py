from __future__ import annotations

from typing import Any


def exact_match(pred: dict[str, Any], exp: dict[str, Any]) -> bool:
    return pred == exp


def _title_set(obj: dict[str, Any]) -> set[str]:
    tasks = obj.get("tasks", [])
    if not isinstance(tasks, list):
        return set()
    titles: set[str] = set()
    for t in tasks:
        if not isinstance(t, dict):
            continue
        title = t.get("title")
        if isinstance(title, str) and title.strip():
            titles.add(title.strip().lower())
    return titles


def f1_for_titles(pred: dict[str, Any], exp: dict[str, Any]) -> float:
    p = _title_set(pred)
    e = _title_set(exp)
    if not p and not e:
        return 1.0
    if not p or not e:
        return 0.0
    tp = len(p & e)
    precision = tp / len(p)
    recall = tp / len(e)
    if precision + recall == 0:
        return 0.0
    return 2 * (precision * recall) / (precision + recall)
