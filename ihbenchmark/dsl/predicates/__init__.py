from typing import Any, Callable

from .code import (
    has_code,
    has_code_block,
    has_json,
    has_json_schema,
)
from .gliner import discusses_topic, has_refusal
from .judge import llm_judge, llm_judge_named
from .lingua import is_language, is_language_conf, is_language_more_conf
from .logical import AND, OR, NOT
from .nlp import sentence_count, word_count
from .string import (
    contains,
    contains_cased,
    contains_norm,
    starts_with,
    starts_with_cased,
    starts_with_norm,
    ends_with,
    ends_with_cased,
    ends_with_norm,
    has_digits,
    has_list,
    has_list_strict,
    matches,
)
from .tools import (
    has_any_tool_call,
    has_tool_call,
    has_only_tool_call,
    has_tool_call_with_params,
    has_tool_call_with_param_value,
    has_tool_call_with_param_value_regex,
)


FUNCTIONS: dict[str, Callable[..., Any]] = {
    # Logical
    "AND": AND,
    "OR": OR,
    "NOT": NOT,
    # Strings
    "contains": contains,
    "contains_cased": contains_cased,
    "contains_norm": contains_norm,
    "starts_with": starts_with,
    "starts_with_cased": starts_with_cased,
    "starts_with_norm": starts_with_norm,
    "ends_with": ends_with,
    "ends_with_cased": ends_with_cased,
    "ends_with_norm": ends_with_norm,
    "has_digits": has_digits,
    "has_list": has_list,
    "has_list_strict": has_list_strict,
    "matches": matches,
    # Tools
    "has_any_tool_call": has_any_tool_call,
    "has_tool_call": has_tool_call,
    "has_only_tool_call": has_only_tool_call,
    "has_tool_call_with_params": has_tool_call_with_params,
    "has_tool_call_with_param_value": has_tool_call_with_param_value,
    "has_tool_call_with_param_value_regex": has_tool_call_with_param_value_regex,
    # LLM-as-a-judge
    "llm_judge": llm_judge,
    "llm_judge_named": llm_judge_named,
    # GLiNER2
    # NOTE: these are experimental and unreliable
    "discusses_topic": discusses_topic,
    "has_refusal": has_refusal, 
    # Lingua
    "is_language": is_language,
    "is_language_conf": is_language_conf,
    "is_language_more_conf" : is_language_more_conf,
    # Code detection
    "has_code": has_code,
    "has_code_block": has_code_block,
    "has_json": has_json,
    "has_json_schema": has_json_schema,
    # NLP
    "sentence_count": sentence_count,
    "word_count": word_count,
}
