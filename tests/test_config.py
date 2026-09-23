from codex_limbo import config


def test_windows_paths_use_appdata(monkeypatch, tmp_path):
    monkeypatch.setattr(config.sys, "platform", "win32")
    monkeypatch.setenv("LOCALAPPDATA", str(tmp_path / "Local"))
    monkeypatch.setenv("APPDATA", str(tmp_path / "Roaming"))
    assert config.data_dir() == tmp_path / "Local/codex-limbo"
    assert config.config_path() == tmp_path / "Roaming/codex-limbo/config.toml"
