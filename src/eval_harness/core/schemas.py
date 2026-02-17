import json
from pathlib import Path
from jsonschema import Draft202012Validator

def load_schema(path: str):
    schema = json.loads(Path(path).read_text(encoding="utf-8"))
    return Draft202012Validator(schema)

def validate_or_errors(validator, output: dict):
    errors = sorted(validator.iter_errors(output), key=lambda e: e.path)
    return len(errors) == 0, [e.message for e in errors]
