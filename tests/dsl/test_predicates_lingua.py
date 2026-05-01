import pytest

from ihbenchmark.dsl.predicates.predicate_types import Context
from ihbenchmark.dsl.predicates.lingua import (
    is_language,
    is_language_conf,
    is_language_more_conf,
)


@pytest.mark.parametrize(
    "lang, content, expected",
    [
        ("spanish", "¿Cuál es la capital de España?", True),
        ("english", "Hello, how are you?", True),
        ("irish", "Tá brón orm, ní féidir liom cabhrú le sin.", True),
    ]
)
def test_is_language(lang: str, content: str, expected: bool):
    context = Context(content=content, tool_calls=[])
    predicate = is_language(lang)
    assert predicate(context).ok == expected


@pytest.mark.parametrize(
    "lang, op, value, content, expected",
    [
        ("french", ">", 0.7, "Désolé, je ne peux pas vous aider dans ce cas.", True),
        ("spanish", "<", 0.1, "Sorry, I can't help with that.", True),
    ]
)
def test_is_language_conf(lang: str, op: str, value: float, content: str, expected: bool):
    context = Context(content=content, tool_calls=[])
    predicate = is_language_conf(lang, op, value)
    assert predicate(context).ok == expected


@pytest.mark.parametrize(
    "lang_gt, lang_lt, content, expected",
    [
        ("chinese", "english", "中国的首都是哪里？", True),
        ("english", "spanish", "Translate the sentence 'Hello, how are you?' into Spanish.", True),
    ]
)
def test_is_language_more_conf(lang_gt: str, lang_lt: str, content: str, expected: bool):
    context = Context(content=content, tool_calls=[])
    predicate = is_language_more_conf(lang_gt, lang_lt)
    assert predicate(context).ok == expected
