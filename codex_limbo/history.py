"""Usage summaries."""
from datetime import datetime, timedelta, timezone


def since(hours: float) -> str:
    return (datetime.now(timezone.utc) - timedelta(hours=hours)).isoformat()


def total(db, hours: int) -> int:
    return db.execute("SELECT COALESCE(SUM(total_tokens),0) FROM usage WHERE timestamp >= ?", (since(hours),)).fetchone()[0]


def today(db) -> int:
    local_midnight = datetime.now().astimezone().replace(hour=0, minute=0, second=0, microsecond=0)
    return db.execute("SELECT COALESCE(SUM(total_tokens),0) FROM usage WHERE timestamp >= ?", (local_midnight.astimezone(timezone.utc).isoformat(),)).fetchone()[0]


def grouped(db, hours: int):
    return db.execute("""SELECT substr(timestamp,1,13) AS hour, SUM(total_tokens) AS tokens
        FROM usage WHERE timestamp >= ? GROUP BY hour ORDER BY hour""", (since(hours),)).fetchall()


def models(db, hours: int = 24):
    return db.execute("""SELECT model, COUNT(*) AS events, SUM(total_tokens) AS tokens,
        ROUND(AVG(total_tokens)) AS average FROM usage WHERE timestamp >= ?
        GROUP BY model ORDER BY tokens DESC""", (since(hours),)).fetchall()


def recent_model(db, minutes: int):
    cutoff = since(minutes / 60)
    row = db.execute("""SELECT model, timestamp FROM usage
        WHERE timestamp >= ? AND model != 'unknown'
        ORDER BY timestamp DESC, rowid DESC LIMIT 1""", (cutoff,)).fetchone()
    if row is None:
        return None
    tokens = db.execute("""SELECT COALESCE(SUM(total_tokens),0) FROM usage
        WHERE timestamp >= ? AND model = ?""", (cutoff, row["model"])).fetchone()[0]
    return row["model"], tokens
