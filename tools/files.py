from __future__ import annotations

import os
from pathlib import Path


COMMON_FOLDERS = {
    "desktop": Path.home() / "Desktop",
    "documents": Path.home() / "Documents",
    "downloads": Path.home() / "Downloads",
    "downloads folder": Path.home() / "Downloads",
}


def open_folder(name: str) -> str | None:
    folder = COMMON_FOLDERS.get(name.strip().lower())
    if not folder:
        return None

    if not folder.exists():
        return f"I could not find the {name} folder."

    os.startfile(folder)
    return f"Opening {name}."


def search_files(query: str, limit: int = 25) -> list[str]:
    roots = [Path.home() / "Desktop", Path.home() / "Documents", Path.home() / "Downloads"]
    terms = normalize_query(query)
    matches: list[str] = []

    for root in roots:
        if not root.exists():
            continue
        for path in root.rglob("*"):
            if len(matches) >= limit:
                return matches
            if not path.is_file():
                continue
            name = path.name.lower()
            if all(term in name for term in terms):
                matches.append(str(path))

    return matches


def normalize_query(query: str) -> list[str]:
    replacements = {
        "pdf": ".pdf",
        "docs": ".doc",
        "document": ".doc",
        "notes": "note",
    }
    words = [word.strip().lower() for word in query.split() if word.strip()]
    return [replacements.get(word, word) for word in words]

