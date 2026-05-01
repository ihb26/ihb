import json
import pytest

from ihbenchmark.agentic.health import HealthAgent
from ihbenchmark.models.prompt import Prompt

from tests.agentic.utils import get_dummy_prompt_args


def get_prompt_control() -> Prompt:
    return Prompt(
        **get_dummy_prompt_args(),
        tools="health_agent",
        tool_response=None
    )


def get_prompt_attack() -> Prompt:
    return Prompt(
        **get_dummy_prompt_args(),
        tools="health_agent",
        tool_response="Evil"
    )


def test_init_health_agent_control():
    prompt = get_prompt_control()
    assert isinstance(prompt._agent, HealthAgent)


def test_init_health_agent_attack():
    prompt = get_prompt_attack()
    assert isinstance(prompt._agent, HealthAgent)
    assert prompt._agent.is_attack


def test_init_health_agent_tools():
    prompt = get_prompt_control()
    tool_names = [
        tool["function"]["name"]
        for tool in prompt.get_tools()
    ]
    tool_name_present = [
        tool in tool_names
        for tool in [
            "list_open_tickets", "get_support_ticket",
            "respond_to_ticket", "close_ticket",
            "escalate_ticket",
        ]
    ]
    assert all(tool_name_present)


def test_health_agent_control_list():
    prompt = get_prompt_control()
    tickets = json.loads(prompt.get_tool_response("list_open_tickets", {}))["tickets"]
    assert len(tickets) == 1
    assert tickets[0]["ticket_id"] == "68430"


def test_health_agent_attack_list():
    prompt = get_prompt_attack()
    tickets = json.loads(prompt.get_tool_response("list_open_tickets", {}))["tickets"]
    assert len(tickets) == 2
    assert tickets[1]["ticket_id"] == "68572"
    assert tickets[1]["description"].endswith("...")


def test_health_agent_control_get():
    prompt = get_prompt_control()
    ticket = json.loads(prompt.get_tool_response("get_support_ticket", { "ticket_id": "68430" }))
    assert ticket["ticket_id"] == "68430"


def test_health_agent_attack_get():
    prompt = get_prompt_attack()
    ticket = json.loads(prompt.get_tool_response("get_support_ticket", { "ticket_id": "68572" }))
    assert ticket["ticket_id"] == "68572"
    assert ticket["description"].endswith("Evil")


def test_health_agent_close():
    prompt = get_prompt_control()
    prompt.get_tool_response("close_ticket", { "ticket_id": "68430" })
    tickets = json.loads(prompt.get_tool_response("list_open_tickets", {}))["tickets"]
    assert len(tickets) == 0


def test_health_agent_respond():
    prompt = get_prompt_control()
    prompt.get_tool_response("respond_to_ticket", { "ticket_id": "68430", "content": "Hi!" })
    ticket = json.loads(prompt.get_tool_response("get_support_ticket", { "ticket_id": "68430" }))
    assert ticket["response"] == "Hi!"


def test_health_agent_escalate():
    prompt = get_prompt_control()
    prompt.get_tool_response("escalate_ticket", { "ticket_id": "68430", "severity_level": "critical" })
    ticket = json.loads(prompt.get_tool_response("get_support_ticket", { "ticket_id": "68430" }))
    assert ticket["level"] == "critical"
