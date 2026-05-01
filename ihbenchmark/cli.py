from pathlib import Path

import click
from colorama import init as colorama_init
from dotenv import load_dotenv

from .benchmark import Benchmark
from .config import Config, load_config, DEF_PATH_CONFIG
from .datasets.judge_dataset import JudgeDataset
from .datasets.prompt_dataset import PromptDataset
from .judge import Judge
from .logger import get_logger
from .utils import get_run_id


colorama_init()
load_dotenv()
logger = get_logger()


def run_benchmark(run_id: str, config: Config, n_threads: int):
    try:
        dataset = PromptDataset(prompt_set_paths=config.prompt_sets)
        logger.info(f"Loaded dataset (n_prompt_sets={len(dataset)})")
    except Exception:
        logger.critical("Failed to load dataset - abandoning run", exc_info=True)
        return

    try:
        benchmark = Benchmark(config, dataset, n_threads=n_threads)
        benchmark.run_full()
        logger.info(f"Finished run {run_id}")
    except KeyboardInterrupt:
        logger.info(f"Stopping run {run_id}")


def run_judge(run_id: str, config: Config, n_threads: int):
    try:
        dataset = JudgeDataset(prompt_set_paths=config.prompt_sets)
        logger.info(f"Loaded dataset (n_prompts={len(dataset)})")
    except Exception:
        logger.critical("Failed to load dataset - abandoning run", exc_info=True)
        return
    
    try:
        judge = Judge(config, dataset, n_threads=n_threads)
        judge.run_full()
        logger.info(f"Finished run {run_id}")
    except KeyboardInterrupt:
        logger.info(f"Stopping run {run_id}")


@click.command(help="IHB: Prompt Injection Benchmarking Suite")
@click.option(
    "-c",
    "--config-path",
    type=click.Path(path_type=Path, exists=True, file_okay=True, dir_okay=False),
    default=DEF_PATH_CONFIG,
    show_default=False,
    help="Optional path to a configuration file [default: ./config/config.yaml]",
)
@click.option(
    "-j",
    "--judge-only",
    is_flag=True,
    help="Optionally only run the LLM judge on pre-generated prompts",
)
@click.option(
    "-t",
    "--n-threads",
    type=click.IntRange(min=0),
    default=0,
    show_default=True,
    help="Optional number of requests to run in parallel, or 0 for a single thread",
)
def main(
    config_path: Path,
    judge_only: bool,
    n_threads: int
) -> None:
    run_id = get_run_id()
    
    if judge_only:
        logger.info(f"Initializing judge run {run_id}")
    else:
        logger.info(f"Initializing run {run_id}")

    try:
        config = load_config(config_path)
        logger.info("Loaded config")
    except Exception:
        logger.critical("Failed to load config - abandoning run", exc_info=True)
        return
    
    if judge_only:
        run_judge(run_id, config, n_threads)
    else:
        run_benchmark(run_id, config, n_threads)
