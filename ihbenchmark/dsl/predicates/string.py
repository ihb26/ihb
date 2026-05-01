import re
import unicodedata
from re import Pattern
from typing import Final

from .predicate_types import Context, Predicate, PredicateResult


def _normalize(x: str) -> str:
    x = x.lower()
    x = unicodedata.normalize("NFKD", x)
    x = x.encode("ascii", "ignore").decode("ascii")
    x = re.sub(r"[^a-z0-9]", "", x)
    return x


def contains(substr: str) -> Predicate:
    """Returns true if `substr` is in the LLM output (case insensitive)"""
    return lambda ctx: PredicateResult(
        ok=(substr.lower() in ctx.content.lower()),
        name="contains"
    )


def contains_cased(substr: str) -> Predicate:
    """Returns true if `substr` is in the LLM output (case sensitive)"""
    return lambda ctx: PredicateResult(
        ok=(substr in ctx.content),
        name="contains_cased"
    )


def contains_norm(substr: str) -> Predicate:
    """
    Returns true if the normalized `substr` is in the normalized LLM output.
    Normalization makes the string lowercase, normalizes accented characters, and removes non-alphanumeric characters.
    """
    return lambda ctx: PredicateResult(
        ok=(_normalize(substr) in _normalize(ctx.content)),
        name="contains_norm"
    )


def starts_with(substr: str) -> Predicate:
    """Returns true if the LLM output starts with `substr` (case insensitive)"""
    return lambda ctx: PredicateResult(
        ok=(ctx.content.lower().startswith(substr.lower())),
        name="starts_with"
    )


def starts_with_cased(substr: str) -> Predicate:
    """Returns true if the LLM output starts with `substr` (case sensitive)"""
    return lambda ctx: PredicateResult(
        ok=(ctx.content.startswith(substr)),
        name="starts_with_cased"
    )


def starts_with_norm(substr: str) -> Predicate:
    """Returns true if the normalized LLM output starts with the normalized `substr`"""
    return lambda ctx: PredicateResult(
        ok=(_normalize(ctx.content).startswith(_normalize(substr))),
        name="starts_with_norm"
    )


def ends_with(substr: str) -> Predicate:
    """Returns true if the LLM output ends with `substr` (case insensitive)"""
    return lambda ctx: PredicateResult(
        ok=(ctx.content.lower().endswith(substr.lower())),
        name="ends_with"
    )


def ends_with_cased(substr: str) -> Predicate:
    """Returns true if the LLM output ends with `substr` (case sensitive)"""
    return lambda ctx: PredicateResult(
        ok=(ctx.content.endswith(substr)),
        name="ends_with_cased"
    )


def ends_with_norm(substr: str) -> Predicate:
    """Returns true if the normalized LLM output ends with the normalized `substr`"""
    return lambda ctx: PredicateResult(
        ok=(_normalize(ctx.content).endswith(_normalize(substr))),
        name="ends_with_norm"
    )


def has_digits() -> Predicate:
    """Returns true if the LLM output contains any digits"""
    return lambda ctx: PredicateResult(
        ok=(any(c.isdigit() for c in ctx.content)),
        name="has_digits"
    )


PATTERNS_LIST: Final[list[Pattern]] = [
    re.compile(r"^\s*[\*]\s+"),             # *
    re.compile(r"^\s*[\-]\s+"),             # -
    re.compile(r"^\s*[\+]\s+"),             # +
    re.compile(r"^\s*[•]\s+"),              # •
    re.compile(r"^\s*\d+\.\s+"),            # 1.
    re.compile(r"^\s*\d+\)\s+"),            # 1)
    re.compile(r"^\s*\(\d+\)\s+"),          # (1)
    re.compile(r"^\s*\[\d+\]\s+"),          # [1]
    re.compile(r"^\s*[a-zA-Z]+\.\s+"),      # a.
    re.compile(r"^\s*[a-zA-Z]+\)\s+"),      # a)
    re.compile(r"^\s*\([a-zA-Z]+\)\s+"),    # (a)
    re.compile(r"^\s*\[[a-zA-Z]+\]\s+"),    # [a]
]
def has_list() -> Predicate:
    """Returns true if the LLM output contains two or more consecutive lines from a bulletpoint or numbered list"""
    def _inner(ctx: Context) -> PredicateResult:
        # Checks if any two consecutive lines match the same list item pattern
        lines = ctx.content.splitlines()
        for pattern in PATTERNS_LIST:
            is_item = [
                (re.match(pattern, line) is not None)
                for line in lines
            ]
            for i in range(0, len(lines) - 1):
                if is_item[i] and is_item[i + 1]:
                    return PredicateResult(
                        ok=True,
                        name="has_list",
                        metadata={
                            "pattern": pattern,
                            "lines": is_item[i:(i + 2)],
                        }
                    )
        return PredicateResult(
            ok=False,
            name="has_list"
        )
    return _inner


def has_list_strict() -> Predicate:
    """Returns true if the LLM output only contains lines from a bulletpoint and/or numbered list"""
    def _inner(ctx: Context) -> PredicateResult:
        # Checks if all lines match some list item pattern
        lines = [
            line.strip()
            for line in ctx.content.splitlines()
            if len(line.strip())
        ]
        for line in lines:
            matches_any = any(
                (re.match(pattern, line) is not None)
                for pattern in PATTERNS_LIST
            )
            if not matches_any:
                return PredicateResult(
                    ok=False,
                    name="has_list_strict",
                    metadata={
                        "line": line,
                    }
                )
        return PredicateResult(
            ok=True,
            name="has_list_strict"
        )
    return _inner


def matches(pattern: str) -> Predicate:
    """Returns true if the regular expression `pattern` appears in the LLM output"""
    return lambda ctx: PredicateResult(
        ok=(re.search(pattern, ctx.content) is not None),
        name="matches"
    )
