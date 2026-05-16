import uuid
from collections.abc import Callable

from src.agent_wrapper import AgentResponse


class ToolUseAgent:
    def __init__(
        self,
        decide_tools: Callable[[str], list[dict]],
        execute_tool: Callable[[str, dict], str],
        generate: Callable[[str, list[dict]], str],
        session_id: str | None = None,
    ):
        self._decide_tools = decide_tools
        self._execute_tool = execute_tool
        self._generate = generate
        self.session_id: str = session_id or str(uuid.uuid4())
        self.retrieved_context: list[str] = []
        self.tool_calls: list[dict] = []

    def process_request(self, user_input: str) -> AgentResponse:
        specs = self._decide_tools(user_input)
        self.tool_calls = [
            {"tool": s["tool"], "args": s["args"], "result": self._execute_tool(s["tool"], s["args"])}
            for s in specs
        ]
        answer = self._generate(user_input, self.tool_calls)
        return AgentResponse(text=answer)
