from __future__ import annotations

import argparse
import datetime
import os
import subprocess
import sys
import webbrowser
from pathlib import Path

from memory.memory import MemoryStore
from tools.apps import open_application
from tools.browser import open_url, search_web
from tools.files import open_folder, search_files


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="AERO personal AI assistant")
    parser.add_argument("--model", help="Ollama model name, for example qwen3 or llama3")
    parser.add_argument("--ollama-url", help="Ollama base URL")
    parser.add_argument("--no-llm", action="store_true", help="Run only local commands")
    return parser.parse_args()


# ── Windows-only helpers ──────────────────────────────────────────────────────
def _run(cmd: list[str]) -> str:
    """Fire-and-forget subprocess. Returns stdout or empty string."""
    try:
        r = subprocess.run(cmd, capture_output=True, text=True, timeout=8)
        return r.stdout.strip()
    except Exception:
        return ""


def _set_volume(level: int) -> str:
    """Set system volume 0-100 via PowerShell."""
    ps = (
        f"$obj = New-Object -ComObject WScript.Shell; "
        f"for($i=0;$i -lt 50;$i++){{$obj.SendKeys([char]174)}}; "  # mute all first
        f"for($i=0;$i -lt {int(level/2)};$i++){{$obj.SendKeys([char]175)}}"
    )
    _run(["powershell", "-Command", ps])
    return f"Volume set to {level}%."


def _open_calendar() -> str:
    _run(["explorer.exe", "outlookcal:"])
    return "Opening your Calendar."


def _set_alarm_notification(time_str: str) -> str:
    """Best-effort: open Windows Alarms & Clock app."""
    _run(["explorer.exe", "ms-clock:"])
    return f"Opening Alarms & Clock. Please set your alarm for {time_str} manually — Windows doesn't allow setting alarms programmatically."


def _get_weather() -> str:
    webbrowser.open("https://www.google.com/search?q=weather+today")
    return "Opening the weather for you."


def _screenshot() -> str:
    try:
        import pyautogui
        path = Path.home() / "Pictures" / f"aero_{datetime.datetime.now():%Y%m%d_%H%M%S}.png"
        path.parent.mkdir(parents=True, exist_ok=True)
        pyautogui.screenshot(str(path))
        return f"Screenshot saved to {path}."
    except ImportError:
        return "pyautogui is not installed. Run: pip install pyautogui"
    except Exception as e:
        return f"Screenshot failed: {e}"


def _lock_pc() -> str:
    _run(["rundll32.exe", "user32.dll,LockWorkStation"])
    return "Locking the workstation."


def _shutdown_pc() -> str:
    _run(["shutdown", "/s", "/t", "30"])
    return "Initiating shutdown in 30 seconds. Say 'cancel shutdown' to abort."


def _cancel_shutdown() -> str:
    _run(["shutdown", "/a"])
    return "Shutdown cancelled."


def _restart_pc() -> str:
    _run(["shutdown", "/r", "/t", "30"])
    return "Restarting in 30 seconds. Say 'cancel shutdown' to abort."


def _close_app(name: str) -> str:
    killed = _run(["taskkill", "/F", "/IM", f"{name}.exe"])
    if killed:
        return f"Closed {name}."
    # Try by window title
    ps = f"Get-Process | Where-Object {{$_.MainWindowTitle -like '*{name}*'}} | Stop-Process -Force"
    _run(["powershell", "-Command", ps])
    return f"Attempted to close {name}."


