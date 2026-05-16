import uuid
from collections.abc import Callable

from src.agent_wrapper import AgentResponse


class MultiTurnAgent:
    def __init__(
        self,
        generate: Callable[[str, list[dict]], str],
        session_id: str | None = None,
    ):
        self._generate = generate
        self.session_id: str = session_id or str(uuid.uuid4())
        self.retrieved_context: list[str] = []
        self.tool_calls: list[dict] = []
        self._history: list[dict] = []

    def process_request(self, user_input: str) -> AgentResponse:
        self._history.append({"role": "user", "content": user_input})
        response_text = self._generate(user_input, self._history)
        self._history.append({"role": "assistant", "content": response_text})
        return AgentResponse(text=response_text)
