import uuid
from collections.abc import Callable

from src.agent_wrapper import AgentResponse


class RAGAgent:
    def __init__(
        self,
        retrieve: Callable[[str], list[str]],
        generate: Callable[[str, list[str]], str],
        session_id: str | None = None,
    ):
        self._retrieve = retrieve
        self._generate = generate
        self.session_id: str = session_id or str(uuid.uuid4())
        self.retrieved_context: list[str] = []
        self.tool_calls: list[dict] = []

    def process_request(self, user_input: str) -> AgentResponse:
        self.retrieved_context = self._retrieve(user_input)
        answer = self._generate(user_input, self.retrieved_context)
        return AgentResponse(text=answer)
