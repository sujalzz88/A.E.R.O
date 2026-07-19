from __future__ import annotations

import subprocess


APP_ALIASES = {
    "chrome": "chrome",
    "google chrome": "chrome",
    "edge": "msedge",
    "microsoft edge": "msedge",
    "vscode": "code",
    "vs code": "code",
    "visual studio code": "code",
    "spotify": "spotify",
    "notepad": "notepad",
    "calculator": "calc",
}


def open_application(name: str) -> str | None:
    command = APP_ALIASES.get(name.strip().lower())
    if not command:
        return None

    try:
        subprocess.Popen([command], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    except OSError as exc:
        return f"I found {name}, but could not open it: {exc}"

    return f"Opening {name}."

