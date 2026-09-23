"""Read selected numeric fields from local JSONL sessions incrementally."""
from dataclasses import dataclass
from hashlib import sha256
import json
from pathlib import Path
from .config import codex_home
from .database import save_incremental


@dataclass
class ParseState:
    session_id: str
    project: str = "unknown"
    model: str = "unknown"
    previous_total: int = 0


def _number(value):
    return max(0, int(value)) if isinstance(value, (int, float)) and not isinstance(value, bool) else 0


def _consume(line: str, state: ParseState, usage: list[tuple], quota: list[tuple]) -> bool:
    try:
        row = json.loads(line)
    except (ValueError, TypeError):
        return False
    if not isinstance(row, dict):
        return True
    payload = row.get("payload")
    if not isinstance(payload, dict):
        return True
    if row.get("type") == "session_meta":
        cwd = payload.get("cwd")
        if isinstance(cwd, str):
            state.project = Path(cwd).name or "unknown"
        state.session_id = str(payload.get("id") or payload.get("session_id") or state.session_id)
    elif row.get("type") == "turn_context":
        if isinstance(payload.get("model"), str):
            state.model = payload["model"]
    elif row.get("type") == "event_msg" and payload.get("type") == "token_count":
        timestamp = row.get("timestamp")
        if not isinstance(timestamp, str):
            return True
        info = payload.get("info")
        if isinstance(info, dict) and isinstance(info.get("total_token_usage"), dict):
            totals = info["total_token_usage"]
            current = _number(totals.get("total_tokens"))
            delta = current - state.previous_total if current >= state.previous_total else current
            state.previous_total = current
            if delta:
                last = info.get("last_token_usage")
                last = last if isinstance(last, dict) else {}
                inp = min(delta, _number(last.get("input_tokens")))
                usage.append((state.session_id, timestamp, state.model, state.project, inp, delta - inp, delta))
        limits = payload.get("rate_limits")
        if isinstance(limits, dict):
            limit_id = str(limits.get("limit_id") or "default")
            credits = limits.get("credits")
            balance = credits.get("balance") if isinstance(credits, dict) else None
            for name in ("primary", "secondary"):
                window = limits.get(name)
                if isinstance(window, dict) and isinstance(window.get("used_percent"), (int, float)):
                    minutes = _number(window.get("window_minutes"))
                    label = "5h" if minutes == 300 else "weekly" if minutes >= 10080 else f"{minutes}m"
                    quota.append((state.session_id, timestamp, limit_id, label, float(window["used_percent"]), window.get("resets_at"), str(balance) if balance is not None else None))
    return True


def parse_session(path: Path) -> tuple[list[tuple], list[tuple]]:
    """Parse an entire file, useful for diagnostics and parser tests."""
    state = ParseState(path.stem)
    usage, quota = [], []
    try:
        stream = path.open(encoding="utf-8", errors="replace")
    except OSError:
        return usage, quota
    with stream:
        for line in stream:
            _consume(line, state, usage, quota)
    return usage, quota


def _cursor_key(root: Path, path: Path) -> str:
    root_id = sha256(str(root.resolve()).encode("utf-8")).hexdigest()[:16]
    return f"{root_id}/{path.relative_to(root).as_posix()}"


def sync(db, root: Path | None = None) -> tuple[int, int]:
    """Import only appended bytes; a new or replaced file is read once in full."""
    root = root or codex_home()
    count = events = 0
    for folder in (root / "sessions", root / "archived_sessions"):
        if not folder.exists():
            continue
        for path in folder.rglob("*.jsonl"):
            try:
                stat = path.stat()
            except OSError:
                continue
            count += 1
            key = _cursor_key(root, path)
            old = db.execute("SELECT * FROM session_cursors WHERE path_key=?", (key,)).fetchone()
            if old and old["device"] == stat.st_dev and old["inode"] == stat.st_ino and old["file_size"] == stat.st_size and old["mtime_ns"] == stat.st_mtime_ns:
                continue
            reset = old is None or old["device"] != stat.st_dev or old["inode"] != stat.st_ino or stat.st_size < old["offset"] or (stat.st_size == old["file_size"] and stat.st_mtime_ns != old["mtime_ns"])
            state = ParseState(path.stem) if reset else ParseState(old["session_id"], old["project"], old["model"], old["previous_total"])
            offset = 0 if reset else old["offset"]
            usage, quota = [], []
            try:
                with path.open("rb") as stream:
                    stream.seek(offset)
                    while True:
                        line = stream.readline()
                        if not line:
                            break
                        # An unfinished JSON object is read again after the next append.
                        if not line.endswith(b"\n"):
                            try:
                                json.loads(line)
                            except (ValueError, UnicodeDecodeError):
                                break
                        _consume(line.decode("utf-8", errors="replace"), state, usage, quota)
                        offset = stream.tell()
            except OSError:
                continue
            cursor = (key, stat.st_dev, stat.st_ino, offset, stat.st_size, stat.st_mtime_ns,
                      state.session_id, state.project, state.model, state.previous_total)
            save_incremental(db, usage, quota, cursor, old["session_id"] if old and reset else None)
            events += len(usage)
    return count, events
