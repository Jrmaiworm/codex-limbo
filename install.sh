#!/usr/bin/env bash
# One-command Ubuntu installer. Run after publishing the GitHub repository.
set -euo pipefail

if [[ "$(uname -s)" != "Linux" ]]; then
  printf 'codex-limbo: this installer currently supports Linux.\n' >&2
  exit 1
fi

limbo_bin_dir="${HOME}/.local/bin"
mkdir -p "$limbo_bin_dir"

if command -v uv >/dev/null 2>&1; then
  limbo_uv="$(command -v uv)"
elif [[ -x "$limbo_bin_dir/uv" ]]; then
  limbo_uv="$limbo_bin_dir/uv"
else
  limbo_download="$(mktemp)"
  trap 'rm -f "$limbo_download"' EXIT
  if command -v curl >/dev/null 2>&1; then
    curl -fsSL https://astral.sh/uv/install.sh -o "$limbo_download"
  elif command -v wget >/dev/null 2>&1; then
    wget -qO "$limbo_download" https://astral.sh/uv/install.sh
  else
    printf 'codex-limbo: curl or wget is required to download the installer.\n' >&2
    exit 1
  fi
  UV_INSTALL_DIR="$limbo_bin_dir" UV_NO_MODIFY_PATH=1 sh "$limbo_download"
  limbo_uv="$limbo_bin_dir/uv"
fi

limbo_source="${CODEX_LIMBO_PACKAGE_SOURCE:-https://github.com/jrmaiworm/codex-limbo/archive/refs/heads/main.zip}"
"$limbo_uv" tool install --reinstall --refresh --python 3.11 "$limbo_source"
if ! "$limbo_uv" tool update-shell; then
  printf 'codex-limbo: PATH setup needs a new terminal; the executable is installed in %s.\n' "$limbo_bin_dir" >&2
fi

printf '\ncodex-limbo installed. Open a new terminal and run: codex-limbo doctor\n'
printf 'You can run it now with: %s/codex-limbo doctor\n' "$limbo_bin_dir"
