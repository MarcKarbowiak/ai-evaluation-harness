from eval_harness.core.schemas import load_schema, validate_or_errors


def test_schema_validation_passes_for_valid_output():
    validator = load_schema("schemas/task_extraction.schema.json")
    ok, errors = validate_or_errors(
        validator,
        {
            "tasks": [
                {"title": "Send email", "assignee": "unknown", "due_date": None, "confidence": 0.8}
            ]
        },
    )
    assert ok is True
    assert errors == []


def test_schema_validation_fails_for_missing_required_fields():
    validator = load_schema("schemas/task_extraction.schema.json")
    ok, errors = validate_or_errors(validator, {"tasks": [{"title": "x"}]})
    assert ok is False
    assert len(errors) >= 1
