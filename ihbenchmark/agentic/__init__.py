from typing import Final

from .agent import Agent
from .coding import CodingAgent
from .health import HealthAgent
from .retail import RetailAgent


AGENT_MAP: Final[dict[str, Agent]] = {
    "coding_agent": CodingAgent,
    "health_agent": HealthAgent,
    "retail_agent": RetailAgent,
}


def init_agent(name: str, prompt_injection: str | None) -> Agent:
    agent_class = AGENT_MAP.get(name)
    if agent_class is None:
        raise KeyError(f"Unknown agent: {name}")
    return agent_class(prompt_injection=prompt_injection)
