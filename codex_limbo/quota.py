"""Quota snapshots from local Codex session events."""
from datetime import datetime, timezone


def latest(db):
    return db.execute("""SELECT q.* FROM quota q WHERE NOT EXISTS
        (SELECT 1 FROM quota n WHERE n.limit_id=q.limit_id AND n.window_name=q.window_name
         AND (n.timestamp>q.timestamp OR (n.timestamp=q.timestamp AND n.rowid>q.rowid)))
        ORDER BY q.limit_id, q.window_name""").fetchall()


def remaining(row) -> float:
    return max(0.0, 100.0 - row["used_percent"])


def reset_text(epoch) -> str:
    if not isinstance(epoch, (int, float)):
        return "unknown"
    return datetime.fromtimestamp(epoch, timezone.utc).astimezone().strftime("%Y-%m-%d %H:%M %Z")


def trend(db, limit_id: str, window: str):
    rows = db.execute("""SELECT timestamp, used_percent FROM quota
        WHERE limit_id=? AND window_name=? ORDER BY timestamp DESC LIMIT 2""", (limit_id, window)).fetchall()
    if len(rows) < 2:
        return 0.0, None
    drop = rows[0]["used_percent"] - rows[1]["used_percent"]
    try:
        seconds = (datetime.fromisoformat(rows[0]["timestamp"].replace("Z", "+00:00")) -
                   datetime.fromisoformat(rows[1]["timestamp"].replace("Z", "+00:00"))).total_seconds()
    except ValueError:
        return drop, None
    # Short intervals can produce wildly unstable forecasts as snapshots arrive in bursts.
    minutes_left = (100 - rows[0]["used_percent"]) * seconds / (drop * 60) if drop > 0 and seconds >= 900 else None
    return drop, minutes_left
