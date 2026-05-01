from functools import lru_cache

from lingua import (
    ConfidenceValue,
    Language,
    LanguageDetector,
    LanguageDetectorBuilder,
)

from .utils import op_compare, CompareOp
from ...logger import get_logger


logger = get_logger(__name__)


@lru_cache(maxsize=1)
def _get_language_detector() -> LanguageDetector:
    return LanguageDetectorBuilder.from_all_languages().build()


def _get_language_confidence(text: str, lang_str: str) -> float:
    return (
        _get_language_detector()
        .compute_language_confidence(text, Language.from_str(lang_str))
    )


def _get_language_confidence_values(text: str) -> list[ConfidenceValue]:
    return [
        conf
        for conf in (
            _get_language_detector()
            .compute_language_confidence_values(text)
        )
    ]


def is_most_confident_language(text: str, lang_str: str) -> tuple[bool, str]:
    conf_vals = _get_language_confidence_values(text)
    logger.debug(
        f"Lingua is_most_confident_language('{lang_str}'): "
        f"{conf_vals[0]} for {text=}"
    )
    conf_lang = conf_vals[0].language
    return (conf_lang == Language.from_str(lang_str), str(conf_lang))


def compare_language_confidence_to_value(
    text: str,
    lang_str: str,
    op: CompareOp,
    value: float
) -> tuple[bool, float]:
    conf = _get_language_confidence(text, lang_str)
    logger.debug(
        f"Lingua compare_language_confidence_to_value('{lang_str}' {op} {value}): "
        f"'{lang_str}' has {conf=:.2f} for {text=}"
    )
    return (op_compare(conf, op, value), conf)


def compare_language_confidence_to_language(
    text: str,
    lang_gt_str: str,
    lang_lt_str: str
) -> tuple[bool, tuple[float, float]]:
    conf_vals = _get_language_confidence_values(text)
    lang_gt = Language.from_str(lang_gt_str)
    lang_lt = Language.from_str(lang_lt_str)
    conf_gt = [conf.value for conf in conf_vals if conf.language == lang_gt][0]
    conf_lt = [conf.value for conf in conf_vals if conf.language == lang_lt][0]
    logger.debug(
        f"Lingua compare_language_confidence_to_language('{lang_gt_str}', '{lang_lt_str}'): "
        f"{lang_gt_str}={conf_gt:.2f} and {lang_lt_str}={conf_lt:.2f} for {text=}"
    )
    return (conf_gt > conf_lt, (conf_gt, conf_lt))
