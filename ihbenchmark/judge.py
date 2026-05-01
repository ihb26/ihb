from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import asdict

import pandas as pd
from colorama import Fore, Style

from .config import Config
from .datasets.judge_dataset import JudgeDataset
from .dsl.wrappers.llm_judge import LLMJudge, KEY_DEFAULT
from .logger import get_logger
from .models.prompt import JudgePrompt
from .models.result import JudgeResult
from .utils import ensure_result_dir_exists, get_result_path


logger = get_logger(__name__)


class Judge:
    def __init__(
        self,
        config: Config,
        dataset: JudgeDataset,
        n_threads: int = 0
    ):
        self.config = config
        self.dataset = dataset
        self.n_threads = n_threads
        self.has_categories, self.judges = self._init_llm_judges()
    
    def _init_llm_judges(self) -> tuple[bool, dict[str, LLMJudge]]:
        if self.config.judge is not None:
            judge = LLMJudge(
                self.config.timeout_judge,
                self.config.max_retries_judge,
                self.config.judge
            )
            return (False, { KEY_DEFAULT: judge })
        
        if self.config.judges is None:
            raise ValueError("At least one LLM judge must be configured")

        configured_categories = set()
        judges = {}
        
        for judge_config in self.config.judges:
            category = judge_config.category
            configured_categories.add(category)
            judges[category] = LLMJudge(
                self.config.timeout_judge,
                self.config.max_retries_judge,
                judge_config
            )
        
        missing_categories = self.dataset.categories - configured_categories
        if len(missing_categories):
            raise ValueError(f"No judge configured for the categories: {missing_categories}")

        return (True, judges)
    
    def save_results(self, results: list[JudgeResult]) -> None:
        ensure_result_dir_exists()
        df = pd.DataFrame(list(map(asdict, results)))
        df.to_csv(get_result_path(), index=False)

    def run_full(self, save_results: bool = True) -> None:
        logger.info(
            f"{Style.DIM}{'RUN':<6} --------- "
            f"{Style.NORMAL}Beginning {Fore.LIGHTBLUE_EX}full{Fore.RESET} judge run"
            f"{Style.RESET_ALL}"
        )

        results = [None] * len(self.dataset)
        n_prompts = len(self.dataset)
        n_succ, n_fail, n_crsh = 0, 0, 0

        def _thread_task(i: int, prompt: JudgePrompt) -> tuple[int, JudgePrompt, JudgeResult]:
            return (i, prompt, self._run_prompt(prompt))
        
        n_workers = max(1, self.n_threads)
        with ThreadPoolExecutor(max_workers=n_workers) as ex:
            futures = [
                ex.submit(_thread_task, i, prompt)
                for i, prompt in enumerate(self.dataset)
            ]
            for future in as_completed(futures):
                i, _, result = future.result()
                results[i] = result
                
                if result.skipped or result.crashed:
                    n_crsh += 1
                    fore = Fore.WHITE
                elif result.judge_verdict:
                    n_succ += 1
                    fore = Fore.GREEN
                else:
                    n_fail += 1
                    fore = Fore.RED

                logger.info(
                    f"{Style.DIM}{'PROMPT':<6} {i+1:04d}/{n_prompts:04d} "
                    f"{Style.NORMAL}{fore}●{Fore.RESET} "
                    f"{result.category}: verdict={result.judge_verdict} label={result.judge_label}"
                )
        
        logger.info(
            f"{Style.DIM}{'RUN':<6} --------- "
            f"{Style.NORMAL}Completed {Fore.LIGHTBLUE_EX}full{Fore.RESET} judge run"
            f"{Style.RESET_ALL}"
        )

        if save_results:
            self.save_results(results)

    def _run_prompt(self, prompt: JudgePrompt) -> JudgeResult:
        category = prompt.category if self.has_categories else KEY_DEFAULT
        judge = self.judges.get(category)
        
        if judge is None:
            logger.error(f"No judge found for {category=}")
            return JudgeResult(
                crashed=False,
                skipped=True,
                judge_verdict=False,
                judge_label="?",
                judge_response="",
                prompt_set_rel_path=prompt.prompt_set_rel_path,
                user_prompt=prompt.user_prompt,
                llm_response=prompt.llm_response,
                category=category
            )
        
        crashed = False
        verdict = False
        label = ""
        response = ""

        try:
            verdict, label, response = judge.judge(prompt.user_prompt, prompt.llm_response)
        except Exception:
            logger.error("Error calling judge")
            logger.debug("Exception:", exc_info=True)
            crashed = True
        
        return JudgeResult(
            crashed=crashed,
            skipped=False,
            judge_verdict=verdict,
            judge_label=label,
            judge_response=response,
            prompt_set_rel_path=prompt.prompt_set_rel_path,
            user_prompt=prompt.user_prompt,
            llm_response=prompt.llm_response,
            category=category
        )
