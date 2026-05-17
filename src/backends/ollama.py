import re

import ollama

_THINK_RE = re.compile(r"<think>.*?</think>", re.DOTALL | re.IGNORECASE)


class OllamaBackend:
    def __init__(self, model: str = "qwen2.5:14b", host: str = "http://localhost:11434", think: bool = False):
        self.model = model
        self.host = host
        self._think = think
        self._client = ollama.Client(host=host)

    def chat(self, messages: list[dict]) -> str:
        response = self._client.chat(model=self.model, messages=messages, think=self._think or None)
        text = response.message.content or ""
        # Strip any residual <think>…</think> blocks (qwen3 models may emit them
        # even when thinking=False depending on version).
        return _THINK_RE.sub("", text).strip()
