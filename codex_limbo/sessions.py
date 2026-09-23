"""Stream local JSONL sessions, extracting only selected numeric fields."""
import json
from pathlib import Path
from datetime import datetime, timezone
from .config import codex_home
from .database import save


def _number(value):
    return max(0, int(value)) if isinstance(value, (int, float)) and not isinstance(value, bool) else 0


def parse_session(path: Path) -> tuple[list[tuple], list[tuple]]:
    session = path.stem
    project = "unknown"
    model = "unknown"
    previous = 0
    usage, quota = [], []
    try:
        stream = path.open(encoding="utf-8", errors="replace")
    except OSError:
        return usage, quota
    with stream:
        for line in stream:
            try:
                row = json.loads(line)
            except (ValueError, TypeError):
                continue
            payload = row.get("payload")
            if not isinstance(payload, dict):
                continue
            if row.get("type") == "session_meta":
                cwd = payload.get("cwd")
                if isinstance(cwd, str):
                    project = Path(cwd).name or "unknown"
                session = str(payload.get("id") or payload.get("session_id") or session)
            elif row.get("type") == "turn_context":
                if isinstance(payload.get("model"), str):
                    model = payload["model"]
            elif row.get("type") == "event_msg" and payload.get("type") == "token_count":
                timestamp = row.get("timestamp")
                if not isinstance(timestamp, str):
                    continue
                info = payload.get("info")
                if isinstance(info, dict) and isinstance(info.get("total_token_usage"), dict):
                    totals = info["total_token_usage"]
                    current = _number(totals.get("total_tokens"))
                    delta = max(0, current - previous)
                    if current < previous:
                        delta = current
                    previous = current
                    if delta:
                        inp = min(delta, _number((info.get("last_token_usage") or {}).get("input_tokens")))
                        usage.append((session, timestamp, model, project, inp, delta - inp, delta))
                limits = payload.get("rate_limits")
                if isinstance(limits, dict):
                    limit_id = str(limits.get("limit_id") or "default")
                    credits = limits.get("credits") or {}
                    balance = credits.get("balance") if isinstance(credits, dict) else None
                    for name in ("primary", "secondary"):
                        window = limits.get(name)
                        if isinstance(window, dict) and isinstance(window.get("used_percent"), (int, float)):
                            minutes = _number(window.get("window_minutes"))
                            label = "5h" if minutes == 300 else "weekly" if minutes >= 10080 else f"{minutes}m"
                            quota.append((session, timestamp, limit_id, label, float(window["used_percent"]), window.get("resets_at"), str(balance) if balance is not None else None))
    return usage, quota


def sync(db, root: Path | None = None) -> tuple[int, int]:
    root = root or codex_home()
    count = events = 0
    for folder in (root / "sessions", root / "archived_sessions"):
        if not folder.exists():
            continue
        for path in folder.rglob("*.jsonl"):
            usage, quota = parse_session(path)
            save(db, usage, quota)
            count += 1
            events += len(usage)
    return count, events
