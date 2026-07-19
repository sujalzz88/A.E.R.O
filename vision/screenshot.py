from __future__ import annotations

from pathlib import Path


def capture_screenshot(path: Path | str) -> Path:
    try:
        import pyautogui
    except ImportError as exc:
        raise RuntimeError("Install pyautogui to capture screenshots.") from exc

    output_path = Path(path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    image = pyautogui.screenshot()
    image.save(output_path)
    return output_path

