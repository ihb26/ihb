from .predicate_types import Context, Predicate, PredicateResult
from ..wrappers.nlp import (
    compare_sentence_count_to_value,
    compare_word_count_to_value,
)
from ..wrappers.utils import CompareOp


def sentence_count(op: CompareOp, value: int) -> Predicate:
    """
    Returns true if the expression `x op value` is true, where op is one of [<, <=, =, >=, >],
    and x is the number of sentences in the LLM output
    """
    def _inner(ctx: Context) -> PredicateResult:
        ok, count = compare_sentence_count_to_value(ctx.content, op, value)
        return PredicateResult(
            ok=ok,
            name="sentence_count",
            metadata={ "count": count }
        )
    return _inner


def word_count(op: CompareOp, value: int) -> Predicate:
    """
    Returns true if the expression `x op value` is true, where op is one of [<, <=, =, >=, >],
    and x is the number of words in the LLM output
    """
    def _inner(ctx: Context) -> PredicateResult:
        ok, count = compare_word_count_to_value(ctx.content, op, value)
        return PredicateResult(
            ok=ok,
            name="word_count",
            metadata={ "count": count }
        )
    return _inner
