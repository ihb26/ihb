from typing import Final

import litellm
from litellm import completion
from litellm.types.utils import Choices

from ...config import JudgeConfig
from ...logger import get_logger
from ...resilience import run_with_retries


logger = get_logger(__name__)
litellm.drop_params = True


KEY_DEFAULT: Final[str] = "default"


class LLMJudge:
    def __init__(
        self,
        timeout: int,
        max_retries: int,
        config: JudgeConfig
    ):
        self.timeout = timeout
        self.max_retries = max_retries
        self.config = config
        self.labels_pass = [
            label.strip().lower()
            for label in self.config.labels_pass
        ]
        self.labels_fail = [
            label.strip().lower()
            for label in self.config.labels_fail
        ]

    def _try_run_completion(self, messages: list[dict[str, str]]) -> Choices:
        def _call() -> Choices:
            response = completion(
                self.config.model.name,
                base_url=self.config.model.base_url,
                messages=messages,
                temperature=self.config.model.temperature,
                reasoning_effort=self.config.model.reasoning_effort,
                thinking=self.config.model.thinking,
                timeout=self.timeout
            )
            return response.choices[0]
        
        return run_with_retries(
            _call,
            max_retries=self.max_retries,
            msg_err=f"Max retries ({self.max_retries}) reached while trying to call judge model"
        )

    def _run_judge(self, objective: str, output: str) -> str:
        prompt_user = self.config.prompt_user.format(
            objective=objective,
            output=output
        )
        messages = [
            { "role": "system", "content": self.config.prompt_judge },
            { "role": "user", "content": prompt_user },
        ]
        
        choice = self._try_run_completion(messages)
        message = choice.message
        logger.debug(f"(judge.{self.config.model.name}) {message=}")

        return message.content
    
    def judge(
        self,
        objective: str,
        output: str
    ) -> bool | tuple[bool, str, str]:
        content = self._run_judge(objective, output)
        content = content.strip().lower()
        verdict = content in self.labels_pass
        logger.debug(f"(judge.{self.config.model.name}) {verdict=} ({content=})")
        if (content not in self.labels_pass) and (content not in self.labels_fail):
            label = "?"
        else:
            label = content.upper()
        return (verdict, label, content)


_llm_judge_instance: LLMJudge | None = None
_named_llm_judge_instances: dict[str, LLMJudge] | None = None

def maybe_init_llm_judge(
    timeout: int,
    max_retries: int,
    config: JudgeConfig | None
) -> None:
    global _llm_judge_instance
    if (config is None) or (_llm_judge_instance is not None):
        return    
    _llm_judge_instance = LLMJudge(
        timeout,
        max_retries,
        config
    )
    logger.debug("Initialized LLMJudge")


def maybe_init_named_llm_judges(
    timeout: int,
    max_retries: int,
    configs: list[JudgeConfig] | None
) -> None:
    global _named_llm_judge_instances
    if (configs is None) or (_named_llm_judge_instances is not None):
        return
    
    _named_llm_judge_instances = {}
    for config in configs:
        if config.category is None:
            raise ValueError("Named LLM judge cannot have a null category")
        _named_llm_judge_instances[config.category] = LLMJudge(
            timeout,
            max_retries,
            config
        )
        logger.debug(f"Initialized LLMJudge with name '{config.category}'")


def get_llm_judge() -> LLMJudge:
    global _llm_judge_instance, _named_llm_judge_instances
    if _llm_judge_instance is None:
        if (_named_llm_judge_instances is not None) and (KEY_DEFAULT in _named_llm_judge_instances):
            return _named_llm_judge_instances[KEY_DEFAULT]
        raise RuntimeError("Tried to get LLM judge but instance was not initialized")
    return _llm_judge_instance


def get_named_llm_judge(name: str) -> LLMJudge:
    global _named_llm_judge_instances
    if _named_llm_judge_instances is None:
        raise RuntimeError("Tried to get named LLM judge but instances were not initialized")
    if name not in _named_llm_judge_instances:
        raise KeyError(f"LLM judge with name '{name}' does not exist")
    return _named_llm_judge_instances[name]
