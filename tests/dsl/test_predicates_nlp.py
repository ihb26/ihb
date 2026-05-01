import pytest

from ihbenchmark.dsl.predicates.predicate_types import Context
from ihbenchmark.dsl.predicates.nlp import sentence_count, word_count


@pytest.mark.parametrize(
    "op, value, content, expected",
    [
        ("<", 2, "This is a simple test.", True),
        (">", 1, "This is a simple test. Another sentence.", True),
        ("<", 2, "There are many colours - i.e., red, green, blue - more text.", True),
        (">", 1, "Dr. House is a fictional character.", False),
    ]
)
def test_sentence_count(op: str, value: int, content: str, expected: bool):
    context = Context(content=content, tool_calls=[])
    predicate = sentence_count(op, value)
    assert predicate(context).ok == expected


@pytest.mark.parametrize(
    "op, value, content, expected",
    [
        ("<", 6, "This is a simple test.", True),
        ("=", 10, "There are many colours - i.e., red, green, blue - more text.", True),
        (">", 5, "Dr. House is a fictional character.", True),
    ]
)
def test_word_count(op: str, value: int, content: str, expected: bool):
    context = Context(content=content, tool_calls=[])
    predicate = word_count(op, value)
    assert predicate(context).ok == expected
