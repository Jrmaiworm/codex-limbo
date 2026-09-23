import json
from io import StringIO
from datetime import datetime, timedelta, timezone
from pathlib import Path
from rich.console import Console
from codex_limbo.sessions import parse_session
from codex_limbo.database import connect, save
from codex_limbo.alerts import check
from codex_limbo.cli import show_status
from codex_limbo.config import Config
from codex_limbo.history import recent_model, total
from codex_limbo.quota import trend


def stamp(minutes=0):
    return (datetime.now(timezone.utc) + timedelta(minutes=minutes)).isoformat()


def test_parser_only_extracts_numeric_fields(tmp_path):
    path = tmp_path / "s.jsonl"
    rows = [
        {"type": "session_meta", "payload": {"id": "s", "cwd": "/work/demo", "secret": "never store"}},
        {"type": "turn_context", "payload": {"model": "model-a"}},
        {"type": "event_msg", "timestamp": stamp(), "payload": {"type": "token_count", "info": {"total_token_usage": {"total_tokens": 30}, "last_token_usage": {"input_tokens": 20}}, "rate_limits": {"limit_id": "codex", "primary": {"window_minutes": 300, "used_percent": 20.0, "resets_at": 123}}}},
        {"type": "event_msg", "timestamp": stamp(1), "payload": {"type": "token_count", "info": {"total_token_usage": {"total_tokens": 50}, "last_token_usage": {"input_tokens": 10}}}},
    ]
    path.write_text("\n".join(json.dumps(r) for r in rows))
    usage, quota = parse_session(path)
    assert [r[-1] for r in usage] == [30, 20]
    assert usage[0][3] == "demo"
    assert quota[0][3:5] == ("5h", 20.0)
    assert "never store" not in repr((usage, quota))


def test_database_deduplicates_and_alerts(tmp_path):
    db = connect(tmp_path / "data.sqlite3")
    now = stamp()
    row = ("s", now, "model-a", "demo", 60, 40, 100)
    save(db, [row], [])
    save(db, [row], [])
    assert total(db, 1) == 100
    assert check(db, Config(token_threshold=100))[0][0] == "red"


def test_quota_trend(tmp_path):
    db = connect(tmp_path / "data.sqlite3")
    save(db, [], [("s", stamp(-4), "codex", "5h", 20, 123, None), ("s", stamp(), "codex", "5h", 40, 123, None)])
    drop, eta = trend(db, "codex", "5h")
    assert drop == 20
    assert 11 < eta < 13


def test_quota_alert_uses_recent_window_and_ignores_reset(tmp_path):
    db = connect(tmp_path / "data.sqlite3")
    save(db, [], [("s", stamp(-6), "codex", "5h", 10, 123, None),
                  ("s", stamp(-4), "codex", "5h", 20, 123, None),
                  ("s", stamp(), "codex", "5h", 26, 123, None)])
    assert any("Cota consumida: 6.0%" in message and "Nesse ritmo" in message for _, message in check(db, Config()))
    save(db, [], [("s", stamp(1), "codex", "5h", 30, 456, None)])
    assert trend(db, "codex", "5h") == (None, None)


def test_old_quota_snapshot_does_not_alert(tmp_path):
    db = connect(tmp_path / "data.sqlite3")
    save(db, [], [("s", stamp(-20), "codex", "5h", 20, 123, None),
                  ("s", stamp(-16), "codex", "5h", 95, 123, None)])
    assert check(db, Config()) == []


def test_status_shows_recent_model_consumption_and_forecast(tmp_path):
    db = connect(tmp_path / "data.sqlite3")
    save(db, [("s", stamp(-3), "model-a", "demo", 10, 10, 20),
              ("s", stamp(-1), "model-b", "demo", 20, 10, 30),
              ("s", stamp(), "model-b", "demo", 10, 10, 20)],
         [("s", stamp(-4), "codex", "5h", 20, 123, None),
          ("s", stamp(), "codex", "5h", 40, 123, None)])
    assert recent_model(db, 5) == ("model-b", 50)
    output = StringIO()
    show_status(db, Console(file=output, width=72, color_system=None), Config())
    rendered = output.getvalue()
    assert "Previsão" in rendered and "até esgotar" in rendered
    assert "Modelo ativo" in rendered and "model-b" in rendered
    assert "Modelo/5 min" in rendered and "50 tokens" in rendered
