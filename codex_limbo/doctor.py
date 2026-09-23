"""Safe local diagnostics."""
from .config import codex_home, config_path, load_config


def diagnostics() -> list[str]:
    root = codex_home()
    try:
        load_config()
        config_status = "found"
    except (OSError, ValueError, TypeError):
        config_status = "invalid or unreadable"
    result = [f'Codex directory: {"found" if root.is_dir() else "missing"}',
              f'Sessions directory: {"found" if (root / "sessions").is_dir() else "missing"}',
              f'Authentication file: {"present" if (root / "auth.json").is_file() else "missing"} (contents never read)',
              f'Configuration: {config_status} ({config_path()})']
    result.append("Authentication validity cannot be checked offline without accessing credentials or a service.")
    return result
