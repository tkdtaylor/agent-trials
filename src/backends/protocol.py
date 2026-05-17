from typing import Protocol, runtime_checkable


@runtime_checkable
class BackendProtocol(Protocol):
    def chat(self, messages: list[dict]) -> str: ...
