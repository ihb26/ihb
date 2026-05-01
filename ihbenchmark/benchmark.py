from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import asdict

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


class Benchmark:
    def __init__(
        self,
        config: Config,
        dataset: PromptDataset,
        n_threads: int = 0
    ):
        self.config = config
        self.dataset = dataset
        self.client = Client(
            config.timeout_client,
            config.max_retries_client,
            config.enable_langfuse,
            config.max_chat_iters
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
                    row["prompt_set"] = prompt_set_result.name
                    row["prompt_set_group"] = "control"
                    rows.append(row)
                for result in prompt_set_result.attacks:
                    row = asdict(result)
                    row["prompt_set"] = prompt_set_result.name
                    row["prompt_set_group"] = "attack"
                    rows.append(row)
        return pd.DataFrame(rows)

    def _pass_rate_to_fore(self, pass_rate: float) -> AnsiFore:
        if pass_rate >= 90.0:
            return Fore.GREEN
        elif pass_rate >= 80.0:
            return Fore.YELLOW
        elif pass_rate >= 70.0:
            return Fore.LIGHTRED_EX
        elif pass_rate >= 60.0:
            return Fore.RED
        else:
            return Fore.BLACK

    def show_results(self, results: FullResults) -> None:
        def format_cols(c):
            if isinstance(c, tuple):
                return "/".join([str(x).replace("_", " ").title() for x in c])
            return str(c).replace("_", " ").title()
        
        df = self._results_to_df(results)
        df = (
            pd.concat([
                df.groupby("model_name")["success"].mean().rename("Overall"),
                df.pivot_table(
                    index="model_name",
                    columns=["prompt_set", "prompt_set_group"],
                    values="success",
                    aggfunc="mean"
                )
            ], axis=1)
            .rename(columns=format_cols)
            .reset_index()
        )
        df = (
            df
            .rename(columns={"model_name": "Model"})
            .sort_values(by="Overall", ascending=False)
        )
        for c in df.columns:
            if c == "Model": continue
            df[c] = (df[c] * 100).round(1).astype(str) + "%"
        logger.info(f"Results:\n{df.head()}")

    def save_results(self, results: FullResults) -> None:
        ensure_result_dir_exists()
        df = self._results_to_df(results)
        df.to_csv(get_result_path(), index=False)

    def run_full(
        self,
        show_results: bool = True,
        save_results: bool = True
    ) -> None:
        logger.info(
            f"{Style.DIM}{'RUN':<6} ------- "
            f"{Style.NORMAL}Beginning {Fore.LIGHTBLUE_EX}full{Fore.RESET} benchmark run"
            f"{Style.RESET_ALL}"
        )
        results_full = []

        n_models = len(self.config.models)
        n_prompt_sets = len(self.dataset)

        for i, model in enumerate(self.config.models):
            logger.info(
                f"{Style.DIM}{'MODEL':<6} {i+1:03d}/{n_models:03d} "
                f"{Style.NORMAL}{Fore.CYAN}{model.get_name()}{Fore.RESET}"
                f"{Style.RESET_ALL}"
            )
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
                    name=prompt_set.name,
                    control_pass_rate=control_pass_rate,
                    controls=control_results,
                    attack_pass_rate=attack_pass_rate,
                    attacks=attack_results
                ))
            
            results_full.append(results_model)
        
        logger.info(
            f"{Style.DIM}{'RUN':<6} ------- "
            f"{Style.NORMAL}Completed {Fore.LIGHTBLUE_EX}full{Fore.RESET} benchmark run"
            f"{Style.RESET_ALL}"
        )

        if show_results:
            self.show_results(results_full)
        
        if save_results:
            self.save_results(results_full)

    def _run_prompts_for_model(
        self,
        prompts: list[Prompt],
        model: ModelConfig
    ) -> tuple[float, list[Result]]:
        if len(prompts) == 0:
            return (0.0, [])

        results = [None] * len(prompts)
        n_prompts = len(prompts)
        n_succ = 0

        def _thread_task(i: int, prompt: Prompt) -> tuple[int, Prompt, Result]:
            return (i, prompt, self._run_prompt_for_model(prompt, model))
        
        n_workers = max(1, self.n_threads)
        with ThreadPoolExecutor(max_workers=n_workers) as ex:
            futures = [
                ex.submit(_thread_task, i, prompt)
                for i, prompt in enumerate(prompts)
            ]
            for future in as_completed(futures):
                i, prompt, result = future.result()
                results[i] = result

                if result.skipped:
                    n_succ += 1
                    fore = Fore.WHITE
                elif result.success:
                    n_succ += 1
                    fore = Fore.GREEN
                elif result.crashed:
                    fore = Fore.BLACK
                else:
                    fore = Fore.RED

                logger.info(
                    f"{Style.DIM}{'PROMPT':<6} {i+1:03d}/{n_prompts:03d} "
                    f"{Style.NORMAL}{fore}●{Fore.RESET} "
                    f"{prompt.category}.{prompt.subcategory}.{prompt.name}"
                )

        pass_rate = round(100 * n_succ / n_prompts, 1)
        return (pass_rate, results)

    def _run_prompt_for_model(
        self,
        prompt: Prompt,
        model: ModelConfig
    ) -> Result:
        if (prompt.user_image_path is not None) and (not model.supports_vision):
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
                messages=None
            )

        pred_result = None
        success = False
        crashed = False
        context = None
        messages = None

        try:
            context, messages = self.client.run_prompt_for_model(prompt, model)
            logger.debug(f"Content: {context.content}")
            logger.debug(f"Tool calls: {context.tool_calls}")
        except Exception:
            logger.error(f"Error during prompt {prompt.name} run against {model.name}")
            logger.debug("Exception:", exc_info=True)
            crashed = True
        
        if not crashed:
            try:
                pred_result = prompt.predicate(context)
                success = pred_result.ok
            except Exception:
                logger.warning(f"Error during predicate verification for prompt {prompt.name}")
                logger.debug("Exception:", exc_info=True)
        
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
            messages=messages
        )
