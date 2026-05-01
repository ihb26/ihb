import logging
import pytest


# @pytest.fixture(autouse=True)
# def _disable_logging():
#     logging.disable(logging.CRITICAL)
#     yield
#     logging.disable(logging.NOTSET)


def pytest_addoption(parser):
    parser.addoption(
        "--skip-llm-judge",
        action="store_true",
        default=False,
        help="Skip tests marked with @pytest.mark.llm_judge",
    )
    parser.addoption(
        "--skip-gliner",
        action="store_true",
        default=False,
        help="Skip tests marked with @pytest.mark.gliner",
    )


def pytest_collection_modifyitems(config, items):
    skip_llm_judge = config.getoption("--skip-llm-judge")
    skip_gliner = config.getoption("--skip-gliner")

    if not (skip_llm_judge or skip_gliner):
        return

    for item in items:
        if skip_llm_judge and "llm_judge" in item.keywords:
            item.add_marker(pytest.mark.skip(reason="--skip-llm-judge set"))
        if skip_gliner and "gliner" in item.keywords:
            item.add_marker(pytest.mark.skip(reason="--skip-gliner set"))
