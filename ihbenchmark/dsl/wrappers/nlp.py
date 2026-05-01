from functools import lru_cache

import spacy
from spacy.language import Language

from .utils import op_compare, CompareOp
from ...logger import get_logger


logger = get_logger(__name__)


@lru_cache(maxsize=1)
def _get_spacy_pipeline() -> Language:
    nlp = spacy.load("en_core_web_sm")
    nlp.add_pipe("sentencizer")
    return nlp


def _get_sentence_count(text: str) -> int:
    nlp = _get_spacy_pipeline()
    doc = nlp(text)
    return len(list(doc.sents))


def _get_word_count(text: str) -> int:
    nlp = _get_spacy_pipeline()
    doc = nlp(text)
    return len([
        token
        for token in doc
        if (not token.is_punct) and (not token.is_space)
    ])


def compare_sentence_count_to_value(
    text: str,
    op: CompareOp,
    value: int
) -> tuple[bool, int]:
    count = _get_sentence_count(text)
    logger.debug(
        f"SpaCy compare_sentence_count_to_value({op} {value}): "
        f"{count=} for {text=}"
    )
    return (op_compare(count, op, value), count)


def compare_word_count_to_value(
    text: str,
    op: CompareOp,
    value: int
) -> tuple[bool, int]:
    count = _get_word_count(text)
    logger.debug(
        f"SpaCy compare_word_count_to_value({op} {value}): "
        f"{count=} for {text=}"
    )
    return (op_compare(count, op, value), count)
