from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


class MemoryStore:
    def __init__(self, path: Path | str) -> None:
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        if not self.path.exists():
            self._write({"facts": []})

    def remember_fact(self, fact: str) -> None:
        data = self._read()
        facts = data.setdefault("facts", [])
        facts.append(
            {
                "value": fact,
                "created_at": datetime.now(timezone.utc).isoformat(),
            }
        )
        self._write(data)

    def search(self, query: str) -> list[dict[str, Any]]:
        query_words = query.lower().split()
        facts = self._read().get("facts", [])
        return [
            fact
            for fact in facts
            if all(word in str(fact.get("value", "")).lower() for word in query_words)
        ]

    def as_prompt_context(self, limit: int = 12) -> str:
        facts = self._read().get("facts", [])[-limit:]
        return "\n".join(f"- {fact['value']}" for fact in facts if fact.get("value"))

    def _read(self) -> dict[str, Any]:
        try:
            return json.loads(self.path.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, FileNotFoundError):
            return {"facts": []}

    def _write(self, data: dict[str, Any]) -> None:
        self.path.write_text(json.dumps(data, indent=2), encoding="utf-8")

