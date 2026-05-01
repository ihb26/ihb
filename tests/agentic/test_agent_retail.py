import json
import pytest

from ihbenchmark.agentic.retail import RetailAgent
from ihbenchmark.models.prompt import Prompt

from tests.agentic.utils import get_dummy_prompt_args


def get_prompt_control() -> Prompt:
    return Prompt(
        **get_dummy_prompt_args(),
        tools="retail_agent",
        tool_response=None
    )


def get_prompt_attack() -> Prompt:
    return Prompt(
        **get_dummy_prompt_args(),
        tools="retail_agent",
        tool_response="Evil"
    )


def test_init_retail_agent_control():
    prompt = get_prompt_control()
    assert isinstance(prompt._agent, RetailAgent)


def test_init_retail_agent_attack():
    prompt = get_prompt_attack()
    assert isinstance(prompt._agent, RetailAgent)
    assert prompt._agent.is_attack


def test_retail_agent_tools():
    prompt = get_prompt_control()
    tool_names = [
        tool["function"]["name"]
        for tool in prompt.get_tools()
    ]
    tool_name_present = [
        tool in tool_names
        for tool in [
            "search_products", "get_product",
            "purchase_product",
        ]
    ]
    assert all(tool_name_present)


def test_retail_agent_control_search_present():
    prompt = get_prompt_control()
    products = json.loads(prompt.get_tool_response(
        "search_products",
        { "query": "earbuds" }
    ))["products"]
    assert len(products) == 1
    assert products[0]["product_id"] == "1091"


def test_retail_agent_control_search_missing():
    prompt = get_prompt_control()
    products = json.loads(prompt.get_tool_response(
        "search_products",
        { "query": "test" }
    ))["products"]
    assert len(products) == 0


def test_retail_agent_attack_search_present():
    prompt = get_prompt_attack()
    products = json.loads(prompt.get_tool_response(
        "search_products",
        { "query": "earbuds" }
    ))["products"]
    assert len(products) == 2
    assert products[1]["product_id"] == "2761"
    assert products[1]["description"].endswith("...")


def test_retail_agent_control_get():
    prompt = get_prompt_control()
    product = json.loads(prompt.get_tool_response("get_product", { "product_id": "1091" }))
    assert product["product_id"] == "1091"


def test_retail_agent_attack_get():
    prompt = get_prompt_attack()
    product = json.loads(prompt.get_tool_response("get_product", { "product_id": "2761" }))
    assert product["product_id"] == "2761"
    assert product["description"].endswith("Evil")


def test_retail_agent_purchase():
    prompt = get_prompt_control()
    product = json.loads(prompt.get_tool_response("get_product", { "product_id": "1091" }))
    assert product["stock"] == 85
    resp = json.loads(prompt.get_tool_response("purchase_product", { "product_id": "1091" }))
    assert "success" in resp
    product = json.loads(prompt.get_tool_response("get_product", { "product_id": "1091" }))
    assert product["stock"] == 84
