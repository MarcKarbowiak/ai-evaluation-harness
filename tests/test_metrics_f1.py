from eval_harness.core.metrics import f1_for_titles


def test_f1_perfect_match():
    pred = {"tasks": [{"title": "Send email"}]}
    exp = {"tasks": [{"title": "Send email"}]}
    assert f1_for_titles(pred, exp) == 1.0


def test_f1_no_overlap():
    pred = {"tasks": [{"title": "Send email"}]}
    exp = {"tasks": [{"title": "Follow up"}]}
    assert f1_for_titles(pred, exp) == 0.0


def test_f1_partial_overlap():
    pred = {"tasks": [{"title": "Send email"}, {"title": "Follow up"}]}
    exp = {"tasks": [{"title": "Send email"}, {"title": "Book meeting"}]}
    f1 = f1_for_titles(pred, exp)
    # Expected: precision=1/2, recall=1/2 -> f1=0.5
    assert abs(f1 - 0.5) < 1e-9
