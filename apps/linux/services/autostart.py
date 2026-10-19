"""Autostart — S17-4: ~/.config/autostart/streakgrid.desktop writer."""

from __future__ import annotations

import os
import sys
from pathlib import Path

DESKTOP_ENTRY = """[Desktop Entry]
Type=Application
Name=StreakGrid
Comment=Tactical habit tracker
Exec={exec_cmd}
Terminal=false
Categories=Utility;
X-GNOME-Autostart-enabled=true
"""


def default_exec() -> str:
    main_py = Path(__file__).resolve().parents[1] / "main.py"
    return f"{sys.executable} {main_py}"


def ensure_autostart(
    enabled: bool = True,
    exec_cmd: str | None = None,
    config_home: str | None = None,
) -> str | None:
    """Write/remove autostart entry. Returns file path (or None when removed)."""
    base = Path(config_home) if config_home else Path(
        os.environ.get("XDG_CONFIG_HOME", str(Path.home() / ".config"))
    )
    target = base / "autostart" / "streakgrid.desktop"
    if not enabled:
        try:
            target.unlink()
        except FileNotFoundError:
            pass
        return None
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(DESKTOP_ENTRY.format(exec_cmd=exec_cmd or default_exec()))
    return str(target)


def is_enabled(config_home: str | None = None) -> bool:
    base = Path(config_home) if config_home else Path(
        os.environ.get("XDG_CONFIG_HOME", str(Path.home() / ".config"))
    )
    return (base / "autostart" / "streakgrid.desktop").exists()
