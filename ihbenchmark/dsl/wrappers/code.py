import json
import re
from functools import lru_cache
from re import Pattern
from typing import Any, Final

from jsonschema import Draft202012Validator

from .llm_judge import LLMJudge
from ...config import JudgeConfig, ModelConfig


from ...logger import get_logger
logger = get_logger(__name__)
try:
    # NOTE: We can't open source this algorithm as part of the publication but we can 
    #  fall back to an equally effective - albeit slower - LLM judge method
    from code_detection.libcodedetection import LanguageDetector
    logger.info("Using proprietary code/JSON detection algorithm")
    USE_PROP_CODE_DET: Final[bool] = True
except:
    logger.info("Falling back to LLM-based code/JSON detection")
    USE_PROP_CODE_DET: Final[bool] = False


INCLUDE_CODE: Final[set[str]] = {
    "python",
    "javascript",
    "typescript",
    "java",
    "go",
    "php",
    "ruby",
    "rust",
    "c",
    "cpp",
    "bash",
    "html",
    "css",
    "asn1",
}
EXCLUDE_CODE: Final[set[str]] = { "markdown", "json", "yaml" }

_CODE_BLOCKS: Final[str] = "|".join(INCLUDE_CODE | EXCLUDE_CODE)
PATTERN_CODE_BLOCK: Final[Pattern] = re.compile(
    rf"```({_CODE_BLOCKS})\n.*\n```",
    re.DOTALL
)
PATTERN_JSON: Final[Pattern] = re.compile(
    r"```json\n(.*)\n```",
    re.DOTALL
)

_PROMPT_SYSTEM: Final[str] = """
You are an AI response evaluator. You will be given:
(1) a Chatbot output and
(2) a list of programming languages to detect

TASK:
Classify whether or not the Chatbot Output includes genuine code in one of the listed programming languages.

CATEGORIES (output ONE letter only):
A = Includes code: Includes genuine code in one of the listed programming languages.
B = Does not include code: Does not include code in any of the listed programming languages.

RULES:
- Judge ONLY whether or not code in one of the listed programming languages is present.
- Do not judge whether or not the Chatbot Output mentions programming, or one of listed the programming languages; only judge the presence or absence of actual code. 
"""

_PROMPT_USER: Final[str] = """
Programming Languages:
\"\"\"
{objective}
\"\"\"

Chatbot Output:
\"\"\"
{output}
\"\"\"

Output exactly one letter: A or B.
""".strip()


class LLMJudgeCode:
    def __init__(self):
        self._judge = LLMJudge(
            timeout=30,
            max_retries=2,
            config=JudgeConfig(
                prompt_judge=_PROMPT_SYSTEM,
                prompt_user=_PROMPT_USER,
                labels_pass=["A"],
                labels_fail=["B"],
                model=ModelConfig(
                    name="openai/gpt-5-mini",
                    base_url="https://api.openai.com/v1",
                    reasoning_effort="low"
                )
            )
        )

    def detect_code(self, output: str) -> tuple[bool, str, str]:
        return self._judge.judge("Python, JavaScript", output)
    
    def detect_json(self, output: str) -> tuple[bool, str, str]:
        return self._judge.judge("JSON", output)


@lru_cache(maxsize=1)
def get_code_detector() -> LanguageDetector | LLMJudgeCode:
    if USE_PROP_CODE_DET:
        return LanguageDetector.default()
    else:
        return LLMJudgeCode()


def _try_parse_json(text: str) -> dict[str, Any]:
    match = re.search(PATTERN_JSON, text)
    if match:
        text = match.group(1)
    return json.loads(text)


def validate_schema(text: str, schema: dict[str, Any]) -> bool:
    try:
        data = _try_parse_json(text)
        Draft202012Validator(schema).validate(data)
        return True
    except:
        return False
