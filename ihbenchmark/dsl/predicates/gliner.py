from .predicate_types import Context, Predicate, PredicateResult
from ..wrappers.gliner import get_gliner2_client


def discusses_topic(topic: str) -> Predicate:
    """Returns true if the LLM output discusses a topic according to GLiNER2 (warning: experimental)"""
    def _inner(ctx: Context) -> PredicateResult:
        ok, preds = get_gliner2_client().discusses_topic(ctx.content, topic)
        return PredicateResult(
            ok=ok,
            name="discusses_topic",
            metadata={ "preds": preds }
        )
    return _inner


def has_refusal() -> Predicate:
    """Returns true if the LLM output contains a refusal according to GLiNER2 (warning: experimental)"""
    def _inner(ctx: Context) -> PredicateResult:
        ok, preds = get_gliner2_client().has_refusal(ctx.content)
        return PredicateResult(
            ok=ok,
            name="has_refusal",
            metadata={ "preds": preds }
        )
    return _inner
