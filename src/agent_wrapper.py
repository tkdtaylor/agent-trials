from dataclasses import dataclass
from typing import Protocol


@dataclass
class AgentResponse:
    text: str


class AgentProtocol(Protocol):
    session_id: str
    retrieved_context: list[str]
    tool_calls: list[dict]

    def process_request(self, user_input: str) -> AgentResponse: ...


class SecurityBlockedError(Exception):
    pass


class ArmorGuard:
    def __init__(self, agent: AgentProtocol, armor_client=None, session_id: str | None = None):
        self._agent = agent
        self._armor = armor_client
        self._session_id = session_id or agent.session_id

    def process(self, user_input: str) -> str:
        if self._armor is not None:
            result = self._armor.check_input(user_input, self._session_id)
            if result.blocked:
                raise SecurityBlockedError("Armor blocked input")

        response = self._agent.process_request(user_input)

        if self._armor is not None:
            result = self._armor.check_output(response.text, self._session_id)
            if result.blocked:
                raise SecurityBlockedError("Armor blocked output")

        return response.text
