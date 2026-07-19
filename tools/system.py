from __future__ import annotations

import platform


def system_summary() -> str:
    return f"{platform.system()} {platform.release()} on {platform.machine()}"

