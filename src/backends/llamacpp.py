from llama_cpp import Llama


class LlamaCppBackend:
    def __init__(self, model_path: str, n_ctx: int = 4096, n_gpu_layers: int = 0):
        self.model_path = model_path
        self.n_ctx = n_ctx
        self.n_gpu_layers = n_gpu_layers
        self._llm = Llama(model_path=model_path, n_ctx=n_ctx, n_gpu_layers=n_gpu_layers, verbose=False)

    def chat(self, messages: list[dict]) -> str:
        response = self._llm.create_chat_completion(messages=messages)
        return response["choices"][0]["message"]["content"]
