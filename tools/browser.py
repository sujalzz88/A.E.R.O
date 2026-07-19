from __future__ import annotations

import urllib.parse
import webbrowser


WEB_SHORTCUTS = {
    "gmail": "https://mail.google.com/",
    "youtube": "https://www.youtube.com/",
    "chatgpt": "https://chatgpt.com/",
    "ollama": "https://ollama.com/",
}


def open_url(target: str) -> str | None:
    lowered = target.strip().lower()
    url = WEB_SHORTCUTS.get(lowered)

    if not url and (lowered.startswith("http://") or lowered.startswith("https://")):
        url = target.strip()

    if not url:
        return None

    webbrowser.open(url)
    return f"Opening {target}."


def search_web(query: str) -> str:
    encoded = urllib.parse.quote_plus(query)
    webbrowser.open(f"https://www.google.com/search?q={encoded}")
    return f"Searching the web for {query}."

