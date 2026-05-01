import os
import uuid
from datetime import datetime, timezone
from functools import lru_cache
from pathlib import Path


def get_dir_root() -> Path:
    return Path(__file__).resolve().parent.parent


def get_time_utc() -> str:
    return datetime.now(tz=timezone.utc).strftime("%Y%m%d-%H%M%S")


@lru_cache(maxsize=1)
def get_run_id() -> str:
    return str(uuid.uuid4())


def is_langfuse_configured() -> bool:
    return (
        (os.getenv("LANGFUSE_HOST") is not None) and
        (os.getenv("LANGFUSE_PUBLIC_KEY") is not None) and
        (os.getenv("LANGFUSE_SECRET_KEY") is not None)
    )


def ensure_result_dir_exists() -> None:
    os.makedirs(
        get_dir_root() / "results",
        exist_ok=True
    )


def get_result_path() -> Path:
    return (
        get_dir_root() /
        "results" /
        f"{get_run_id()}.csv"
    )
