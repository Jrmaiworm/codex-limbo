"""Quota snapshots from local Codex session events."""
from datetime import datetime, timedelta, timezone


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


def trend(db, limit_id: str, window: str, window_minutes: int = 5):
    latest_row = db.execute("""SELECT timestamp, used_percent, resets_at FROM quota
        WHERE limit_id=? AND window_name=? ORDER BY timestamp DESC, rowid DESC LIMIT 1""",
        (limit_id, window)).fetchone()
    if latest_row is None:
        return None, None
    try:
        current = datetime.fromisoformat(latest_row["timestamp"].replace("Z", "+00:00"))
        if current.tzinfo is None:
            current = current.replace(tzinfo=timezone.utc)
    except ValueError:
        return None, None
    cutoff = current - timedelta(minutes=window_minutes)
    rows = db.execute("""SELECT timestamp, used_percent FROM quota
        WHERE limit_id=? AND window_name=? AND resets_at IS ?
          AND timestamp>=? AND timestamp<=? ORDER BY timestamp ASC, rowid ASC""",
        (limit_id, window, latest_row["resets_at"], cutoff.strftime("%Y-%m-%dT%H:%M:%S"), latest_row["timestamp"])).fetchall()
    baseline = None
    baseline_time = None
    for row in rows:
        try:
            when = datetime.fromisoformat(row["timestamp"].replace("Z", "+00:00"))
            if when.tzinfo is None:
                when = when.replace(tzinfo=timezone.utc)
        except ValueError:
            continue
        if cutoff <= when < current:
            baseline, baseline_time = row, when
            break
    if baseline is None:
        return None, None
    seconds = (current - baseline_time).total_seconds()
    drop = max(0.0, latest_row["used_percent"] - baseline["used_percent"])
    # A forecast based on a burst shorter than a minute is too unstable.
    minutes_left = (100 - latest_row["used_percent"]) * seconds / (drop * 60) if drop > 0 and seconds >= 60 else None
    return drop, minutes_left
