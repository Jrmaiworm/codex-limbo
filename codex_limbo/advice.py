"""Descriptive usage advice, with no assumed model prices."""
from .history import models


def recommend(db) -> list[str]:
    rows = [r for r in models(db) if r["model"] != "unknown" and r["events"] >= 3]
    if not rows:
        return ["Not enough model data yet (need at least 3 events per model)."]
    lines = [f'{r["model"]}: {r["tokens"]:,} tokens across {r["events"]} events; {r["average"]:,.0f} per event' for r in rows]
    if len(rows) > 1:
        low = min(rows, key=lambda r: r["average"])
        high = max(rows, key=lambda r: r["tokens"])
        lines.append(f'For simple tasks, consider {low["model"]} when it meets your quality needs; {high["model"]} has the highest recorded use.')
    lines.append("Cost-benefit is an estimate based on local tokens, not model prices or task difficulty.")
    return lines
