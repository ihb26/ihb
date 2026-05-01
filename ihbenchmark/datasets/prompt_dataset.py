import json
from collections.abc import Iterator
from pathlib import Path
from typing import Any

from ..logger import get_logger
from ..models.prompt import Prompt, PromptSet
from ..utils import get_dir_root


logger = get_logger(__name__)


class PromptDataset:
    def __init__(self, prompt_set_paths: list[str]):
        self.prompt_sets = [
            self._load_prompt_set(path)
            for path in prompt_set_paths
        ]
    
    def __len__(self) -> int:
        return len(self.prompt_sets)
    
    def __getitem__(self, idx: int) -> PromptSet:
        return self.prompt_sets[idx]
    
    def __iter__(self) -> Iterator[PromptSet]:
        return iter(self.prompt_sets)
    
    def _load_prompt_set(self, prompt_set_rel_path: str) -> PromptSet:
        prompt_set_path = get_dir_root() / prompt_set_rel_path
        if not prompt_set_path.exists():
            raise FileNotFoundError(f"Prompt set file does not exist: {prompt_set_path}")
        
        with open(prompt_set_path, "r") as f:
            data = json.load(f)
        
        name = data.get("name", "Unnamed")
        description = data.get("description", "No description provided.")
        tools_all = data.get("tools", {})
        controls_raw = data.get("controls", [])
        attacks_raw = data.get("attacks", [])

        if (not len(controls_raw)) and (not len(attacks_raw)):
            raise ValueError(f"No prompts found in dataset: {prompt_set_path}")
        
        controls = self._json_to_prompts(controls_raw, prompt_set_path, tools_all)
        attacks = self._json_to_prompts(attacks_raw, prompt_set_path, tools_all)

        logger.debug(
            f"Successfully loaded '{name}' prompt set with "
            f"{len(controls)} control prompt(s) and "
            f"{len(attacks)} attack prompt(s)"
        )

        return PromptSet(
            name=name,
            description=description,
            controls=controls,
            attacks=attacks
        )
        
    def _json_to_prompts(
        self,
        data_prompts: dict[str, Any],
        path_json: Path,
        tools_all: dict[str, dict[str, Any]]
    ) -> list[Prompt]:
        prompts = []
        for prompt_json in data_prompts:
            try:
                prompt = Prompt(**prompt_json)
                prompt.load_image_if_exists(path_json)
                prompt.maybe_assign_tools(tools_all)
                prompts.append(prompt)
            except Exception:
                logger.exception("Error loading prompt")
        return prompts
