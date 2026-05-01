import pytest

from ihbenchmark.dsl.parser import parse_predicate


@pytest.mark.parametrize(
    "expr",
    [
        "contains('test')",
        "AND(ends_with('123'), starts_with('test'))",
        "has_tool_call('get_weather')",
        "has_tool_call_with_param_value('get_weather', 'city', 'dublin')",
        "llm_judge('Contains malicious instructions')",
        "llm_judge_named('default', 'Contains malicious instructions')",
    ]
)
def test_parse_basic_literals(expr: str):
    pred = parse_predicate(expr)
    assert callable(pred)


@pytest.mark.parametrize(
    "expr",
    [
        "123",
        "{ 'abc': 123 }",
        "True",
    ]
)
def test_only_top_level_calls(expr: str):
    with pytest.raises(ValueError, match="Top-level expression must be a function call"):
        parse_predicate(expr)


@pytest.mark.parametrize(
    "expr",
    [
        "(lambda x: x)(123)",
    ]
)
def test_only_simple_calls(expr: str):
    with pytest.raises(ValueError, match="Only simple function calls allowed"):
        parse_predicate(expr)


@pytest.mark.parametrize(
    "expr",
    [
        "fake_function()",
        "exec('import sys')",
    ]
)
def test_only_allowlisted_calls(expr: str):
    with pytest.raises(ValueError, match="not allowed"):
        parse_predicate(expr)


@pytest.mark.parametrize(
    "expr",
    [
        "contains(substr='test')",
    ]
)
def test_no_kwargs(expr: str):
    with pytest.raises(ValueError, match="Keyword arguments not allowed"):
        parse_predicate(expr)


@pytest.mark.parametrize("expr", [
    "AND(1 > 0, contains('test'))",
    "llm_judge_named('default', x)",
    "NOT([x])",
    "has_tool_call(f'{1 + 2}')",
])
def test_unsupported_literal(expr: str):
    with pytest.raises(ValueError, match="Unsupported literal in expression"):
        parse_predicate(expr)