# ── Command router ────────────────────────────────────────────────────────────
def handle_local_command(user_text: str, memory: MemoryStore) -> str | None:
    text = user_text.strip()
    lo = text.lower()

    # ── Memory ──
    if lo.startswith("remember that "):
        fact = text[len("remember that "):].strip().rstrip(".")
        memory.remember_fact(fact)
        return "Noted. I've stored that."

    if lo.startswith("remember "):
        fact = text[len("remember "):].strip().rstrip(".")
        memory.remember_fact(fact)
        return "Stored."

    if "what project am i working on" in lo or "current project" in lo:
        matches = memory.search("project")
        if matches:
            return matches[-1]["value"]
        return "No project saved yet."

    # ── Time & Date ──
    if any(x in lo for x in ["what time", "current time", "tell me the time"]):
        now = datetime.datetime.now()
        return f"The time is {now.strftime('%I:%M %p')}."

    if any(x in lo for x in ["what's the date", "today's date", "what date", "current date"]):
        now = datetime.datetime.now()
        return f"Today is {now.strftime('%A, %B %d, %Y')}."

    if any(x in lo for x in ["day is it", "what day"]):
        return f"Today is {datetime.datetime.now().strftime('%A')}."

    # ── Open ──
    if lo.startswith("open "):
        target = text[5:].strip()

        # Special targets
        tlo = target.lower()
        if "calendar" in tlo:
            return _open_calendar()
        if "alarm" in tlo or "clock" in tlo:
            _run(["explorer.exe", "ms-clock:"])
            return "Opening Alarms & Clock."
        if "calculator" in tlo:
            _run(["calc.exe"])
            return "Opening Calculator."
        if "notepad" in tlo:
            _run(["notepad.exe"])
            return "Opening Notepad."
        if "task manager" in tlo or "taskmanager" in tlo:
            _run(["taskmgr.exe"])
            return "Opening Task Manager."
        if "settings" in tlo:
            _run(["explorer.exe", "ms-settings:"])
            return "Opening Settings."
        if "file explorer" in tlo or "explorer" in tlo:
            _run(["explorer.exe"])
            return "Opening File Explorer."
        if "paint" in tlo:
            _run(["mspaint.exe"])
            return "Opening Paint."
        if "camera" in tlo:
            _run(["explorer.exe", "microsoft.windows.camera:"])
            return "Opening Camera."
        if "store" in tlo or "microsoft store" in tlo:
            _run(["explorer.exe", "ms-windows-store:"])
            return "Opening Microsoft Store."

        app_result = open_application(target)
        if app_result:
            return app_result
        browser_result = open_url(target)
        if browser_result:
            return browser_result
        folder_result = open_folder(target)
        if folder_result:
            return folder_result
        return f"I couldn't find '{target}'. Try saying the exact app name."

    # ── Close / Kill ──
    if lo.startswith("close ") or lo.startswith("kill "):
        name = text.split(" ", 1)[1].strip()
        return _close_app(name)

    # ── Volume ──
    if "volume up" in lo or "turn up" in lo:
        ps = "$obj = New-Object -ComObject WScript.Shell; for($i=0;$i -lt 5;$i++){$obj.SendKeys([char]175)}"
        _run(["powershell", "-Command", ps])
        return "Volume increased."
    if "volume down" in lo or "turn down" in lo:
        ps = "$obj = New-Object -ComObject WScript.Shell; for($i=0;$i -lt 5;$i++){$obj.SendKeys([char]174)}"
        _run(["powershell", "-Command", ps])
        return "Volume decreased."
    if "mute" in lo and "volume" in lo or lo == "mute":
        ps = "$obj = New-Object -ComObject WScript.Shell; $obj.SendKeys([char]173)"
        _run(["powershell", "-Command", ps])
        return "Audio muted."
    if "volume" in lo and any(c.isdigit() for c in lo):
        nums = [int(s) for s in lo.split() if s.isdigit()]
        if nums:
            return _set_volume(nums[0])

    # ── Screenshot ──
    if any(x in lo for x in ["screenshot", "take a screenshot", "capture screen"]):
        return _screenshot()

    # ── Lock / Shutdown / Restart ──
    if any(x in lo for x in ["lock computer", "lock pc", "lock the computer", "lock screen"]):
        return _lock_pc()
    if any(x in lo for x in ["shutdown", "shut down", "turn off computer", "power off"]):
        return _shutdown_pc()
    if "cancel shutdown" in lo or "abort shutdown" in lo:
        return _cancel_shutdown()
    if any(x in lo for x in ["restart", "reboot"]):
        return _restart_pc()

    # ── Alarm ──
    if "alarm" in lo or "set alarm" in lo or "wake me" in lo:
        return _set_alarm_notification(text)

    # ── Weather ──
    if any(x in lo for x in ["weather", "temperature outside", "will it rain"]):
        return _get_weather()

    # ── Search ──
    if lo.startswith("find ") or lo.startswith("search for "):
        query = text.split(" ", 1)[1].strip()
        results = search_files(query)
        if not results:
            return "No matching files found."
        lines = [f"Found {len(results)} file(s):"]
        lines.extend(f"- {path}" for path in results[:8])
        return "\n".join(lines)

    if lo.startswith("search web for ") or lo.startswith("google ") or lo.startswith("search "):
        for prefix in ["search web for ", "google ", "search "]:
            if lo.startswith(prefix):
                query = text[len(prefix):].strip()
                return search_web(query)

    # ── Battery / System info ──
    if any(x in lo for x in ["battery", "battery level", "how much battery"]):
        ps = "Get-WmiObject -Class Win32_Battery | Select-Object EstimatedChargeRemaining | Format-List"
        out = _run(["powershell", "-Command", ps])
        if out:
            return f"Battery status: {out}"
        return "Could not read battery info — desktop PC may not have a battery."

    if "ip address" in lo or "my ip" in lo:
        ps = "(Get-NetIPAddress -AddressFamily IPv4 | Where-Object {$_.IPAddress -notlike '127.*'} | Select-Object -First 1).IPAddress"
        ip = _run(["powershell", "-Command", ps])
        return f"Your local IP address is {ip}." if ip else "Could not determine IP address."

    return None


# ── CLI loop (for terminal use) ───────────────────────────────────────────────
def chat_loop(settings) -> None:
    from brain.llm import LocalLLMError, OllamaClient
    from brain.prompts import build_messages

    memory = MemoryStore(settings.memory_path)
    llm = OllamaClient(base_url=settings.ollama_url, model=settings.model)

    print("AERO online. Type 'exit' to quit.")

    while True:
        try:
            user_text = input("\nYou: ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\nAERO: Session ended.")
            break

        if not user_text:
            continue
        if user_text.lower() in {"exit", "quit", "bye"}:
            print("AERO: Shutting down.")
            break

        local_response = handle_local_command(user_text, memory)
        if local_response is not None:
            print(f"AERO: {local_response}")
            continue

        if settings.no_llm:
            print("AERO: Local-only mode. Command not recognized.")
            continue

        messages = build_messages(user_text=user_text, memory_context=memory.as_prompt_context())
        try:
            response = llm.chat(messages)
        except LocalLLMError as exc:
            response = f"LLM error: {exc}"
        print(f"AERO: {response}")


def main() -> None:
    from config.settings import Settings

    args = parse_args()
    project_root = Path(__file__).resolve().parent
    settings = Settings.from_env(project_root=project_root)

    if args.model:
        settings.model = args.model
    if args.ollama_url:
        settings.ollama_url = args.ollama_url
    if args.no_llm:
        settings.no_llm = True

    chat_loop(settings)


if __name__ == "__main__":
    main()
