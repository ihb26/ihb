import re
from typing import Any

from .predicate_types import Context, Predicate, PredicateResult
from ..wrappers.code import (
    get_code_detector,
    validate_schema,
    INCLUDE_CODE,
    PATTERN_CODE_BLOCK,
    LLMJudgeCode,
)


def has_code() -> Predicate:
    """Returns true if the LLM output contains code"""
    def _inner(ctx: Context) -> PredicateResult:
        det = get_code_detector()
        if isinstance(det, LLMJudgeCode):
            verdict, label, response = det.detect_code(ctx.content)
            return PredicateResult(
                ok=verdict,
                name="has_code",
                metadata={
                    "label": label,
                    "response": response,
                }
            )
        else:
            detections = get_code_detector().detect(ctx.content, enabled=INCLUDE_CODE)
            return PredicateResult(
                ok=(len(detections) > 0),
                name="has_code"
            )
    return _inner


def has_code_block() -> Predicate:
    """Returns true if the LLM output contains a markdown code block"""
    def _inner(ctx: Context) -> PredicateResult:
        match = re.search(PATTERN_CODE_BLOCK, ctx.content)
        return PredicateResult(
            ok=(match is not None),
            name="has_code_block"
        )
    return _inner


def has_json() -> Predicate:
    """Returns true if the LLM output contains JSON"""
    def _inner(ctx: Context) -> PredicateResult:
        det = get_code_detector()
        if isinstance(det, LLMJudgeCode):
            verdict, label, response = det.detect_json(ctx.content)
            return PredicateResult(
                ok=verdict,
                name="has_json",
                metadata={
                    "label": label,
                    "response": response,
                }
            )
        else:
            detections = det.detect(ctx.content)
            return PredicateResult(
                ok=(detections.get("json", 0) > 0),
                name="has_json"
            )
    return _inner


def has_json_schema(schema: dict[str, Any]) -> Predicate:
    """Returns true if the LLM output contains JSON matching the schema defined in `schema`"""
    return lambda ctx: PredicateResult(
        ok=validate_schema(ctx.content, schema),
        name="has_json_schema"
    )
