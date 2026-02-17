import json
from dataclasses import dataclass
from pathlib import Path

@dataclass(frozen=True)
class DatasetCase:
    id: str
    input: dict
    expected: dict
    meta: dict

def load_jsonl(path: str):
    cases = []
    for line in Path(path).read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        obj = json.loads(line)
        cases.append(DatasetCase(
            id=obj.get("id"),
            input=obj["input"],
            expected=obj.get("expected", {}),
            meta=obj.get("meta", {}),
        ))
    return cases
