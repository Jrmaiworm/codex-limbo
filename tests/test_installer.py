import os
import subprocess
import sys
from pathlib import Path
import pytest


INSTALLER = Path(__file__).resolve().parents[1] / "install.sh"
pytestmark = pytest.mark.skipif(sys.platform == "win32", reason="Bash installer is Linux-only")


def test_installer_uses_uv_without_pipx(tmp_path):
    bin_dir = tmp_path / "bin"
    bin_dir.mkdir()
    uv = bin_dir / "uv"
    uv.write_text('#!/bin/sh\nprintf "%s\\n" "$*" >> "$HOME/uv-calls"\n')
    uv.chmod(0o755)
    env = os.environ.copy()
    env.update(HOME=str(tmp_path), PATH=f'{bin_dir}:{os.environ["PATH"]}', CODEX_LIMBO_PACKAGE_SOURCE="/tmp/local-package")
    result = subprocess.run(["bash", str(INSTALLER)], env=env, text=True, capture_output=True)
    assert result.returncode == 0, result.stderr
    assert (tmp_path / "uv-calls").read_text().splitlines() == [
        "tool install --python 3.11 /tmp/local-package", "tool update-shell"
    ]


def test_installer_bootstraps_uv(tmp_path):
    bin_dir = tmp_path / "bin"
    bin_dir.mkdir()
    curl = bin_dir / "curl"
    curl.write_text('''#!/bin/sh
while [ "$1" != "-o" ]; do shift; done
cat > "$2" <<'SCRIPT'
#!/bin/sh
printf '#!/bin/sh\\nprintf "%%s\\\\n" "$*" >> "$HOME/uv-calls"\\n' > "$UV_INSTALL_DIR/uv"
chmod +x "$UV_INSTALL_DIR/uv"
SCRIPT
''')
    curl.chmod(0o755)
    env = os.environ.copy()
    env.update(HOME=str(tmp_path), PATH=f'{bin_dir}:/usr/bin:/bin', CODEX_LIMBO_PACKAGE_SOURCE="/tmp/local-package")
    result = subprocess.run(["bash", str(INSTALLER)], env=env, text=True, capture_output=True)
    assert result.returncode == 0, result.stderr
    assert "tool install --python 3.11 /tmp/local-package" in (tmp_path / "uv-calls").read_text()
