import uuid

from src.agent_wrapper import AgentResponse


class EchoAgent:
    def __init__(self, session_id: str | None = None):
        self.session_id: str = session_id or str(uuid.uuid4())
        self.retrieved_context: list[str] = []
        self.tool_calls: list[dict] = []

    def process_request(self, user_input: str) -> AgentResponse:
        return AgentResponse(text=f"echo: {user_input}")
