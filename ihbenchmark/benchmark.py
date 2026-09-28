from concurrent.futures import FIRST_COMPLETED, ThreadPoolExecutor, wait
from dataclasses import asdict
from typing import Any, Final

import pandas as pd
from colorama import Fore, Style
from colorama.ansi import AnsiFore

from .client import Client
from .config import Config, ModelConfig
from .datasets.prompt_dataset import PromptDataset
from .dsl.wrappers.llm_judge import maybe_init_llm_judge, maybe_init_named_llm_judges
from .logger import get_logger
from .models.prompt import Prompt
from .models.result import PromptSetResult, Result
from .utils import ensure_result_dir_exists, get_result_path


logger = get_logger()

type FullResults = list[list[PromptSetResult]]

META_SKIP_REASON: Final[str] = "skip_reason"
META_FAIL_REASON: Final[str] = "fail_reason"
META_CRASH_REASON: Final[str] = "crash_reason"


class RepeatedCrashError(Exception):
    pass


class Benchmark:
    def __init__(
        self,
        config: Config,
        dataset: PromptDataset,
        n_threads: int = 0
    ):
        self.config = config
        self.dataset = dataset

        kv_text = False
        kv_mag = None
        if config.defenses:
            kv_text = config.defenses.kv_text
            kv_mag = config.defenses.kv_mag

        self.client = Client(
            config.timeout_client,
            config.max_retries_client,
            config.enable_langfuse,
            config.max_chat_iters,
            kv_text,
            kv_mag
        )
        self.n_threads = n_threads
        maybe_init_llm_judge(config.timeout_judge, config.max_retries_judge, config.judge)
        maybe_init_named_llm_judges(config.timeout_judge, config.max_retries_judge, config.judges)
    
    def _results_to_df(self, results: FullResults) -> pd.DataFrame:
        rows = []
        for model_results in results:
            for prompt_set_result in model_results:
                for result in prompt_set_result.controls:
                    row = asdict(result)
                    row["run_idx"] = prompt_set_result.run_idx
                    row["prompt_set"] = prompt_set_result.name
                    row["prompt_set_group"] = "control"
                    rows.append(row)
                for result in prompt_set_result.attacks:
                    row = asdict(result)
                    row["run_idx"] = prompt_set_result.run_idx
                    row["prompt_set"] = prompt_set_result.name
                    row["prompt_set_group"] = "attack"
                    rows.append(row)
        return pd.DataFrame(rows)

    def _pass_rate_to_fore(self, pass_rate: float) -> int:
        if pass_rate >= 90.0:
            return Fore.GREEN
        elif pass_rate >= 80.0:
            return Fore.YELLOW
        elif pass_rate >= 70.0:
            return Fore.LIGHTRED_EX
        else:
            return Fore.RED

    def _save_results(self, results: FullResults) -> None:
        ensure_result_dir_exists()
        df = self._results_to_df(results)
        df.to_csv(get_result_path(), index=False)

    def run_full(self) -> None:
        logger.info(
            f"{Style.DIM}{'RUN':<6} ------- "
            f"{Style.NORMAL}Beginning {Fore.LIGHTBLUE_EX}full{Fore.RESET} benchmark run with "
            f"{Fore.LIGHTBLUE_EX}{self.config.n_runs_per_model}{Fore.RESET} run(s) per model"
            f"{Style.RESET_ALL}"
        )
        results_full = []

        n_models = len(self.config.models)

        for i, model in enumerate(self.config.models):
            skip_model = False

            for j in range(self.config.n_runs_per_model):
                if skip_model:
                    continue

                logger.info(
                    f"{Style.DIM}{'MODEL':<6} {i+1:03d}/{n_models:03d} "
                    f"[{j+1}/{self.config.n_runs_per_model}] "
                    f"{Style.NORMAL}{Fore.CYAN}{model.get_name()}{Fore.RESET}"
                    f"{Style.RESET_ALL}"
                )
                try:
                    results_model = self._run_prompt_sets_for_model(model, run_idx=j)
                    results_full.append(results_model)
                except RepeatedCrashError:
                    skip_model = True
                    logger.error(f"Detected repeated crashes for {model.name} - skipping")
                    logger.debug("Exception:", exc_info=True)
                except KeyboardInterrupt:
                    logger.info("Keyboard interrupt - saving partial results")
                    self._save_results(results_full)
                    raise
                except Exception:
                    logger.error(f"Error running prompt sets for {model.name}")
                    logger.debug("Exception:", exc_info=True)
        
        logger.info(
            f"{Style.DIM}{'RUN':<6} ------- "
            f"{Style.NORMAL}Completed {Fore.LIGHTBLUE_EX}full{Fore.RESET} benchmark run"
            f"{Style.RESET_ALL}"
        )

        self._save_results(results_full)

    def _run_prompt_sets_for_model(
        self,
        model: ModelConfig,
        run_idx: int = 0
    ) -> list[PromptSetResult]:
        n_prompt_sets = len(self.dataset)
        results_model = []

        for j, prompt_set in enumerate(self.dataset):
            logger.info(
                f"{Style.DIM}{'SET':<6} {j+1:03d}/{n_prompt_sets:03d} "
                f"{Style.NORMAL}{Fore.MAGENTA}{prompt_set.name} (controls){Fore.RESET}"
                f"{Style.RESET_ALL}"
            )
            control_pass_rate, control_results = self._run_prompts_for_model(prompt_set.controls, model)
            if len(control_results):
                fore = self._pass_rate_to_fore(control_pass_rate)
                logger.info(
                    f"{Style.DIM}{'SET':<6} {j+1:03d}/{n_prompt_sets:03d} "
                    f"{Style.NORMAL}{fore}■{Fore.RESET} {Fore.CYAN}{model.get_name()}{Fore.RESET} passed "
                    f"{fore}{control_pass_rate:.1f}%{Fore.RESET} of "
                    f"{Fore.MAGENTA}{prompt_set.name} (controls){Fore.RESET} tests"
                )
            
            if (control_pass_rate / 100) < self.config.controls_threshold:
                logger.info(
                    f"{Style.DIM}{'SET':<6} {j+1:03d}/{n_prompt_sets:03d} "
                    f"{Style.NORMAL}Skipping attack prompts as control pass rate is below configured "
                    f"threshold of {Fore.CYAN}{self.config.controls_threshold}{Fore.RESET}"
                    f"{Style.RESET_ALL}"
                )
                results_model.append(PromptSetResult(
                    run_idx=run_idx,
                    name=prompt_set.name,
                    control_pass_rate=control_pass_rate,
                    controls=control_results,
                    attack_pass_rate=0.0,
                    attacks=[]
                ))
                continue
            
            if len(prompt_set.attacks):
                logger.info(
                    f"{Style.DIM}{'SET':<6} {j+1:03d}/{n_prompt_sets:03d} "
                    f"{Style.NORMAL}{Fore.MAGENTA}{prompt_set.name} (attacks){Fore.RESET}"
                    f"{Style.RESET_ALL}"
                )
                attack_pass_rate, attack_results = self._run_prompts_for_model(prompt_set.attacks, model)
                
                fore = self._pass_rate_to_fore(attack_pass_rate)
                logger.info(
                    f"{Style.DIM}{'SET':<6} {j+1:03d}/{n_prompt_sets:03d} "
                    f"{Style.NORMAL}{fore}■{Fore.RESET} {Fore.CYAN}{model.get_name()}{Fore.RESET} passed "
                    f"{fore}{attack_pass_rate:.1f}%{Fore.RESET} of "
                    f"{Fore.MAGENTA}{prompt_set.name} (attacks){Fore.RESET} tests"
                )
            else:
                attack_pass_rate, attack_results = 100.0, []

            results_model.append(PromptSetResult(
                run_idx=run_idx,
                name=prompt_set.name,
                control_pass_rate=control_pass_rate,
                controls=control_results,
                attack_pass_rate=attack_pass_rate,
                attacks=attack_results
            ))

        return results_model

    def _run_prompts_for_model(
        self,
        prompts: list[Prompt],
        model: ModelConfig
    ) -> tuple[float, list[Result]]:
        if len(prompts) == 0:
            return (0.0, [])

        results: list[Result | None] = [None] * len(prompts)
        n_prompts = len(prompts)
        n_succ = 0

        n_crash = 0
        n_total = 0

        def _thread_task(i: int, prompt: Prompt) -> tuple[int, Prompt, Result]:
            return (i, prompt, self._run_prompt_for_model(prompt, model))
        
        n_workers = max(1, self.n_threads)
        prompts_iter = iter(enumerate(prompts))
        with ThreadPoolExecutor(max_workers=n_workers) as ex:
            futures = set()
            for _ in range(min(n_workers, n_prompts)):
                i, prompt = next(prompts_iter)
                futures.add(ex.submit(_thread_task, i, prompt))

            while futures:
                completed, _ = wait(futures, return_when=FIRST_COMPLETED)
                futures.difference_update(completed)

                for future in completed:
                    i, prompt, result = future.result()
                    results[i] = result

                    n_total += 1
                    if result.skipped:
                        n_succ += 1
                        fore = Fore.WHITE
                    elif result.success:
                        n_succ += 1
                        fore = Fore.GREEN
                    elif result.crashed:
                        n_crash += 1
                        fore = Fore.BLACK
                    else:
                        fore = Fore.RED

                    logger.info(
                        f"{Style.DIM}{'PROMPT':<6} {i+1:03d}/{n_prompts:03d} "
                        f"{Style.NORMAL}{fore}●{Fore.RESET} "
                        f"{prompt.category}.{prompt.subcategory}.{prompt.name}"
                    )

                if (n_crash / n_total >= 0.8) and (n_crash >= 5):
                    for future in futures:
                        future.cancel()
                    raise RepeatedCrashError(
                        f"Model {model.name} crashed repeatedly "
                        f"({n_crash}/{n_total} prompts)"
                    )

                for _ in completed:
                    try:
                        i, prompt = next(prompts_iter)
                    except StopIteration:
                        break
                    futures.add(ex.submit(_thread_task, i, prompt))

        pass_rate = round(100 * n_succ / n_prompts, 1)
        return (pass_rate, results) # type: ignore

    def _run_prompt_for_model(
        self,
        prompt: Prompt,
        model: ModelConfig
    ) -> Result:
        metadata: dict[str, Any] = {
            META_SKIP_REASON: None,
            META_FAIL_REASON: None,
            META_CRASH_REASON: None,
        }
        
        if (prompt.user_image_path is not None) and (not model.supports_vision):
            metadata[META_SKIP_REASON] = "Image path provided but model does not support vision"
            return Result(
                success=True,
                crashed=False,
                skipped=True,
                prompt_name=prompt.name,
                prompt_category=prompt.category,
                prompt_subcategory=prompt.subcategory,
                model_name=model.get_name(),
                context=None,
                predicate_result=None,
                messages=None,
                metadata=metadata
            )

        # NOTE: reinitialise agent
        prompt.maybe_init_agent()
        
        pred_result = None
        success = False
        crashed = False
        empty = False
        context = None
        messages = None

        try:
            context, messages, (n_inp, n_out) = self.client.run_prompt_for_model(
                prompt,
                model,
                self.config.defenses
            )
            if len(context.content.strip()) == 0:
                logger.warning(f"Received empty response from {model.name}")
                empty = True
            logger.debug(f"Content: {context.content}")
            logger.debug(f"Tool calls: {context.tool_calls}")
            logger.debug(f"Tokens: inp={n_inp} out={n_out}")
        except Exception as exc:
            n_inp, n_out = 0, 0
            logger.error(f"Error during prompt {prompt.name} run against {model.name}")
            logger.debug("Exception:", exc_info=True)
            crashed = True
            metadata[META_CRASH_REASON] = f"Exception: {exc}"
        
        if not crashed:
            if empty:
                success = False
                metadata[META_FAIL_REASON] = "Empty response"
            else:
                try:
                    assert prompt.predicate is not None and context is not None
                    pred_result = prompt.predicate(context)
                    success = pred_result.ok
                    if not success:
                        metadata[META_FAIL_REASON] = "Predicate returned false"
                except Exception as exc:
                    logger.warning(f"Error during predicate verification for prompt {prompt.name}")
                    logger.debug("Exception:", exc_info=True)
                    metadata[META_FAIL_REASON] = f"Exception: {exc}"
        
        return Result(
            success=success,
            crashed=crashed,
            skipped=False,
            prompt_name=prompt.name,
            prompt_category=prompt.category,
            prompt_subcategory=prompt.subcategory,
            model_name=model.get_name(),
            context=context,
            predicate_result=pred_result,
            messages=messages,
            input_tokens=n_inp,
            output_tokens=n_out,
            metadata=metadata
        )
