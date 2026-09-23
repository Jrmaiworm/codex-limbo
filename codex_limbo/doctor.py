"""Safe local diagnostics."""
from .config import codex_home, config_path


def diagnostics() -> list[str]:
    root = codex_home()
    result = [f'Codex directory: {"found" if root.is_dir() else "missing"}',
              f'Sessions directory: {"found" if (root / "sessions").is_dir() else "missing"}',
              f'Authentication file: {"present" if (root / "auth.json").is_file() else "missing"} (contents never read)',
              f'Configuration: {"found" if config_path().is_file() else "defaults in use"}']
    result.append("Authentication validity cannot be checked offline without accessing credentials or a service.")
    return result
