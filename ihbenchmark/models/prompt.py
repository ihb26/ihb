import base64
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from ..agentic import init_agent
from ..agentic.agent import Agent
from ..dsl.parser import parse_predicate
from ..dsl.predicates.predicate_types import Predicate


@dataclass
class Prompt:
    # Mandatory fields
    name: str
    category: str
    subcategory: str
    system_prompt: str
    user_prompt: list[dict[str, Any]] | str | None
    expression: str
    # Optional fields
    user_image_path: str | None = None
    tool_response: str | dict[str, str | dict[str, str]] | None = None
    tools: list[dict[str, Any] | str] | str | None = None
    pass_condition: str | None = None
    rationale: str | None = None
    max_chat_iters: int | None = None
    break_on_tool_call: bool | None = None
    
    predicate: Predicate | None = None

    _user_image: str | None = None
    _tools_actual: list[dict[str, Any]] | None = None
    _agent: Agent | None = None

    def __post_init__(self):
        if (self.user_prompt is None) and (self.user_image_path is None):
            raise ValueError("One of `user_prompt` or `user_image_path` must be provided")
        
        is_agent_tool = isinstance(self.tools, str)
        is_agent_tool_resp = (
            isinstance(self.tool_response, str) or (self.tool_response is None)
        )
        
        if is_agent_tool and is_agent_tool_resp:
            self._agent = init_agent(self.tools, self.tool_response)
        
        if (not is_agent_tool) and (self.tools is not None) and (self.tool_response is None):
            raise ValueError("`tool_response` must be provided when `tools` is provided")
        
        self.predicate = parse_predicate(self.expression)
    
    def load_image_if_exists(self, path_json: Path) -> None:
        if self.user_image_path is None:
            return

        path_image = path_json.parent / self.user_image_path
        if not path_image.exists():
            raise FileNotFoundError(f"Image file does not exist: {path_image}")
        
        image_ext = path_image.suffix[1:]
        if image_ext == "jpg":
            image_ext = "jpeg"
        
        with open(path_image, "rb") as f:
            image_b64 = base64.b64encode(f.read()).decode("utf-8")
        
        self._user_image = f"data:image/{image_ext};base64,{image_b64}"

    def maybe_assign_tools(self, tools_all: dict[str, dict[str, Any]]) -> None:
        if (self._agent is not None) or (self.tools is None) or isinstance(self.tools, str):
            return
        
        self._tools_actual = []
        for tool in self.tools:
            if isinstance(tool, str):
                if tool not in tools_all:
                    raise KeyError(f"Tool with name '{tool}' is not defined")
                self._tools_actual.append(tools_all[tool])
            elif isinstance(tool, dict):
                self._tools_actual.append(tool)
            else:
                raise ValueError(f"Prompt tool must be a dictionary or a string: {tool}")

    def get_user_image(self) -> str | None:
        return self._user_image
    
    def get_tools(self) -> list[dict[str, Any]] | None:
        if self._agent is not None:
            return self._agent.get_tool_definitions()
        
        return self._tools_actual
    
    def get_tool_response(self, tool_name: str, tool_args: dict[str, Any]) -> str:
        if self._agent is not None:
            return self._agent.get_tool_response(tool_name, tool_args)

        if self.tool_response is None:
            raise ValueError(f"Received tool call for '{tool_name}' but `tool_response` is None")
        
        # Single universal tool response
        if isinstance(self.tool_response, str):
            return self.tool_response
        # Indiviudal per-tool responses
        elif isinstance(self.tool_response, dict):
            responses = self.tool_response.get(tool_name)
            # Single per-tool response
            if isinstance(responses, str):
                return responses
            # Args-based per-tool response
            elif isinstance(responses, dict):
                tool_args_fmt = "|".join(str(v) for v in tool_args.values())
                for pattern, response in responses.items():
                    if (pattern != "") and (re.search(pattern, tool_args_fmt) is not None):
                        return response
                response = responses.get("")
                if response is not None:
                    return response
                else:
                    raise ValueError(f"No fallback `tool_response` configured for tool {tool_name}")
            else:
                raise ValueError(f"Invalid `tool_response` configured for tool {tool_name}: {responses}")
        else:
            raise ValueError(f"Expected `tool_response` to be of type `str` or `dict`")


@dataclass
class PromptSet:
    name: str
    description: str
    controls: list[Prompt]
    attacks: list[Prompt]


@dataclass
class JudgePrompt:
    prompt_set_rel_path: str
    user_prompt: str
    llm_response: str
    category: str | None
