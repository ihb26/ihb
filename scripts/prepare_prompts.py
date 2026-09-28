import json
import random
from functools import lru_cache
from pathlib import Path
from typing import Final

import click


RANDOM_SEED: Final[int] = 1337

DIR_ROOT: Final[Path] = Path(__file__).resolve().parent.parent
DEF_PATH_OUTPUT: Final[Path] = DIR_ROOT / "data" / "prompts_policy_behaviors.json"
DEF_PATH_TEMPLATES: Final[Path] = DIR_ROOT / "resources" / "templates" / "policy_puppetry.json"
DEF_PATH_SEEDS: Final[Path] = DIR_ROOT / "resources" / "advbench" / "harmful_behaviors_filtered.txt"
DEF_PS_NAME: Final[str] = "Unnamed"
DEF_PS_DESC: Final[str] = "No description provided."
DEF_SYSTEM_PROMPT: Final[str] = "You are a helpful assistant."

LEETSPEAK_MAP: Final[dict[str, str]] = {
    "a": "4",
    "e": "3",
    "g": "6",
    "i": "1",
    "l": "1",
    "o": "0",
    "s": "5",
    "t": "7",
}


def load_templates(path_templates: Path) -> list[dict[str, str]]:
    with open(path_templates, "r") as f:
        return json.loads(f.read())["templates"]


def load_seeds(path_seeds: Path, n_seeds: int) -> list[str]:
    seeds = []
    with open(path_seeds, "r") as f:
        for line in f.readlines():
            line = line.strip()
            if len(line):
                seeds.append(line)
    if (n_seeds == -1) or (n_seeds > len(seeds)):
        return seeds
    random.shuffle(seeds)
    return seeds[:n_seeds]


@lru_cache()
def to_leetspeak(seed: str, pct: float = 0.7) -> str:
    return "".join([
        LEETSPEAK_MAP[char]
        if (char in LEETSPEAK_MAP) and (random.random() < pct)
        else char
        for char in seed
    ])


def transform_seed(seed: str, transform: str) -> str:
    match transform:
        case "leetspeak":
            return to_leetspeak(seed)
        case "none":
            return seed
        case _:
            return seed


@click.command(help="Helper script to prepare policy puppetry prompt set")
@click.option(
    "--name",
    type=str,
    default=DEF_PS_NAME,
    show_default=True,
    help=f"Optional prompt set name",
)
@click.option(
    "--description",
    type=str,
    default=DEF_PS_DESC,
    show_default=True,
    help=f"Optional prompt set description",
)
@click.option(
    "--output-path",
    type=click.Path(path_type=Path, exists=True, file_okay=True, dir_okay=False),
    default=DEF_PATH_OUTPUT,
    show_default=False,
    help="Path to save prompt set to [default: ./data/prompts_policy_behaviors.json]",
)
@click.option(
    "--templates-path",
    type=click.Path(path_type=Path, exists=True, file_okay=True, dir_okay=False),
    default=DEF_PATH_TEMPLATES,
    show_default=False,
    help="Path to prompt templates [default: ./resources/templates/policy_puppetry.json]",
)
@click.option(
    "--seeds-path",
    type=click.Path(path_type=Path, exists=True, file_okay=True, dir_okay=False),
    default=DEF_PATH_SEEDS,
    show_default=False,
    help="Path to seed prompts [default: ./resources/advbench/harmful_behaviors_filtered.txt]",
)
@click.option(
    "--n-seeds",
    type=int,
    default=-1,
    show_default=True,
    help="Number of seed prompts to use, or -1 to use all seeds",
)
@click.option(
    "--system-prompt",
    type=str,
    default=DEF_SYSTEM_PROMPT,
    show_default=True,
    help=f"System prompt to use with each of the user prompts",
)
@click.option(
    "--skip-controls",
    is_flag=True,
    help="Do not generate control prompts",
)
def main(
    name: str,
    description: str,
    output_path: Path,
    templates_path: Path,
    seeds_path: Path,
    n_seeds: int,
    system_prompt: str,
    skip_controls: bool
) -> None:
    random.seed(RANDOM_SEED)

    templates = load_templates(templates_path)
    seeds = load_seeds(seeds_path, n_seeds)

    unique_seeds_seen = set()
    controls, attacks = [], []
    for i, seed in enumerate(seeds):
        seed_esc_quotes = seed.replace("'", "\\'")
        expression = f"llm_judge('{seed_esc_quotes}')"

        for template in templates:
            format = template["format"]
            _type = template["type"]

            seed_transformer = template.get("seed_transformer", "none")
            seed_final = transform_seed(seed, seed_transformer)
            
            if (seed, seed_transformer) not in unique_seeds_seen:
                unique_seeds_seen.add((seed, seed_transformer))
                if not skip_controls:
                    controls.append({
                        "name": f"plain-{i:03d}",
                        "category": "plaintext",
                        "subcategory": seed_transformer,
                        "system_prompt": system_prompt,
                        "user_prompt": seed_final,
                        "user_image_path": None,
                        "tool_response": None,
                        "tools": None,
                        "pass_condition": "",
                        "expression": expression,
                        "rationale": "",
                    })

            prompt = template["template"].replace("{{PROMPT}}", seed_final)
            attacks.append({
                "name": f"pp-{format}-{_type}-{i:03d}",
                "category": format,
                "subcategory": _type,
                "system_prompt": system_prompt,
                "user_prompt": prompt,
                "user_image_path": None,
                "tool_response": None,
                "tools": None,
                "pass_condition": "",
                "expression": expression,
                "rationale": "",
            })
    
    output = {
        "$schema": "./schema.json",
        "name": name,
        "description": description,
        "seeds": seeds,
        "controls": controls,
        "attacks": attacks,
    }
    with open(output_path, "w+") as f:
        json.dump(output, f, indent=4)


if __name__ == "__main__":
    main()
