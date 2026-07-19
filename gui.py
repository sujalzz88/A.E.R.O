from __future__ import annotations

import argparse
import json
import socket
import subprocess
import sys
import webbrowser
from http.server import BaseHTTPRequestHandler, HTTPServer
from socketserver import ThreadingMixIn
from pathlib import Path
from urllib.error import URLError
from urllib.request import urlopen

# Add the project root to sys.path so we can import modules correctly
project_root = Path(__file__).resolve().parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from brain.llm import LocalLLMError, OllamaClient
from brain.prompts import build_messages
from config.settings import Settings
from main import handle_local_command
from memory.memory import MemoryStore
from tools.apps import open_application
from tools.browser import open_url, search_web
from tools.files import open_folder, search_files

# ── Global instances ──────────────────────────────────────────────────────────
settings: Settings = None
memory: MemoryStore = None
llm: OllamaClient | None = None


def check_ollama_alive(url: str) -> bool:
    """Return True if Ollama HTTP endpoint is reachable."""
    try:
        with urlopen(f"{url}/api/tags", timeout=5) as r:
            return r.status == 200
    except Exception:
        return False


def execute_system_command(cmd: str) -> str:
    """Run shell/powershell commands securely and capture stdout/stderr."""
    try:
        if cmd.lower().startswith("powershell"):
            ps_cmd = cmd[10:].strip()
            # Unescape double quotes inside the powershell command if they were escaped
            if '\\"' in ps_cmd:
                ps_cmd = ps_cmd.replace('\\"', '"')
            result = subprocess.run(
                ["powershell", "-Command", ps_cmd],
                capture_output=True,
                text=True,
                timeout=20
            )
        else:
            result = subprocess.run(
                cmd,
                shell=True,
                capture_output=True,
                text=True,
                timeout=20
            )
        
        out = result.stdout.strip()
        err = result.stderr.strip()
        
        if out and err:
            return f"{out}\n{err}"
        elif out:
            return out
        elif err:
            return f"Error: {err}"
        else:
            return "Command executed successfully with no output."
    except subprocess.TimeoutExpired:
        return "Command timed out after 20 seconds."
    except Exception as exc:
        return f"Execution error: {exc}"


class CommandStreamParser:
    """Buffer and process streamed text chunks to extract and execute <aero-cmd> blocks."""
    def __init__(self, callback):
        self.callback = callback
        self.buffer = ""
        self.in_command = False
        self.command_text = ""

    def feed(self, chunk: str):
        self.buffer += chunk
        
        while True:
            if not self.in_command:
                idx = self.buffer.find("<aero-cmd>")
                if idx != -1:
                    text_before = self.buffer[:idx]
                    if text_before:
                        self.callback(text_before)
                    
                    self.in_command = True
                    self.command_text = ""
                    self.buffer = self.buffer[idx + len("<aero-cmd>"):]
                else:
                    tag = "<aero-cmd>"
                    keep = len(tag) - 1
                    if len(self.buffer) > keep:
                        send_len = len(self.buffer) - keep
                        self.callback(self.buffer[:send_len])
                        self.buffer = self.buffer[send_len:]
                    break
            else:
                idx = self.buffer.find("</aero-cmd>")
                if idx != -1:
                    self.command_text += self.buffer[:idx]
                    cmd = self.command_text.strip()
                    
                    self.callback(f"\n[Executing system operation: {cmd}...]\n")
                    exec_result = execute_system_command(cmd)
                    self.callback(f"[Execution Result: {exec_result}]\n")
                    
                    self.in_command = False
                    self.command_text = ""
                    self.buffer = self.buffer[idx + len("</aero-cmd>"):]
                else:
                    tag_close = "</aero-cmd>"
                    keep = len(tag_close) - 1
                    if len(self.buffer) > keep:
                        send_len = len(self.buffer) - keep
                        self.command_text += self.buffer[:send_len]
                        self.buffer = self.buffer[send_len:]
                    break

    def flush(self):
        if self.buffer:
            if self.in_command:
                self.command_text += self.buffer
                cmd = self.command_text.strip()
                self.callback(f"\n[Executing system operation: {cmd}...]\n")
                exec_result = execute_system_command(cmd)
                self.callback(f"[Execution Result: {exec_result}]\n")
            else:
                self.callback(self.buffer)
        self.buffer = ""


class ThreadedHTTPServer(ThreadingMixIn, HTTPServer):
    """Handle each request in a new thread so streaming doesn't block."""
    daemon_threads = True


