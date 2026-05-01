import pytest

from ihbenchmark.dsl.predicates.predicate_types import Context, Predicate
from ihbenchmark.dsl.predicates.logical import AND, OR, NOT
from ihbenchmark.dsl.predicates.string import contains, starts_with, ends_with, has_digits


@pytest.mark.parametrize(
    "preds, content, expected",
    [
        ([contains("123"), starts_with("test")], "testing123", True),
        ([contains("tests"), starts_with("test")], "testing123", False),
    ]
)
def test_and(preds: list[Predicate], content: str, expected: bool):
    context = Context(content=content, tool_calls=[])
    predicate = AND(*preds)
    assert predicate(context).ok == expected


@pytest.mark.parametrize(
    "preds, content, expected",
    [
        ([contains("123"), starts_with("test")], "testing123", True),
        ([contains("tests"), starts_with("test")], "testing123", True),
        ([has_digits(), ends_with("test")], "testing", False),
    ]
)
def test_or(preds: list[Predicate], content: str, expected: bool):
    context = Context(content=content, tool_calls=[])
    predicate = OR(*preds)
    assert predicate(context).ok == expected


@pytest.mark.parametrize(
    "pred, content, expected",
    [
        (contains("test"), "testing123", False),
        (contains("456"), "testing123", True),
    ]
)
def test_not(pred: Predicate, content: str, expected: bool):
    context = Context(content=content, tool_calls=[])
    predicate = NOT(pred)
    assert predicate(context).ok == expected
