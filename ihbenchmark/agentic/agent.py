import json
from abc import ABC, abstractmethod
from typing import Any


class Agent(ABC):
    def __init__(self, prompt_injection: str | None = None):
        self.prompt_injection = prompt_injection
        self.is_attack = (prompt_injection is not None)

    def _to_response(self, obj: dict[str, Any]) -> str:
        return json.dumps(obj, indent=2)

    @abstractmethod
    def get_tool_definitions(self) -> list[dict[str, Any]]:
        pass

    @abstractmethod
    def get_tool_response(self, tool_name: str, tool_args: dict[str, Any]) -> str:
        pass
