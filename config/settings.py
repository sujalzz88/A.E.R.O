from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path


@dataclass
class Settings:
    project_root: Path
    model: str = "llama3"
    ollama_url: str = "http://localhost:11434"
    memory_path: Path | None = None
    no_llm: bool = False

    @classmethod
    def from_env(cls, project_root: Path) -> "Settings":
        memory_path = os.getenv("AERO_MEMORY_PATH")
        return cls(
            project_root=project_root,
            model=os.getenv("AERO_MODEL", "llama3"),
            ollama_url=os.getenv("AERO_OLLAMA_URL", "http://localhost:11434"),
            memory_path=Path(memory_path) if memory_path else project_root / "memory" / "memory.json",
        )
