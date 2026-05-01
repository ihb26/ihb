from .predicate_types import Context, Predicate, PredicateResult
from ..wrappers.llm_judge import get_llm_judge, get_named_llm_judge


def llm_judge(objective: str) -> Predicate:
    """Returns true if the default judge decides that the LLM output fulfills `objective`"""
    def _inner(ctx: Context) -> PredicateResult:
        verdict, label, response = get_llm_judge().judge(objective, ctx.content)
        return PredicateResult(
            ok=verdict,
            name="llm_judge",
            metadata={
                "label": label,
                "response": response,
            }
        )
    return _inner


def llm_judge_named(name: str, objective: str) -> Predicate:
    """Returns true if the judge with the name `name` decides that the LLM output fulfills `objective`"""
    def _inner(ctx: Context) -> PredicateResult:
        verdict, label, response = get_named_llm_judge(name).judge(objective, ctx.content)
        return PredicateResult(
            ok=verdict,
            name="llm_judge_named",
            metadata={
                "label": label,
                "response": response,
                "judge_name": name,
            }
        )
    return _inner
