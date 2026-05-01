import os
import logging
from logging import FileHandler, Logger
from pathlib import Path

from colorlog import ColoredFormatter
from dotenv import load_dotenv

from .utils import (
    get_dir_root,
    get_run_id,
    get_time_utc,
)


load_dotenv()


def get_stream_log_level() -> int:
    match os.getenv("IHB_LOG_LEVEL", "3"):
        case "0":
            return logging.CRITICAL
        case "1":
            return logging.ERROR
        case "2":
            return logging.WARNING
        case "3":
            return logging.INFO
        case "4":
            return logging.DEBUG
        case _:
            return logging.INFO


def _ensure_log_dir_exists() -> None:
    os.makedirs(
        get_dir_root() / "logs",
        exist_ok=True
    )


def _get_log_path() -> Path:
    return (
        get_dir_root() /
        "logs" /
        f"{get_time_utc()}_{get_run_id()}.log"
    )


_shared_file_handler: FileHandler | None = None
def get_logger(name: str = "ihbenchmark") -> Logger:
    global _shared_file_handler
    _ensure_log_dir_exists()

    logger = logging.getLogger(name)
    logger.setLevel(logging.DEBUG)

    if not logger.handlers:
        if _shared_file_handler is None:
            path_log = _get_log_path()
            file_handler = logging.FileHandler(path_log)
            file_handler.setLevel(logging.DEBUG)
            file_formatter = logging.Formatter(
                "%(asctime)s | %(name)s | %(levelname)s | %(message)s"
            )
            file_handler.setFormatter(file_formatter)
            _shared_file_handler = file_handler
        
        stream_handler = logging.StreamHandler()
        stream_handler.setLevel(get_stream_log_level())
        stream_formatter = ColoredFormatter(
            "%(asctime)s "
            "%(log_color)s%(levelname)-8s%(reset)s "
            "%(name_log_color)s%(name)-20s%(reset)s "
            "%(message)s",
            log_colors={
                "DEBUG": "cyan",
                "INFO": "green",
                "WARNING": "yellow",
                "ERROR": "red",
                "CRITICAL": "bold_red",
            },
            secondary_log_colors={
                "name": {
                    "DEBUG": "thin_white",
                    "INFO": "thin_white",
                    "WARNING": "thin_white",
                    "ERROR": "thin_white",
                    "CRITICAL": "thin_white",
                },
            },
            style="%"
        )
        
        stream_handler.setFormatter(stream_formatter)
        
        logger.addHandler(_shared_file_handler)
        logger.addHandler(stream_handler)
    
    logger.propagate = False
    return logger
