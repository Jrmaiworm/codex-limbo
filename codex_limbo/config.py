"""Local configuration and paths."""
from dataclasses import dataclass
from pathlib import Path
import os
import tomllib


def data_dir() -> Path:
    return Path(os.environ.get("XDG_DATA_HOME", Path.home() / ".local/share")) / "codex-limbo"


def config_path() -> Path:
    return Path(os.environ.get("XDG_CONFIG_HOME", Path.home() / ".config")) / "codex-limbo/config.toml"


def codex_home() -> Path:
    return Path(os.environ.get("CODEX_HOME", Path.home() / ".codex"))


@dataclass(frozen=True)
class Config:
    token_threshold: int = 100_000
    period_minutes: int = 60
    quota_drop_percent: float = 15.0
    exhaustion_minutes: int = 60
    watch_seconds: int = 30


def load_config(path: Path | None = None) -> Config:
    path = path or config_path()
    if not path.exists():
        return Config()
    raw = tomllib.loads(path.read_text(encoding="utf-8")).get("alerts", {})
    values = {name: raw[name] for name in Config.__dataclass_fields__ if name in raw}
    config = Config(**values)
    if min(config.token_threshold, config.period_minutes, config.exhaustion_minutes, config.watch_seconds) <= 0 or config.quota_drop_percent <= 0:
        raise ValueError("Configuration thresholds must be positive")
    return config
