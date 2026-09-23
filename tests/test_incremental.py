import json
from datetime import datetime, timedelta, timezone
from codex_limbo.database import connect, save
from codex_limbo.history import total
from codex_limbo.sessions import sync


def line(kind, payload, minute=0):
    timestamp = (datetime.now(timezone.utc) + timedelta(minutes=minute)).isoformat()
    return json.dumps({"type": kind, "timestamp": timestamp, "payload": payload}) + "\n"


def token(count, minute=0):
    return line("event_msg", {"type": "token_count", "info": {
        "total_token_usage": {"total_tokens": count},
        "last_token_usage": {"input_tokens": count // 2}}}, minute)


def test_sync_reads_only_appended_lines_and_keeps_model(tmp_path, monkeypatch):
    root = tmp_path / "codex"
    folder = root / "sessions"
    folder.mkdir(parents=True)
    path = folder / "s.jsonl"
    path.write_text(line("session_meta", {"id": "s", "cwd": "/work/demo"}) +
                    line("turn_context", {"model": "model-a"}) + token(10, -3))
    db = connect(tmp_path / "usage.sqlite3")
    assert sync(db, root) == (1, 1)
    assert total(db, 1) == 10
    cursor = db.execute("SELECT * FROM session_cursors").fetchone()
    assert str(tmp_path) not in cursor["path_key"]
    assert cursor["model"] == "model-a"

    from codex_limbo import sessions
    original = sessions._consume
    def fail_if_read(*args):
        raise AssertionError("unchanged file was parsed again")
    monkeypatch.setattr(sessions, "_consume", fail_if_read)
    assert sync(db, root) == (1, 0)
    monkeypatch.setattr(sessions, "_consume", original)

    with path.open("a") as stream:
        stream.write(token(25, -2))
    assert sync(db, root) == (1, 1)
    assert total(db, 1) == 25
    assert db.execute("SELECT model, total_tokens FROM usage ORDER BY timestamp DESC LIMIT 1").fetchone()[:] == ("model-a", 15)


def test_partial_line_waits_and_replaced_file_resets(tmp_path):
    root = tmp_path / "codex"
    folder = root / "sessions"
    folder.mkdir(parents=True)
    path = folder / "s.jsonl"
    path.write_text(line("session_meta", {"id": "s"}) + token(10, -3))
    db = connect(tmp_path / "usage.sqlite3")
    sync(db, root)
    next_line = token(30, -2)
    with path.open("a") as stream:
        stream.write(next_line[:len(next_line) // 2])
    assert sync(db, root) == (1, 0)
    assert total(db, 1) == 10
    with path.open("a") as stream:
        stream.write(next_line[len(next_line) // 2:])
    assert sync(db, root) == (1, 1)
    assert total(db, 1) == 30

    path.write_text(line("session_meta", {"id": "s"}) + token(7, -1))
    assert sync(db, root) == (1, 1)
    assert total(db, 1) == 7


def test_first_incremental_scan_replaces_existing_usage(tmp_path):
    root = tmp_path / "codex"
    folder = root / "sessions"
    folder.mkdir(parents=True)
    path = folder / "s.jsonl"
    event = token(10)
    timestamp = json.loads(event)["timestamp"]
    path.write_text(line("session_meta", {"id": "s"}) + event)
    db = connect(tmp_path / "usage.sqlite3")
    save(db, [("s", timestamp, "old-model", "demo", 999, 0, 999)], [])
    sync(db, root)
    assert total(db, 1) == 10
