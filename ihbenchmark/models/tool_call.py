from dataclasses import dataclass


@dataclass
class ToolCall:
    name: str
    params: dict[str, str]
    output: str
