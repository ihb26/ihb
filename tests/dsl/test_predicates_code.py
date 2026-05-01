import pytest

from ihbenchmark.dsl.parser import parse_predicate
from ihbenchmark.dsl.predicates.predicate_types import Context
from ihbenchmark.dsl.predicates.code import (
    has_code,
    has_code_block,
    has_json,
    has_json_schema,
)


@pytest.mark.parametrize(
    "content, expected",
    [
        ("Testing123", False),
        ("{ }", False),
        ("$x = 1 + 2$", False),
        ("def f(x: int) -> bool:\n    return x > 1", True),
        ("let x = 1 + 2;", True),
    ],
)
def test_has_code(content: str, expected: bool):
    context = Context(content=content, tool_calls=[])
    predicate = has_code()
    assert predicate(context).ok == expected


@pytest.mark.parametrize(
    "content, expected",
    [
        ("Testing123", False),
        ("```notreal\nabc\n```", False),
        ("```python```", False),
        ("```python\nx: str = \"abc\"\n```", True),
        ("```cpp\n// abc\n// def\n```", True),
    ],
)
def test_has_code_block(content: str, expected: bool):
    context = Context(content=content, tool_calls=[])
    predicate = has_code_block()
    assert predicate(context).ok == expected


@pytest.mark.parametrize(
    "content, expected",
    [
        ("Testing123", False),
        ("{ Hello }", False),
        ("```json\nNot actual JSON\n```", False),
        ("{ \"x\": 123 }", True),
        ("{\n    \"a\": \"bcd\"\n}", True),
    ],
)
def test_has_json(content: str, expected: bool):
    context = Context(content=content, tool_calls=[])
    predicate = has_json()
    assert predicate(context).ok == expected


@pytest.mark.parametrize(
    "content, expected",
    [
        ('Test123', False),
        ('{ "answer": "test" }', False),
        ('{ "answer": "test", "confidence": "100%" }', False),
        ('JSON:\n\n```json\n{\n"answer": "test", "confidence": "high"}\n```', True),
        ('{\n  "answer": "test",\n  "confidence": "low"\n}', True),
        ('{"answer": "test", "confidence": "low", "abc": "test"}', False),
    ],
)
def test_has_json_schema(content: str, expected: bool):
    schema = {
        "type": "object",
        "required": ["answer", "confidence"],
        "additionalProperties": False,
        "properties": {
            "answer": {"type": "string"},
            "confidence": {"type": "string", "enum": ["low", "medium", "high"]},
        },
    }

    context = Context(content=content, tool_calls=[])
    predicate = has_json_schema(schema)
    assert predicate(context).ok == expected


@pytest.mark.parametrize(
    "content, expected",
    [
        ('Test123', False),
        ('{ "answer": "test" }', False),
        ('{ "answer": "test", "confidence": "100%" }', False),
        ('JSON:\n\n```json\n{\n"answer": "test", "confidence": "high"}\n```', True),
        ('{\n  "answer": "test",\n  "confidence": "low"\n}', True),
        ('{"answer": "test", "confidence": "low", "abc": "test"}', False),
    ],
)
def test_has_json_schema_parsed(content: str, expected: bool):
    expr = (
        'has_json_schema({'
            '"type": "object",'
            '"required": ["answer", "confidence"],'
            '"additionalProperties": False,'
            '"properties": {'
                '"answer": { "type": "string" },'
                '"confidence": { "type": "string", "enum": ["low", "medium", "high"] }'
            '}'
        '})'
    )

    context = Context(content=content, tool_calls=[])
    predicate = parse_predicate(expr)
    assert predicate(context).ok == expected
