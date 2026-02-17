def exact_match(pred: dict, exp: dict) -> bool:
    return pred == exp

def f1_for_titles(pred: dict, exp: dict) -> float:
    p = {t["title"].lower() for t in pred.get("tasks", [])}
    e = {t["title"].lower() for t in exp.get("tasks", [])}
    if not p and not e:
        return 1.0
    if not p or not e:
        return 0.0
    tp = len(p & e)
    precision = tp / len(p) if p else 0.0
    recall = tp / len(e) if e else 0.0
    if precision + recall == 0:
        return 0.0
    return 2 * (precision * recall) / (precision + recall)
