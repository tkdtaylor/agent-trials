import ollama


class OllamaBackend:
    def __init__(self, model: str = "qwen2.5:14b", host: str = "http://localhost:11434"):
        self.model = model
        self.host = host
        self._client = ollama.Client(host=host)

    def chat(self, messages: list[dict]) -> str:
        response = self._client.chat(model=self.model, messages=messages)
        return response.message.content