class AeroRequestHandler(BaseHTTPRequestHandler):
    def log_message(self, fmt, *args):
        # Print requests for debugging
        sys.stdout.write(f"[AERO] {args[0] if args else fmt}\n")
        sys.stdout.flush()

    # ── GET ──────────────────────────────────────────────────────────────────
    def do_GET(self):
        if self.path in ("/", "/index.html"):
            self._serve_file(project_root / "index.html", "text/html; charset=utf-8")
        elif self.path == "/api/settings":
            self._json_response({"model": settings.model, "no_llm": settings.no_llm})
        elif self.path == "/api/ollama-check":
            alive = check_ollama_alive(settings.ollama_url)
            self._json_response({"alive": alive})
        else:
            self.send_response(404)
            self.end_headers()

    def _serve_file(self, path: Path, content_type: str):
        try:
            content = path.read_bytes()
            self.send_response(200)
            self.send_header("Content-Type", content_type)
            self.send_header("Content-Length", str(len(content)))
            self.end_headers()
            self.wfile.write(content)
        except Exception as exc:
            self.send_response(500)
            self.end_headers()
            self.wfile.write(f"Error: {exc}".encode())

    def _json_response(self, data: dict, status: int = 200):
        body = json.dumps(data).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def _send_stream_headers(self):
        self.send_response(200)
        self.send_header("Content-Type", "application/x-ndjson")
        self.send_header("Cache-Control", "no-cache")
        self.send_header("Transfer-Encoding", "chunked")
        self.send_header("Connection", "close")
        self.end_headers()

    def _send_stream_chunk(self, text: str):
        try:
            payload = json.dumps({"text": text}).encode("utf-8") + b"\n"
            chunk = f"{len(payload):x}\r\n".encode() + payload + b"\r\n"
            self.wfile.write(chunk)
            self.wfile.flush()
        except Exception:
            pass

    def _end_stream(self):
        try:
            self.wfile.write(b"0\r\n\r\n")
            self.wfile.flush()
        except Exception:
            pass

    # ── POST ─────────────────────────────────────────────────────────────────
    def do_POST(self):
        if self.path == "/api/chat":
            self._handle_chat()
        elif self.path == "/api/screenshot":
            self._handle_screenshot()
        else:
            self.send_response(404)
            self.end_headers()

    def _read_json_body(self) -> dict | None:
        length = int(self.headers.get("Content-Length", 0))
        try:
            return json.loads(self.rfile.read(length).decode("utf-8"))
        except Exception:
            return None

    def _handle_chat(self):
        payload = self._read_json_body()
        if payload is None:
            self.send_response(400)
            self.end_headers()
            return

        user_text = payload.get("message", "").strip()
        if not user_text:
            self._send_stream_headers()
            self._send_stream_chunk("")
            self._end_stream()
            return

        # 1. Local command handler (memory, open app/url/folder, find files)
        local_response = handle_local_command(user_text, memory)
        if local_response is not None:
            self._send_stream_headers()
            self._send_stream_chunk(local_response)
            self._end_stream()
            return

        # 2. Local-only mode
        if settings.no_llm:
            self._send_stream_headers()
            self._send_stream_chunk("Local command mode is active. I did not find a matching command.")
            self._end_stream()
            return

        # 3. Check Ollama is alive before calling
        if not check_ollama_alive(settings.ollama_url):
            self._send_stream_headers()
            self._send_stream_chunk(
                "Ollama is not running on this machine. "
                "Please open Ollama (the llama icon in your taskbar) and wait a few seconds, then try again."
            )
            self._end_stream()
            return

        # 4. Query LLM via streaming
        messages = build_messages(user_text=user_text, memory_context=memory.as_prompt_context())
        self._send_stream_headers()
        try:
            parser = CommandStreamParser(self._send_stream_chunk)
            for chunk in llm.chat_stream(messages):
                parser.feed(chunk)
            parser.flush()
        except Exception as exc:
            self._send_stream_chunk(f"\nLLM streaming error: {exc}")
        self._end_stream()

    def _handle_screenshot(self):
        """v0.7 stub – screenshot analysis."""
        try:
            import pyautogui
            screenshot = pyautogui.screenshot()
            path = project_root / "data" / "last_screenshot.png"
            path.parent.mkdir(parents=True, exist_ok=True)
            screenshot.save(path)
            self._json_response({"response": f"Screenshot saved to {path}."})
        except Exception as exc:
            self._json_response({"response": f"Screenshot failed: {exc}"})


# ── Server bootstrap ──────────────────────────────────────────────────────────

def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="AERO Jarvis Web UI Server")
    parser.add_argument("--model", help="Ollama model name, e.g. llama3 or qwen3")
    parser.add_argument("--ollama-url", dest="ollama_url", help="Ollama base URL")
    parser.add_argument("--no-llm", action="store_true", help="Run only local commands")
    parser.add_argument("--port", type=int, default=8000, help="Local server port (default 8000)")
    return parser.parse_args()


def is_port_free(port: int) -> bool:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        return s.connect_ex(("localhost", port)) != 0


def main() -> None:
    global settings, memory, llm

    args = parse_args()
    settings = Settings.from_env(project_root=project_root)

    if args.model:
        settings.model = args.model
    if args.ollama_url:
        settings.ollama_url = args.ollama_url
    if args.no_llm:
        settings.no_llm = True

    memory = MemoryStore(settings.memory_path)

    if not settings.no_llm:
        llm = OllamaClient(base_url=settings.ollama_url, model=settings.model)

    # Find a free port
    port = args.port
    while not is_port_free(port):
        print(f"[AERO] Port {port} busy, trying {port + 1}…")
        port += 1

    httpd = ThreadedHTTPServer(("localhost", port), AeroRequestHandler)
    url = f"http://localhost:{port}"

    ollama_ok = check_ollama_alive(settings.ollama_url)

    print("=" * 60)
    print("  AERO // J.A.R.V.I.S. INTERFACE ONLINE")
    print(f"  UI  : {url}")
    print(f"  Model : {settings.model}")
    print(f"  LLM   : {'DISABLED (local-only)' if settings.no_llm else 'ENABLED (Ollama)'}")
    print(f"  Ollama: {'REACHABLE [OK]' if ollama_ok else 'NOT RUNNING - start Ollama first!'}")
    print("=" * 60)
    print("  Press Ctrl+C to stop.\n")

    webbrowser.open(url)

    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        print("\n[AERO] Shutting down.")
        httpd.server_close()


if __name__ == "__main__":
    main()