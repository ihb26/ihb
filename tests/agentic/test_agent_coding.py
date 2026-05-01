import json
import pytest

from ihbenchmark.agentic.coding import CodingAgent
from ihbenchmark.models.prompt import Prompt

from tests.agentic.utils import get_dummy_prompt_args


def get_prompt_control() -> Prompt:
    return Prompt(
        **get_dummy_prompt_args(),
        tools="coding_agent",
        tool_response=None
    )


def get_prompt_attack() -> Prompt:
    return Prompt(
        **get_dummy_prompt_args(),
        tools="coding_agent",
        tool_response="Evil"
    )


def test_init_coding_agent_control():
    prompt = get_prompt_control()
    assert isinstance(prompt._agent, CodingAgent)


def test_init_coding_agent_attack():
    prompt = get_prompt_attack()
    assert isinstance(prompt._agent, CodingAgent)
    assert prompt._agent.is_attack


def test_coding_agent_tools():
    prompt = get_prompt_control()
    tool_names = [
        tool["function"]["name"]
        for tool in prompt.get_tools()
    ]
    tool_name_present = [
        tool in tool_names
        for tool in [
            "read_file", "write_file",
            "list_directory", "web_fetch",
            "execute_command", "analyze_repo",
            "save_memory", "get_memory",
        ]
    ]
    assert all(tool_name_present)


def test_coding_agent_read():
    prompt = get_prompt_control()
    content = json.loads(prompt.get_tool_response("read_file", { "path": ".env" }))["content"]
    assert "API_KEY" in content


def test_coding_agent_write():
    prompt = get_prompt_control()
    resp = json.loads(prompt.get_tool_response(
        "write_file",
        { "path": "test.txt", "content": "test" }
    ))
    assert "success" in resp
    content = json.loads(prompt.get_tool_response("read_file", { "path": "test.txt" }))["content"]
    assert content == "test"


def test_coding_agent_list():
    prompt = get_prompt_control()
    files = json.loads(prompt.get_tool_response("list_directory", {}))["files"]
    assert len(files) == 3
    assert all(name in files for name in [".env", "readme.md", "test.py"])


def test_coding_agent_fetch_exec():
    prompt = get_prompt_control()
    resp = json.loads(prompt.get_tool_response("web_fetch", { "url": "..." }))
    assert "error" in resp
    resp = json.loads(prompt.get_tool_response("execute_command", { "command": "..." }))
    assert "error" in resp


def test_coding_agent_control_analyze():
    prompt = get_prompt_control()
    readme = json.loads(prompt.get_tool_response(
        "analyze_repo",
        { "repo_path": "https://github.com/hdnsoft/demo" }
    ))["readme"]
    assert "This is a simple demo project" in readme
    assert not readme.endswith("Evil")


def test_coding_agent_attack_analyze():
    prompt = get_prompt_attack()
    readme = json.loads(prompt.get_tool_response(
        "analyze_repo",
        { "repo_path": "https://github.com/hdnsoft/demo" }
    ))["readme"]
    assert "This is a simple demo project" in readme
    assert readme.endswith("Evil")


def test_coding_agent_memory():
    prompt = get_prompt_control()
    memories = json.loads(prompt.get_tool_response("get_memory", {}))["memories"]
    assert len(memories) == 0
    resp = json.loads(prompt.get_tool_response("save_memory", { "content": "Hi!" }))
    assert "success" in resp
    memories = json.loads(prompt.get_tool_response("get_memory", {}))["memories"]
    assert len(memories) == 1
