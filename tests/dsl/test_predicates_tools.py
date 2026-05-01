import pytest

from ihbenchmark.dsl.parser import parse_predicate
from ihbenchmark.dsl.predicates.predicate_types import Context, ToolCall
from ihbenchmark.dsl.predicates.tools import (
    has_any_tool_call,
    has_tool_call,
    has_only_tool_call,
    has_tool_call_with_params,
    has_tool_call_with_param_value,
    has_tool_call_with_param_value_regex,
)


@pytest.fixture
def get_weather_tool_call_fixture() -> ToolCall:
    return ToolCall(
        name="get_weather",
        params={
            "location": "Berlin",
            "unit": "celsius",
        },
        output="{ \"temperature\": 10 }"
    )


@pytest.fixture
def list_files_tool_call_fixture() -> ToolCall:
    return ToolCall(
        name="list_files",
        params={},
        output="{ \"files\": [\"notes.txt\"] }"
    )


def test_has_any_tool_call_true(get_weather_tool_call_fixture: ToolCall):
    context = Context(content="", tool_calls=[get_weather_tool_call_fixture])
    predicate = has_any_tool_call()
    assert predicate(context).ok is True


def test_has_any_tool_call_false():
    context = Context(content="", tool_calls=[])
    predicate = has_any_tool_call()
    assert predicate(context).ok is False


def test_has_tool_call_true(get_weather_tool_call_fixture: ToolCall):
    context = Context(content="", tool_calls=[get_weather_tool_call_fixture])
    predicate = has_tool_call("get_weather")
    assert predicate(context).ok is True


def test_has_tool_call_false(get_weather_tool_call_fixture: ToolCall):
    context = Context(content="", tool_calls=[get_weather_tool_call_fixture])
    predicate = has_tool_call("read_file")
    assert predicate(context).ok is False


def test_has_only_tool_call_none():
    context = Context(content="", tool_calls=[])
    predicate = has_only_tool_call("get_weather")
    assert predicate(context).ok is False


def test_has_only_tool_call_true(get_weather_tool_call_fixture: ToolCall):
    context = Context(content="", tool_calls=[get_weather_tool_call_fixture])
    predicate = has_only_tool_call("get_weather")
    assert predicate(context).ok is True


def test_has_only_tool_call_false(
    get_weather_tool_call_fixture: ToolCall,
    list_files_tool_call_fixture: ToolCall
):
    tool_calls = [get_weather_tool_call_fixture, list_files_tool_call_fixture]
    context = Context(content="", tool_calls=tool_calls)
    predicate = has_only_tool_call("get_weather")
    assert predicate(context).ok is False


def test_has_tool_call_with_params_true(get_weather_tool_call_fixture: ToolCall):
    context = Context(content="", tool_calls=[get_weather_tool_call_fixture])
    predicate = has_tool_call_with_params(
        "get_weather",
        { "location": "Berlin", "unit": "celsius" }
    )
    assert predicate(context).ok is True


def test_has_tool_call_with_params_true_multi(
    get_weather_tool_call_fixture: ToolCall,
    list_files_tool_call_fixture: ToolCall
):
    tool_calls = [list_files_tool_call_fixture, get_weather_tool_call_fixture]
    context = Context(content="", tool_calls=tool_calls)
    predicate = has_tool_call_with_params(
        "get_weather",
        { "location": "Berlin", "unit": "celsius" }
    )
    assert predicate(context).ok is True


def test_has_tool_call_with_params_false_no_tool(list_files_tool_call_fixture: ToolCall):
    context = Context(content="", tool_calls=[list_files_tool_call_fixture])
    predicate = has_tool_call_with_params(
        "get_weather",
        { "location": "Berlin", "unit": "celsius" }
    )
    assert predicate(context).ok is False


def test_has_tool_call_with_params_false_no_value(get_weather_tool_call_fixture: ToolCall):
    context = Context(content="", tool_calls=[get_weather_tool_call_fixture])
    predicate = has_tool_call_with_params(
        "get_weather",
        { "location": "Dublin", "unit": "celsius" }
    )
    assert predicate(context).ok is False


def test_has_tool_call_with_param_value_true(get_weather_tool_call_fixture: ToolCall):
    context = Context(content="", tool_calls=[get_weather_tool_call_fixture])
    predicate = has_tool_call_with_param_value("get_weather", "unit", "celsius")
    assert predicate(context).ok is True


def test_has_tool_call_with_param_value_true_multi(
    get_weather_tool_call_fixture: ToolCall,
    list_files_tool_call_fixture: ToolCall
):
    tool_calls = [list_files_tool_call_fixture, get_weather_tool_call_fixture]
    context = Context(content="", tool_calls=tool_calls)
    predicate = has_tool_call_with_param_value("get_weather", "location", "Berlin")
    assert predicate(context).ok is True


def test_has_tool_call_with_param_value_false(get_weather_tool_call_fixture: ToolCall):
    context = Context(content="", tool_calls=[get_weather_tool_call_fixture])
    predicate = has_tool_call_with_param_value("get_weather", "unit", "fahrenheit")
    assert predicate(context).ok is False


@pytest.mark.parametrize(
    "path, expected",
    [
        ("/notes.txt", True),
        ("../notes.txt", True),
        ("./tmp/../notes.txt", True),
        ("./notes.txt", False),
        ("tmp/notes.txt", False),
        ("notes.txt", False),
    ]
)
def test_has_tool_call_with_param_value_regex_paths(path: str, expected: bool):
    tool_call = ToolCall(
        "read_file",
        { "path": path },
        output="{}"
    )
    context = Context(content="", tool_calls=[tool_call])
    predicate = has_tool_call_with_param_value_regex("read_file", "path", r"^/|\.\./")
    assert predicate(context).ok == expected


@pytest.mark.parametrize(
    "path, expected",
    [
        ("/notes.txt", True),
        ("../notes.txt", True),
        ("./tmp/../notes.txt", True),
        ("./notes.txt", False),
        ("tmp/notes.txt", False),
        ("notes.txt", False),
    ]
)
def test_has_tool_call_with_param_value_regex_paths_parsed(path: str, expected: bool):
    tool_call = ToolCall(
        "read_file",
        { "path": path },
        output="{}"
    )
    context = Context(content="", tool_calls=[tool_call])
    predicate = parse_predicate(
        r"has_tool_call_with_param_value_regex('read_file', 'path', r'^/|\.\./')"
    )
    assert predicate(context).ok == expected
