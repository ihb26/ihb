from pathlib import Path
from typing import Final

import click
import pandas as pd


DIR_ROOT: Final[Path] = Path(__file__).resolve().parent.parent
DEF_DIR_SRC: Final[Path] = DIR_ROOT / "results"
DEF_DIR_DST: Final[Path] = DIR_ROOT / "ihbenchmark-vis" / "data"


def convert_name_to_parts(name: str, prompt_set) -> tuple[str, ...]:
    if prompt_set == "System-User":
        # domain:spcomp_rulecomp_rule:subrule_type
        parts = name.split("_")
        domain, sys_prompt_complexity = parts[0].split(":")
        if sys_prompt_complexity == "basic":
            sys_prompt_complexity = "simple"
        rule_complexity = parts[1]
        rule, subrule = parts[2], ""
        if ":" in parts[2]:
            rule, subrule = parts[2].split(":")
        attack_type = parts[3]
        prompt_type = attack_type
        if attack_type != "control":
            prompt_type = "attack"
        return (
            domain,
            sys_prompt_complexity,
            rule_complexity,
            rule,
            subrule,
            attack_type,
            prompt_type,
            attack_type, # user_prompt_type
        )
    elif prompt_set == "User-Tool":
        # domain_rulecomp_scenario:userprompt:rule_type
        parts = name.split("_")
        domain = parts[0]
        rule_complexity = parts[1]
        attack_type = parts[3]
        prompt_type = attack_type
        if attack_type != "control":
            prompt_type = "attack"
        
        if parts[0] == "generic":
            scenario, user_prompt_type, rule = parts[2].split(":")
            domain = f"{domain}-{scenario}"
            sys_prompt_complexity = "simple"
        else:
            user_prompt_type, rule = parts[2].split(":")
            domain = f"agent-{domain}"
            sys_prompt_complexity = "full"
        
        return (
            domain,
            sys_prompt_complexity,
            rule_complexity,
            rule,
            "", # subrule
            attack_type,
            prompt_type,
            user_prompt_type
        )
    else:
        raise ValueError(f"Unknown prompt set: {prompt_set}")


def extract_simplified_results(
    model: str,
    df_full: pd.DataFrame,
    dst_dir: Path
) -> None:
    model = model.lower()
    if model.startswith("together_ai/"):
        model = model[len("together_ai/"):]

    prompt_sets = set()
    
    rows = []
    for _, row in df_full.iterrows():
        parts = convert_name_to_parts(row["prompt_name"], row["prompt_set"])
        prompt_sets.add(row["prompt_set"])
        rows.append({
            "model": model,
            "success": row["success"],
            "set": row["prompt_set"],
            "domain": parts[0],
            "sys_prompt_complexity": parts[1],
            "rule_complexity": parts[2],
            "rule": parts[3],
            "subrule": parts[4],
            "attack_type": parts[5],
            "prompt_type": parts[6],
            "user_prompt_type": parts[7],
        })

    model_out = model.replace("/", "_")
    if len(prompt_sets) > 1:
        fname = f"{model_out}__multi.csv"
    else:
        prompt_set = list(prompt_sets)[0].lower().replace("-", "_")
        fname = f"{model_out}__{prompt_set}.csv"
    
    df = pd.DataFrame(rows)
    df.to_csv(dst_dir / fname, index=False)


@click.command(help="Helper script to extract simplified results from completed runs")
@click.option(
    "-r",
    "--run-id",
    type=str,
    help="Run ID"
)
@click.option(
    "-s",
    "--src-dir",
    type=click.Path(path_type=Path, exists=True, file_okay=False, dir_okay=True),
    default=DEF_DIR_SRC,
    show_default=False,
    help="Optional directory to load the run from [default: ./results/]"
)
@click.option(
    "-d",
    "--dst-dir",
    type=click.Path(path_type=Path, exists=True, file_okay=False, dir_okay=True),
    default=DEF_DIR_DST,
    show_default=False,
    help="Optional directory to save the results to [default: ./vis/data/]"
)
def main(
    run_id: str,
    src_dir: Path,
    dst_dir: Path
) -> None:
    df_full = pd.read_csv(src_dir / f"{run_id}.csv")
    df_full = df_full[(~df_full["crashed"]) & (~df_full["skipped"])].copy()
    models = df_full["model_name"].unique()
    for model in models:
        df_model = df_full[df_full["model_name"] == model]
        extract_simplified_results(model, df_model, dst_dir)


if __name__ == "__main__":
    main()
