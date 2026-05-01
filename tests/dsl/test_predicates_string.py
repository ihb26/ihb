import pytest

from ihbenchmark.dsl.predicates.predicate_types import Context
from ihbenchmark.dsl.predicates.string import (
    contains,
    contains_cased,
    contains_norm,
    starts_with,
    starts_with_cased,
    ends_with,
    ends_with_cased,
    has_digits,
    has_list,
    has_list_strict,
    matches,
)


@pytest.mark.parametrize(
    "substr, content, expected",
    [
        ("test", "testing123", True),
        ("Test", "testing123", True),
        ("test", "Testing123", True),
        ("test", "esting123", False),
    ]
)
def test_contains(substr: str, content: str, expected: bool):
    context = Context(content=content, tool_calls=[])
    predicate = contains(substr)
    assert predicate(context).ok == expected


@pytest.mark.parametrize(
    "substr, content, expected",
    [
        ("test", "testing123", True),
        ("TEST", "TESTING123", True),
        ("Test", "testing123", False),
        ("test", "Testing123", False),
        ("test", "esting123", False),
    ]
)
def test_contains_cased(substr: str, content: str, expected: bool):
    context = Context(content=content, tool_calls=[])
    predicate = contains_cased(substr)
    assert predicate(context).ok == expected


@pytest.mark.parametrize(
    "substr, content, expected",
    [
        ("Sorry, I can't help with that.", "sorry I cant help with that!", True),
        ("Sorry, I can't help with that.", "Sorry, I cannot help with that", False),
        ("Désolé, je ne peux pas vous aider dans ce cas.", "desole je ne peux pas vous aider dans ce cas", True),
        ("Tá brón orm, ní féidir liom cabhrú le sin.", "ta bron orm ni feidir liom cabhru le sin", True),
    ]
)
def test_contains_norm(substr: str, content: str, expected: bool):
    context = Context(content=content, tool_calls=[])
    predicate = contains_norm(substr)
    assert predicate(context).ok == expected


@pytest.mark.parametrize(
    "substr, content, expected",
    [
        ("test", "testing123", True),
        ("Test", "testing123", True),
        ("test", "Testing123", True),
        ("test", "_testing123", False),
    ]
)
def test_starts_with(substr: str, content: str, expected: bool):
    context = Context(content=content, tool_calls=[])
    predicate = starts_with(substr)
    assert predicate(context).ok == expected


@pytest.mark.parametrize(
    "substr, content, expected",
    [
        ("test", "testing123", True),
        ("TEST", "TESTING123", True),
        ("Test", "testing123", False),
        ("test", "Testing123", False),
        ("test", "_testing123", False),
    ]
)
def test_starts_with_cased(substr: str, content: str, expected: bool):
    context = Context(content=content, tool_calls=[])
    predicate = starts_with_cased(substr)
    assert predicate(context).ok == expected


@pytest.mark.parametrize(
    "substr, content, expected",
    [
        ("ing", "testing", True),
        ("inG", "testing", True),
        ("ing", "testinG", True),
        ("ing", "testing_", False),
    ]
)
def test_ends_with(substr: str, content: str, expected: bool):
    context = Context(content=content, tool_calls=[])
    predicate = ends_with(substr)
    assert predicate(context).ok == expected


@pytest.mark.parametrize(
    "substr, content, expected",
    [
        ("ing", "testing", True),
        ("ING", "TESTING", True),
        ("inG", "testing", False),
        ("ing", "testinG", False),
        ("ing", "testing_", False),
    ]
)
def test_ends_with_cased(substr: str, content: str, expected: bool):
    context = Context(content=content, tool_calls=[])
    predicate = ends_with_cased(substr)
    assert predicate(context).ok == expected


@pytest.mark.parametrize(
    "content, expected",
    [
        ("testing", False),
        ("testing123", True),
        ("onetwothree", False),
    ]
)
def test_has_digits(content: str, expected: bool):
    context = Context(content=content, tool_calls=[])
    predicate = has_digits()
    assert predicate(context).ok == expected


@pytest.mark.parametrize(
    "content, expected",
    [
        ("- Hello", False),
        ("- 1 - 2 - 3", False),
        ("Testing123\n- abc\n* def", False),
        ("Test\n\n- One\n- Two\n- Three", True),
        ("Test\n\n(1) ...\n(2) ...\n(3) ...", True),
        ("a) a\nb) b\nc) c", True),
        ("• One\n- Two\n• Three", False),
    ]
)
def test_has_list(content: str, expected: bool):
    context = Context(content=content, tool_calls=[])
    predicate = has_list()
    assert predicate(context).ok == expected


@pytest.mark.parametrize(
    "content, expected",
    [
        ("- Hello", True),
        ("Items:\n1. a\n2. b", False),
        ("1. a\n2. b", True),
        ("Test\n\n(1) ...\n(2) ...\n(3) ...", False),
        ("a) a\nb) b\nc) c", True),
        ("• Each\n- Pattern\n* Different", True),
    ]
)
def test_has_list_strict(content: str, expected: bool):
    context = Context(content=content, tool_calls=[])
    predicate = has_list_strict()
    assert predicate(context).ok == expected


@pytest.mark.parametrize(
    "pattern, content, expected",
    [
        (r"\d+", "Two plus two is three", False),
        (r"\d+", "Two plus two = 3", True),
        (r"^test", "Test", False),
        (r"^test", "a test", False),
        (r"(?i)^test", "Test", True),
        (r"a.cdef", "str=abcdef", True),
        (r"a\.cdef", "str=abcdef", False),
    ],
)
def test_matches(pattern: str, content: str, expected: bool):
    context = Context(content=content, tool_calls=[])
    predicate = matches(pattern)
    assert predicate(context).ok == expected
