from codex_limbo import config


def test_windows_paths_use_appdata(monkeypatch, tmp_path):
    monkeypatch.setattr(config.sys, "platform", "win32")
    monkeypatch.setenv("LOCALAPPDATA", str(tmp_path / "Local"))
    monkeypatch.setenv("APPDATA", str(tmp_path / "Roaming"))
    assert config.data_dir() == tmp_path / "Local/codex-limbo"
    assert config.config_path() == tmp_path / "Roaming/codex-limbo/config.toml"


def test_first_run_creates_editable_defaults(tmp_path):
    path = tmp_path / "settings/config.toml"
    assert config.load_config(path) == config.Config()
    assert config.load_config(path).watch_seconds == 60
    assert path.is_file()
    text = path.read_text()
    assert "[alerts]" in text
    assert "token_threshold = 10000" in text
    path.write_text("[alerts]\ntoken_threshold = 42\n")
    assert config.load_config(path).token_threshold == 42
    assert path.read_text() == "[alerts]\ntoken_threshold = 42\n"
