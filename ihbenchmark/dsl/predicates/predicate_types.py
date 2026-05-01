from dataclasses import dataclass, field
from typing import Any, Callable

from ...models.tool_call import ToolCall


@dataclass
class Context:
    content: str
    tool_calls: list[ToolCall]


@dataclass
class PredicateResult:
    ok: bool
    name: str | None = None
    metadata: dict[str, Any] = field(default_factory=dict)
    children: list["PredicateResult"] = field(default_factory=list)


type Predicate = Callable[[Context], PredicateResult]
