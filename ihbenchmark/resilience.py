import logging
from typing import Any, Callable, TypeVar

from litellm.exceptions import (
    BadRequestError,
    OpenAIError,
    Timeout,
    RateLimitError,
    APIConnectionError,
    APIError,
    ServiceUnavailableError,
    InternalServerError,
)
from tenacity import (
    before_sleep_log,
    retry,
    RetryError,
    retry_if_exception_type,
    stop_after_attempt,
    wait_random_exponential,
)

from .logger import get_logger


logger = get_logger(__name__)

T = TypeVar("T")


def _mk_completion_retry(max_retries: int) -> Any:
    return retry(
        reraise=True,
        stop=stop_after_attempt(max_retries),
        wait=wait_random_exponential(multiplier=3, max=90),
        retry=retry_if_exception_type((
            BadRequestError,            # 400 (this technically indicates a user error but TogetherAI is weird)
            OpenAIError,                # 400 (same as above)
            Timeout,                    # 408
            RateLimitError,             # 429
            APIConnectionError,         # 500
            APIError,                   # 500
            ServiceUnavailableError,    # 503
            InternalServerError,        # 500+
        )),
        before_sleep=before_sleep_log(logger, logging.WARNING)
    )


def run_with_retries(
    f: Callable[[], T],
    *,
    max_retries: int,
    msg_err: str
) -> T:
    try:
        return _mk_completion_retry(max_retries)(f)()
    except KeyboardInterrupt:
        raise
    except RetryError as e:
        raise RuntimeError(msg_err) from e
    except Exception as e:
        raise RuntimeError(msg_err) from e
