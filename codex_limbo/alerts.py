"""Threshold checks for local usage and quota changes."""
from .history import total
from .quota import latest, trend


def check(db, config) -> list[tuple[str, str]]:
    notices = []
    tokens = total(db, config.period_minutes / 60)
    if tokens >= config.token_threshold:
        notices.append(("red", f"{tokens:,} tokens in {config.period_minutes} minutes"))
    for row in latest(db):
        drop, minutes_left = trend(db, row["limit_id"], row["window_name"])
        name = f'{row["limit_id"]} {row["window_name"]}'
        if drop >= config.quota_drop_percent:
            notices.append(("yellow", f"{name}: quota fell {drop:.1f} percentage points"))
        if minutes_left is not None and minutes_left < config.exhaustion_minutes:
            notices.append(("red", f"{name}: estimated exhaustion in {minutes_left:.0f} minutes"))
    return notices
