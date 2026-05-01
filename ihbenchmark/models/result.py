from dataclasses import dataclass
from typing import Any

from litellm.types.utils import Message

from ..dsl.predicates.predicate_types import Context, PredicateResult


@dataclass
class Result:
    success: bool
    crashed: bool
    skipped: bool
    prompt_name: str
    prompt_category: str
    prompt_subcategory: str
    model_name: str
    context: Context | None
    predicate_result: PredicateResult | None
    messages: list[Message | dict[str, Any]] | None


@dataclass
class PromptSetResult:
    name: str
    control_pass_rate: float
    controls: list[Result]
    attack_pass_rate: float
    attacks: list[Result]


@dataclass
class JudgeResult:
    crashed: bool
    skipped: bool
    judge_verdict: bool
    judge_label: str
    judge_response: str
    prompt_set_rel_path: str
    user_prompt: str
    llm_response: str
    category: str
