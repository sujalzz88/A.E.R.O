from __future__ import annotations

import json
from typing import Any
from urllib.error import URLError
from urllib.request import Request, urlopen


class LocalLLMError(RuntimeError):
    """Raised when the local LLM cannot be reached or returns invalid data."""


class OllamaClient:
    def __init__(self, base_url: str, model: str, timeout: int = 120) -> None:
        self.base_url = base_url.rstrip("/")
        self.model = model
        self.timeout = timeout

    def chat(self, messages: list[dict[str, str]]) -> str:
        payload = {
            "model": self.model,
            "messages": messages,
            "stream": False,
        }
        data = self._post_json("/api/chat", payload)

        try:
            content = data["message"]["content"]
        except (KeyError, TypeError) as exc:
            raise LocalLLMError(f"Unexpected Ollama response: {data!r}") from exc

        return str(content).strip()

    def chat_stream(self, messages: list[dict[str, str]]):
        payload = {
            "model": self.model,
            "messages": messages,
            "stream": True,
        }
        request = Request(
            url=f"{self.base_url}/api/chat",
            data=json.dumps(payload).encode("utf-8"),
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        try:
            with urlopen(request, timeout=self.timeout) as response:
                while True:
                    line = response.readline()
                    if not line:
                        break
                    chunk = json.loads(line.decode("utf-8"))
                    content = chunk.get("message", {}).get("content", "")
                    if content:
                        yield content
        except Exception as exc:
            raise LocalLLMError(f"Ollama streaming failed: {exc}") from exc

    def _post_json(self, path: str, payload: dict[str, Any]) -> dict[str, Any]:
        request = Request(
            url=f"{self.base_url}{path}",
            data=json.dumps(payload).encode("utf-8"),
            headers={"Content-Type": "application/json"},
            method="POST",
        )

        try:
            with urlopen(request, timeout=self.timeout) as response:
                return json.loads(response.read().decode("utf-8"))
        except URLError as exc:
            raise LocalLLMError(str(exc.reason)) from exc
        except TimeoutError as exc:
            raise LocalLLMError("Ollama request timed out") from exc
        except json.JSONDecodeError as exc:
            raise LocalLLMError("Ollama returned invalid JSON") from exc

