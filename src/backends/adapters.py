import json
from collections.abc import Callable

from src.backends.protocol import BackendProtocol


def rag_retrieve(documents: list[str]) -> Callable[[str], list[str]]:
    def retrieve(query: str) -> list[str]:
        q = query.lower()
        return [doc for doc in documents if q in doc.lower()]

    return retrieve


def rag_generate(backend: BackendProtocol) -> Callable[[str, list[str]], str]:
    def generate(prompt: str, context: list[str]) -> str:
        context_text = "\n".join(context)
        messages = [
            {"role": "system", "content": f"Use the following context to answer:\n{context_text}"},
            {"role": "user", "content": prompt},
        ]
        return backend.chat(messages)

    return generate


def multi_turn_generate(backend: BackendProtocol) -> Callable[[str, list[dict]], str]:
    def generate(_prompt: str, history: list[dict]) -> str:
        return backend.chat(history)

    return generate


def tool_use_decide(backend: BackendProtocol, tools: list[dict]) -> Callable[[str], list[dict]]:
    tools_json = json.dumps(tools)

    def decide(user_input: str) -> list[dict]:
        messages = [
            {
                "role": "system",
                "content": (
                    f"Available tools: {tools_json}\n"
                    "Respond with a JSON array of {\"tool\": name, \"args\": {...}} objects only."
                ),
            },
            {"role": "user", "content": user_input},
        ]
        response = backend.chat(messages)
        try:
            result = json.loads(response)
            if isinstance(result, list):
                return result
        except (json.JSONDecodeError, ValueError):
            pass
        return []

    return decide


def simulated_execute_tool(tool_responses: dict[str, str] | None = None) -> Callable[[str, dict], str]:
    responses = tool_responses or {}

    def execute(tool_name: str, _args: dict) -> str:
        return responses.get(tool_name, f"[simulated result for '{tool_name}']")

    return execute


def tool_use_generate(backend: BackendProtocol) -> Callable[[str, list[dict]], str]:
    def generate(prompt: str, tool_calls: list[dict]) -> str:
        tool_text = "\n".join(f"Tool: {tc['tool']}, Result: {tc.get('result', '')}" for tc in tool_calls)
        messages = [
            {"role": "system", "content": f"Tool results:\n{tool_text}"},
            {"role": "user", "content": prompt},
        ]
        return backend.chat(messages)

    return generate
