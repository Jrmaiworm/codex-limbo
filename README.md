# codex-limbo

Local, offline Codex usage monitor for Ubuntu and other systems with Python 3.11+.

## Install (end users)

```bash
curl -fsSL https://raw.githubusercontent.com/jrmaiworm/codex-limbo/main/install.sh | bash
```

This one-command install becomes available after the repository is published on GitHub. It downloads [uv](https://docs.astral.sh/uv/getting-started/installation/) if needed; uv then downloads Python 3.11 and installs codex-limbo from the GitHub source archive into an isolated environment. `pipx`, Git and a preinstalled Python are not required. Ubuntu needs `curl` to fetch this script; inside the script, either `curl` or `wget` can download uv. No `sudo` is used. The repository has not been published yet; do not use this command until a release is announced.

For local development from this checkout: `pipx install .`. To run tests: `python -m pip install -e '.[test]'` and `pytest`.

## Commands

```bash
codex-limbo status
codex-limbo history --hours 6   # 1, 3, 6, 12 or 24
codex-limbo watch --seconds 30
codex-limbo alerts
codex-limbo advice
codex-limbo doctor
```

The first five commands import local `~/.codex/sessions` and `~/.codex/archived_sessions` JSONL files into `~/.local/share/codex-limbo/usage.sqlite3`. Set `CODEX_HOME` to use another Codex directory, or `XDG_DATA_HOME` for another data location. Reimports replace the same session/timestamp records.

`status` shows quota snapshots recorded in local Codex session events, plus token totals estimated from those events. The official quota may be missing, stale, or depend on nonpublic Codex interfaces and formats; this tool makes no authenticated network requests. Token counts are local estimates and can differ from billing or quota units. Today starts at local midnight; history windows are rolling. Reset times use the machine's local timezone. `watch` refreshes from local files and can be stopped with Ctrl+C.

## Alert configuration

Create `~/.config/codex-limbo/config.toml`:

```toml
[alerts]
token_threshold = 100000
period_minutes = 60
quota_drop_percent = 15.0
exhaustion_minutes = 60
watch_seconds = 30
```

Alerts are printed locally. Quota drop and exhaustion estimates compare successive recorded snapshots. Advice compares observed tokens per event; it does not know prices or task complexity, so cost benefit suggestions are estimates.

## Privacy

The importer reads session metadata, model IDs, token counters and rate limit fields. It stores only session IDs, timestamps, project directory names, model IDs, numeric usage and quota fields. It does not store prompts, answers, file contents, cookies or authentication credentials. `doctor` checks whether an authentication file exists, but never opens it. Nothing is sent to a server. The database remains on this machine.

No automatic quota reset is implemented.
