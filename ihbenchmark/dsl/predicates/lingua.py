from .predicate_types import Context, Predicate, PredicateResult
from ..wrappers.lingua import (
    compare_language_confidence_to_language,
    compare_language_confidence_to_value,
    is_most_confident_language,
)
from ..wrappers.utils import CompareOp


def is_language(lang: str) -> Predicate:
    """Returns true if the Lingua confidence for the language `lang` is the highest confidence language in the LLM output"""
    def _inner(ctx: Context) -> PredicateResult:
        ok, conf_lang = is_most_confident_language(ctx.content, lang)
        return PredicateResult(
            ok=ok,
            name="is_language",
            metadata={ "conf_lang": conf_lang }
        )
    return _inner


def is_language_conf(lang: str, op: CompareOp, value: float) -> Predicate:
    """
    Returns true if the expression `x op value` is true, where op is one of [<, <=, =, >=, >],
    and x is the Lingua confidence for the language `lang` in the LLM output
    """
    def _inner(ctx: Context) -> PredicateResult:
        ok, conf = compare_language_confidence_to_value(ctx.content, lang, op, value)
        return PredicateResult(
            ok=ok,
            name="is_language_conf",
            metadata={ "conf": conf }
        )
    return _inner


def is_language_more_conf(lang_gt: str, lang_lt: str) -> Predicate:
    """Returns true if the Lingua confidence for the language `lang_gt` is higher than `lang_lt` in the LLM output"""
    def _inner(ctx: Context) -> PredicateResult:
        ok, (conf_gt, conf_lt) = compare_language_confidence_to_language(
            ctx.content,
            lang_gt,
            lang_lt
        )
        return PredicateResult(
            ok=ok,
            name="is_language_more_conf",
            metadata={
                "conf_gt": conf_gt,
                "conf_lt": conf_lt,
            }
        )
    return _inner
