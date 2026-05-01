import pandas as pd
from collections.abc import Iterator

from ..logger import get_logger
from ..models.prompt import JudgePrompt
from ..utils import get_dir_root


logger = get_logger(__name__)


class JudgeDataset:
    COL_PROMPT: str = "prompt"
    COL_RESPONSE: str = "response"
    COL_CATEGORY: str = "category"

    def __init__(self, prompt_set_paths: list[str]):
        self.prompts: list[JudgePrompt] = []
        self.categories: set[str] = set()
        for path in prompt_set_paths:
            self.prompts.extend(self._load_prompt_set(path))
        logger.debug(
            "Successfully loaded all prompt sets and found "
            f"{len(self.categories)} unique categories"
        )
    
    def __len__(self) -> int:
        return len(self.prompts)

    def __getitem__(self, idx: int) -> JudgePrompt:
        return self.prompts[idx]
    
    def __iter__(self) -> Iterator[JudgePrompt]:
        return iter(self.prompts)
    
    def _load_prompt_set(self, prompt_set_rel_path: str) -> list[JudgePrompt]:
        prompt_set_path = get_dir_root() / prompt_set_rel_path
        if not prompt_set_path.exists():
            raise FileNotFoundError(f"Prompt set file does not exist: {prompt_set_path}")
        
        df = pd.read_csv(prompt_set_path)
        columns = df.columns.values.tolist()
        if (self.COL_PROMPT not in columns) or (self.COL_RESPONSE not in columns):
            raise ValueError(
                f"Prompt set file ({prompt_set_rel_path}) is missing at least "
                f"one required column: {self.COL_PROMPT}, {self.COL_RESPONSE}"
            )
        has_category = (self.COL_CATEGORY in columns)

        prompts = []
        for _, row in df.iterrows():
            user_prompt = row[self.COL_PROMPT]
            llm_response = row[self.COL_RESPONSE]
            category = None
            if has_category:
                category = row[self.COL_CATEGORY]
                self.categories.add(category)
            prompts.append(JudgePrompt(
                prompt_set_rel_path,
                user_prompt,
                llm_response,
                category
            ))
        
        logger.debug(f"Successfully loaded {prompt_set_rel_path} prompts with {len(prompts)} prompt(s)")
        return prompts
