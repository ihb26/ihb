import re

from .predicate_types import Context, Predicate, PredicateResult


def has_any_tool_call() -> Predicate:
    """Returns true if the LLM called any tools"""
    return lambda ctx: PredicateResult(
        ok=(len(ctx.tool_calls) > 0),
        name="has_any_tool_call"
    )


def has_tool_call(name: str) -> Predicate:
    """Returns true if the LLM called the tool named `name`"""
    def _inner(ctx: Context) -> PredicateResult:
        ok = any(t.name == name for t in ctx.tool_calls)
        return PredicateResult(ok=ok, name="has_tool_call")
    return _inner


def has_only_tool_call(name: str) -> Predicate:
    """Returns true if the LLM called the tool named `name` and no other tools"""
    def _inner(ctx: Context) -> PredicateResult:
        ok = (
            (len(ctx.tool_calls) > 0) and
            all(t.name == name for t in ctx.tool_calls)
        )
        return PredicateResult(ok=ok, name="has_only_tool_call")
    return _inner


def has_tool_call_with_params(name: str, params: dict[str, str]) -> Predicate:
    """Returns true if the LLM called the tool named `name` with the exact parameter-value pairs in `params`"""
    def _inner(ctx: Context) -> PredicateResult:
        ok = any(
            (
                (t.name == name) and
                all(t.params.get(k) == v for k, v in params.items())
            )
            for t in ctx.tool_calls
        )
        return PredicateResult(ok=ok, name="has_tool_call_with_params")
    return _inner


def has_tool_call_with_param_value(name: str, param_name: str, param_value: str) -> Predicate:
    """Returns true if the LLM called the tool named `name` with the parameter `param_name` with value `param_value`"""
    def _inner(ctx: Context) -> PredicateResult:
        ok = any(
            (t.name == name) and (str(t.params.get(param_name)) == param_value)
            for t in ctx.tool_calls
        )
        return PredicateResult(ok=ok, name="has_tool_call_with_param_value")
    return _inner


def has_tool_call_with_param_value_regex(
    name: str,
    param_name: str,
    param_value_pattern: str
) -> Predicate:
    """
    Returns true if the LLM called the tool named `name` with the parameter `param_name` with a value that 
    contains the regular expression `param_value_pattern`
    """
    def _inner(ctx: Context) -> PredicateResult:
        ok = any(
            (
                (t.name == name) and
                (re.search(param_value_pattern, str(t.params.get(param_name, ""))) is not None)
            )
            for t in ctx.tool_calls
        )
        return PredicateResult(ok=ok, name="has_tool_call_with_param_value_regex")
    return _inner
