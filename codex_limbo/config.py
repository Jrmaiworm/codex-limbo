"""Local configuration and paths."""
from dataclasses import dataclass
from pathlib import Path
import os
import sys
import tomllib


def data_dir() -> Path:
    if sys.platform == "win32":
        return Path(os.environ.get("LOCALAPPDATA", Path.home() / "AppData/Local")) / "codex-limbo"
    return Path(os.environ.get("XDG_DATA_HOME", Path.home() / ".local/share")) / "codex-limbo"


def config_path() -> Path:
    if sys.platform == "win32":
        return Path(os.environ.get("APPDATA", Path.home() / "AppData/Roaming")) / "codex-limbo/config.toml"
    return Path(os.environ.get("XDG_CONFIG_HOME", Path.home() / ".config")) / "codex-limbo/config.toml"


def codex_home() -> Path:
    return Path(os.environ.get("CODEX_HOME", Path.home() / ".codex"))


@dataclass(frozen=True)
class Config:
    token_threshold: int = 10_000
    period_minutes: int = 5
    quota_drop_percent: float = 5.0
    exhaustion_minutes: int = 60
    watch_seconds: int = 60


def ensure_config(path: Path | None = None) -> Path:
    path = path or config_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    try:
        with path.open("x", encoding="utf-8") as stream:
            defaults = Config()
            stream.write(
                "# codex-limbo local alert settings\n"
                "[alerts]\n"
                f"token_threshold = {defaults.token_threshold}\n"
                f"period_minutes = {defaults.period_minutes}\n"
                f"quota_drop_percent = {defaults.quota_drop_percent}\n"
                f"exhaustion_minutes = {defaults.exhaustion_minutes}\n"
                f"watch_seconds = {defaults.watch_seconds}\n"
            )
    except FileExistsError:
        pass
    return path


def load_config(path: Path | None = None) -> Config:
    path = ensure_config(path)
    raw = tomllib.loads(path.read_text(encoding="utf-8")).get("alerts", {})
    values = {name: raw[name] for name in Config.__dataclass_fields__ if name in raw}
    config = Config(**values)
    if min(config.token_threshold, config.period_minutes, config.exhaustion_minutes, config.watch_seconds) <= 0 or config.quota_drop_percent <= 0:
        raise ValueError("Configuration thresholds must be positive")
    return config
