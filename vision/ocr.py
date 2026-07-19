from __future__ import annotations

from pathlib import Path


def read_text_from_image(path: Path | str) -> str:
    raise NotImplementedError(
        f"OCR is planned for AERO v0.7. Add an OCR engine for image: {Path(path)}"
    )

