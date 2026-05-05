"""Replicate all numeric LaTeX result tables from the paper.

This file was generated entirely by Claude (Anthropic) from a human-authored
exploratory analysis. The numerical results, table designs, model groupings,
constraint-family classifications, sort orders, and tie-breaking conventions
all originate from human-written code that was used to produce the figures
and tables in the paper; this script is a clean, deterministic, single-entry-
point reimplementation of that pipeline against the post-processed parquet
in `materials/results_postproc/results_paper.parquet`.

Reads only `materials/results_postproc/results_paper.parquet` and emits the
contents of every numeric \\begin{tabular}...\\end{tabular} block from the
paper (excluding the variance analysis table from the appendix and the purely
descriptive tables of constraint families, prompt phrasings, delivery
variants, model identifiers, and tool lists).

Run from the repository root:

    python scripts/replicate_paper_tables.py
"""
from __future__ import annotations

from pathlib import Path
from typing import Final

import pandas as pd


PATH_DATA: Final[Path] = (
    Path(__file__).resolve().parent.parent
    / "materials" / "results_postproc" / "results_paper.parquet"
)


# ---------------------------------------------------------------------------
# Model display name mappings (full appendix names)
# ---------------------------------------------------------------------------

MODEL_DISPLAY: Final[dict[str, str]] = {
    "anthropic/claude-opus-4-7":              "Claude Opus 4.7",
    "anthropic/claude-opus-4-6":              "Claude Opus 4.6",
    "anthropic/claude-opus-4-5":              "Claude Opus 4.5",
    "anthropic/claude-sonnet-4-6":            "Claude Sonnet 4.6",
    "anthropic/claude-sonnet-4-5":            "Claude Sonnet 4.5",
    "anthropic/claude-sonnet-4":              "Claude Sonnet 4",
    "anthropic/claude-haiku-4-5":             "Claude Haiku 4.5",
    "openai/gpt-5.4 (medium)":                "GPT 5.4 (med)",
    "openai/gpt-5.4 (low)":                   "GPT 5.4 (low)",
    "openai/gpt-5.4 (none)":                  "GPT 5.4 (none)",
    "openai/gpt-5.2 (medium)":                "GPT 5.2 (med)",
    "openai/gpt-5.2 (low)":                   "GPT 5.2 (low)",
    "openai/gpt-5-mini (medium)":             "GPT 5 Mini (med)",
    "openai/gpt-5-mini (low)":                "GPT 5 Mini (low)",
    "openai/gpt-5-nano (medium)":             "GPT 5 Nano (med)",
    "openai/gpt-5-nano (low)":                "GPT 5 Nano (low)",
    "openai/gpt-4o":                          "GPT 4o",
    "xai/grok-4-1-fast-reasoning":            "Grok 4.1 Fast (R)",
    "xai/grok-4-1-fast-non-reasoning":        "Grok 4.1 Fast",
    "xai/grok-4.20-0309-reasoning":           "Grok 4.20 (R)",
    "xai/grok-4.20-0309-non-reasoning":       "Grok 4.20",
    "zai-org/glm-5":                          "GLM 5",
    "zai-org/glm-5.1":                        "GLM 5.1",
    "moonshotai/kimi-k2.5":                   "Kimi K2.5",
    "google/gemma-4-31b-it":                  "Gemma 4 31B",
    "google/gemma-4-31b-it (reasoning)":      "Gemma 4 31B (R)",
    "google/gemma-4-26b-a4b":                 "Gemma 4 26B-A4B",
    "google/gemma-4-26b-a4b (reasoning)":     "Gemma 4 26B-A4B (R)",
    "meta/llama3.3-70b-it":                   "Llama 3.3 70B",
    "meta/llama4-maverick-17b-it":            "Llama 4 Maverick 17B",
    "meta/llama4-scout-17b-it":               "Llama 4 Scout 17B",
    "amazon/nova-2-lite":                     "Nova 2 Lite",
    "minimaxai/minimax-m2.5":                 "MiniMax M2.5",
    "minimaxai/minimax-m2.7":                 "MiniMax M2.7",
    "deepseek-ai/deepseek-v3.1":              "DeepSeek V3.1",
    "qwen/qwen3-235b-a22b-instruct-2507-tput": "Qwen 3 235B-A22B",
    "qwen/qwen3.5-397b-a17b":                 "Qwen 3.5 397B-A17B",
}

# 13-model subset used by the main-paper "selected" tables. The display name
# in the main paper drops the OpenAI "(med)" suffix from the medium-effort
# variants (the sole GPT-5 variants in the subset).
SUBSET_MODELS_RAW: Final[list[str]] = [
    "anthropic/claude-opus-4-6",
    "openai/gpt-5.4 (medium)",
    "openai/gpt-5.2 (medium)",
    "anthropic/claude-sonnet-4-5",
    "zai-org/glm-5",
    "moonshotai/kimi-k2.5",
    "google/gemma-4-31b-it (reasoning)",
    "xai/grok-4.20-0309-reasoning",
    "meta/llama4-scout-17b-it",
    "minimaxai/minimax-m2.7",
    "deepseek-ai/deepseek-v3.1",
    "amazon/nova-2-lite",
    "qwen/qwen3-235b-a22b-instruct-2507-tput",
]
SUBSET_MODELS: Final[list[str]] = [MODEL_DISPLAY[m] for m in SUBSET_MODELS_RAW]


def display_name(model_clean: str, *, subset: bool = False) -> str:
    """Format a display name for output. `model_clean` is already the appendix
    display name; in the main-paper "selected subset" tables the OpenAI
    `(med)` suffix is stripped (the sole GPT-5 variants in the subset)."""
    name = model_clean
    if subset:
        name = name.replace(" (med)", "")
    return name


def attach_display(df: pd.DataFrame) -> pd.DataFrame:
    """Add a `model_clean` column with the appendix display name. The notebook
    that produced the paper tables grouped by this column, so matching the
    upstream tie-break behaviour requires us to do the same."""
    if "model_clean" in df.columns:
        return df
    out = df.copy()
    out["model_clean"] = out["model"].map(MODEL_DISPLAY)
    return out


# ---------------------------------------------------------------------------
# Constraint family group definitions
# ---------------------------------------------------------------------------

SU_GROUPS: Final[dict[str, list[str]]] = {
    "Output": [
        "forbid-word", "forbid-char", "forbid-phrase", "forbid-digit",
        "forbid-lang", "allow-lang", "forbid-format", "allow-format",
        "allow-disclaimer",
    ],
    "Topic": [
        "forbid-topic", "allow-topic", "forbid-competitors",
        "forbid-disparagement", "forbid-data",
    ],
    "Tool": [
        "forbid-tools-all", "forbid-tools-one", "forbid-tools-except",
        "forbid-tool-param", "forbid-tool-output",
    ],
}

UT_GROUPS: Final[dict[str, list[str]]] = {
    "Format": [
        "format-language", "format-topic", "format-emoji", "format-disclaimer",
        "format-refusal", "format-failed", "format-emergency",
    ],
    "Content": [
        "content-lie", "content-omit", "content-invent", "only-mention",
        "flawed",
    ],
    "Tool": [
        "tool-cause", "tool-block", "tool-change", "search", "escalate",
        "flagged",
    ],
    "High-severity": [
        "exec", "read", "web", "memory", "purchase", "close", "exfil",
    ],
}


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def fmt_pct(x: float, *, na: str = r"--") -> str:
    """Format a fraction in [0, 1] as \\score{XX.X}, with banker's rounding.
    `na` controls the rendering of NaN/empty cells (e.g., the SU * P_2 * L_3
    cell that does not exist by construction)."""
    if pd.isna(x):
        return na
    val = round(float(x) * 100, 1)
    return r"\score{" + f"{val:.1f}" + "}"


def mean_pct(s: pd.Series) -> float:
    return float(s.mean())


def sort_rounded_desc(s: pd.DataFrame, score_col: str) -> pd.DataFrame:
    """Sort `s` by `score_col` descending, where the sort key is the score
    rounded to one decimal place (after multiplying by 100). The notebook
    rounds before sorting, so we must too: otherwise two models that round
    to the same displayed value but differ in the third decimal place will
    sort by raw value rather than tying as the paper expects."""
    if "model_clean" in s.columns:
        s = s.sort_values("model_clean", kind="stable").reset_index(drop=True)
    key = (s[score_col].astype(float) * 100).round(1)
    return s.assign(_sortkey=key).sort_values("_sortkey", ascending=False).drop(columns=["_sortkey"]).reset_index(drop=True)


def top_bot_4(scores: pd.DataFrame, *, score_col: str = "score") -> pd.DataFrame:
    """Pick top-2 and bottom-2 by score and return them in a dataframe sorted
    by score descending."""
    s = sort_rounded_desc(scores, score_col)
    sel = pd.concat([s.head(2), s.tail(2)]).drop_duplicates(subset=["model_clean"]).reset_index(drop=True)
    return sel


# ---------------------------------------------------------------------------
# Section: Main paper Table 1 (selected subset, conflict only)
# ---------------------------------------------------------------------------

SU_DOMAINS_5COL: Final[list[tuple[str, str]]] = [
    ("General", "generic"),
    ("Health", "health"),
    ("Retail", "retail"),
    ("Finance", "finance"),
]
UT_DOMAINS_5COL: Final[list[tuple[str, str]]] = [
    ("General", "generic"),
    ("Health", "health"),
    ("Retail", "retail"),
    ("Coding", "coding"),
]


def _row_5x5(df: pd.DataFrame, label: str) -> str:
    """Build a single LaTeX row of the 5x5 (Average + 4 domains, both tracks)
    table layout used by the main results tables."""
    overall = mean_pct(df["compliant"])

    su = df[df["set"] == "System-User"]
    ut = df[df["set"] == "User-Tool"]
    su_avg = mean_pct(su["compliant"])
    ut_avg = mean_pct(ut["compliant"])

    cells = [label, fmt_pct(overall), fmt_pct(su_avg)]
    for _, dom in SU_DOMAINS_5COL:
        cells.append(fmt_pct(mean_pct(su[su["domain"] == dom]["compliant"])))
    cells.append(fmt_pct(ut_avg))
    for _, dom in UT_DOMAINS_5COL:
        cells.append(fmt_pct(mean_pct(ut[ut["domain"] == dom]["compliant"])))
    return " & ".join(cells) + r" \\"


def _model_overall_order(df: pd.DataFrame) -> list[str]:
    """Return models (by `model_clean`) sorted by their overall compliance
    descending. Mirrors the upstream notebook: alphabetical groupby on
    `model_clean`, mean *rounded to 1 decimal place* (in percent), then sort
    descending. Rounding before the sort is essential because two models can
    have raw means that differ in the third decimal place yet share the same
    displayed value -- the paper consistently breaks such ties on rounded
    values, not raw ones."""
    overall = (
        df.groupby("model_clean", sort=True)["compliant"].mean()
        .mul(100).round(1)
        .reset_index()
    )
    overall = overall.sort_values("compliant", ascending=False).reset_index(drop=True)
    return overall["model_clean"].tolist()


HEADER_5x5: Final[str] = r"""\toprule
& & \multicolumn{5}{c}{\SU Compliance (\%)} 
  & \multicolumn{5}{c}{\UT Compliance (\%)} \\
\cmidrule(lr){3-7} \cmidrule(lr){8-11}
\textbf{Model} 
& \textbf{Overall}
& \textbf{Average}
& \textbf{General} 
& \textbf{Health} 
& \textbf{Retail} 
& \textbf{Finance}
& \textbf{Average}
& \textbf{General} 
& \textbf{Health} 
& \textbf{Retail} 
& \textbf{Coding} \\
\midrule"""


def _print_5x5_table(df_full: pd.DataFrame, df_filt: pd.DataFrame, *, models: list[str], subset_names: bool, average_label: str) -> str:
    """Build a full 5x5 main-results style table over the given model list,
    sorted by Overall descending, plus an Average row over all 37 models."""
    out: list[str] = []
    out.append(r"\begin{tabular}{l r @{\hspace{3pt}\vrule width 0.3pt\hspace{3pt}} rrrrr @{\hspace{3pt}\vrule width 0.3pt\hspace{3pt}} rrrrr}")
    out.append(HEADER_5x5)

    df_sub = df_filt[df_filt["model_clean"].isin(models)]
    sorted_models = _model_overall_order(df_sub)

    for m in sorted_models:
        out.append(_row_5x5(df_filt[df_filt["model_clean"] == m], display_name(m, subset=subset_names)))

    out.append(r"\midrule")
    out.append(_row_5x5(df_full, average_label))
    out.append(r"\bottomrule")
    out.append(r"\end{tabular}")
    return "\n".join(out)


# ---------------------------------------------------------------------------
# Section: Strictness tables
# ---------------------------------------------------------------------------

SU_STRICTNESS: Final[list[str]] = [
    "L_1 (simple)", "L_2 (hardened)", "L_3 (refusal)",
]
UT_STRICTNESS: Final[list[str]] = [
    "L_1 (none)", "L_2 (simple)", "L_3 (hardened)",
]


def _strictness_per_model(df: pd.DataFrame, set_: str, generic: bool) -> pd.DataFrame:
    """Per-model L_1/L_2/L_3 means within (set, generic) bucket."""
    sub = df[(df["set"] == set_) & (df["domain"].eq("generic") == generic)]
    levels = SU_STRICTNESS if set_ == "System-User" else UT_STRICTNESS
    rows = []
    for m, g in sub.groupby("model_clean", sort=True):
        row: dict[str, float | str] = {"model_clean": m}
        for lvl in levels:
            row[lvl] = mean_pct(g[g["constraint_strictness"] == lvl]["compliant"])
        rows.append(row)
    return pd.DataFrame(rows)


def _strictness_avg(df: pd.DataFrame, set_: str, generic: bool) -> dict[str, float]:
    sub = df[(df["set"] == set_) & (df["domain"].eq("generic") == generic)]
    levels = SU_STRICTNESS if set_ == "System-User" else UT_STRICTNESS
    return {lvl: mean_pct(sub[sub["constraint_strictness"] == lvl]["compliant"]) for lvl in levels}


def _strictness_block(
    df_full: pd.DataFrame,
    df_filt: pd.DataFrame,
    *,
    models: list[str],
    subset_names: bool,
) -> str:
    """Build the SELECTED main-paper strictness table (Table 2)."""

    out: list[str] = []
    out.append(r"\begin{tabular}{l @{\hspace{3pt}\vrule width 0.3pt\hspace{3pt}} r @{\hspace{3pt}\vrule width 0.3pt\hspace{3pt}} rrr @{\hspace{3pt}\vrule width 0.3pt\hspace{3pt}} r @{\hspace{3pt}\vrule width 0.3pt\hspace{3pt}} rrr}")
    out.append(r"\toprule")
    out.append(r"& \multicolumn{4}{c}{\SU Compliance (\%)} ")
    out.append(r"  & \multicolumn{4}{c}{\UT Compliance (\%)} \\")
    out.append(r"\cmidrule(lr){2-5} \cmidrule(lr){6-9}")
    out.append(r"\textbf{Group}")
    out.append(r"& \textbf{Model} ")
    out.append(r"& \textbf{$L_1$} ")
    out.append(r"& \textbf{$L_2$} ")
    out.append(r"& \textbf{$L_3$} ")
    out.append(r"& \textbf{Model} ")
    out.append(r"& \textbf{$L_1$} ")
    out.append(r"& \textbf{$L_2$} ")
    out.append(r"& \textbf{$L_3$} \\")
    out.append(r"\midrule")

    for i, generic in enumerate([True, False]):
        group_label = "Generic" if generic else r"\shortstack{Domain/\\Agentic}"
        out.append(r"\multirow{5}{*}{" + group_label + "}")

        df_sub = df_filt[df_filt["model_clean"].isin(models)]
        su_scores = _strictness_per_model(df_sub, "System-User", generic)
        ut_scores = _strictness_per_model(df_sub, "User-Tool", generic)
        su_sel = top_bot_4(su_scores.assign(score=su_scores["L_1 (simple)"]))
        ut_sel = top_bot_4(ut_scores.assign(score=ut_scores["L_1 (none)"]))

        for j in range(4):
            su_row = su_sel.iloc[j]
            ut_row = ut_sel.iloc[j]
            cells = [
                "& " + display_name(su_row["model_clean"], subset=subset_names),
                fmt_pct(su_row["L_1 (simple)"]),
                fmt_pct(su_row["L_2 (hardened)"]),
                fmt_pct(su_row["L_3 (refusal)"]),
                display_name(ut_row["model_clean"], subset=subset_names),
                fmt_pct(ut_row["L_1 (none)"]),
                fmt_pct(ut_row["L_2 (simple)"]),
                fmt_pct(ut_row["L_3 (hardened)"]),
            ]
            out.append(" & ".join(cells) + r" \\")

        out.append(r"\cmidrule(lr){2-9}")
        su_avg = _strictness_avg(df_full, "System-User", generic)
        ut_avg = _strictness_avg(df_full, "User-Tool", generic)
        cells = [
            "& Average",
            fmt_pct(su_avg["L_1 (simple)"]),
            fmt_pct(su_avg["L_2 (hardened)"]),
            fmt_pct(su_avg["L_3 (refusal)"]),
            "Average",
            fmt_pct(ut_avg["L_1 (none)"]),
            fmt_pct(ut_avg["L_2 (simple)"]),
            fmt_pct(ut_avg["L_3 (hardened)"]),
        ]
        out.append(" & ".join(cells) + r" \\")
        if i == 0:
            out.append(r"\midrule")

    out.append(r"\bottomrule")
    out.append(r"\end{tabular}")
    return "\n".join(out)


def _strictness_full_block(df_full: pd.DataFrame, df_filt: pd.DataFrame, *, generic: bool, with_bottomrule: bool = True) -> str:
    """Build the FULL appendix strictness table (Tables 1146/1215).

    `with_bottomrule` lets callers reproduce the paper's missing-rule typo
    in the domain-specific variant (Table 1215 has no \\bottomrule before
    \\end{tabular})."""

    out: list[str] = []
    out.append(r"\begin{tabular}{l @{\hspace{3pt}\vrule width 0.3pt\hspace{3pt}} r @{\hspace{3pt}\vrule width 0.3pt\hspace{3pt}} rrr @{\hspace{3pt}\vrule width 0.3pt\hspace{3pt}} r @{\hspace{3pt}\vrule width 0.3pt\hspace{3pt}} rrr}")
    out.append(r"\toprule")
    out.append(r"& \multicolumn{4}{c}{\SU Compliance (\%)} ")
    out.append(r"  & \multicolumn{4}{c}{\UT Compliance (\%)} \\")
    out.append(r"\cmidrule(lr){2-5} \cmidrule(lr){6-9}")
    out.append(r"\textbf{Group}")
    out.append(r"& \textbf{Model} ")
    out.append(r"& \textbf{$L_1$} ")
    out.append(r"& \textbf{$L_2$} ")
    out.append(r"& \textbf{$L_3$} ")
    out.append(r"& \textbf{Model} ")
    out.append(r"& \textbf{$L_1$} ")
    out.append(r"& \textbf{$L_2$} ")
    out.append(r"& \textbf{$L_3$} \\")
    out.append(r"\midrule")

    group_label = "Generic" if generic else r"\shortstack{Domain/\\Agentic}"
    out.append(r"\multirow{5}{*}{" + group_label + "}")

    su_scores = _strictness_per_model(df_filt, "System-User", generic)
    ut_scores = _strictness_per_model(df_filt, "User-Tool", generic)

    su_sorted = sort_rounded_desc(su_scores, "L_1 (simple)")
    ut_sorted = sort_rounded_desc(ut_scores, "L_1 (none)")

    for j in range(len(su_sorted)):
        su_row = su_sorted.iloc[j]
        ut_row = ut_sorted.iloc[j]
        cells = [
            "& " + display_name(su_row["model_clean"]),
            fmt_pct(su_row["L_1 (simple)"]),
            fmt_pct(su_row["L_2 (hardened)"]),
            fmt_pct(su_row["L_3 (refusal)"]),
            display_name(ut_row["model_clean"]),
            fmt_pct(ut_row["L_1 (none)"]),
            fmt_pct(ut_row["L_2 (simple)"]),
            fmt_pct(ut_row["L_3 (hardened)"]),
        ]
        out.append(" & ".join(cells) + r" \\")

    out.append(r"\cmidrule(lr){2-9}")
    su_avg = _strictness_avg(df_full, "System-User", generic)
    ut_avg = _strictness_avg(df_full, "User-Tool", generic)
    cells = [
        "& Average",
        fmt_pct(su_avg["L_1 (simple)"]),
        fmt_pct(su_avg["L_2 (hardened)"]),
        fmt_pct(su_avg["L_3 (refusal)"]),
        "Average",
        fmt_pct(ut_avg["L_1 (none)"]),
        fmt_pct(ut_avg["L_2 (simple)"]),
        fmt_pct(ut_avg["L_3 (hardened)"]),
    ]
    out.append(" & ".join(cells) + r" \\")
    if with_bottomrule:
        out.append(r"\bottomrule")
    out.append(r"\end{tabular}")
    return "\n".join(out)


# ---------------------------------------------------------------------------
# Section: Phrasing x strictness breakdown tables
# ---------------------------------------------------------------------------

# Track-specific (phrasing, strictness) cell schema. Listed in the column
# order used by the appendix table. The SU * P_2 * L_3 cell does not exist by
# construction (the L_3 "refusal" formulation is only paired with explicit
# user prompts on the SU track), and is rendered as an em-dash.
PXS_COLS_SU: Final[list[tuple[str, str]]] = [
    ("P_1 (explicit)", "L_1 (simple)"),
    ("P_1 (explicit)", "L_2 (hardened)"),
    ("P_1 (explicit)", "L_3 (refusal)"),
    ("P_2 (implicit)", "L_1 (simple)"),
    ("P_2 (implicit)", "L_2 (hardened)"),
    ("P_2 (implicit)", "L_3 (refusal)"),  # empty by construction
]
PXS_COLS_UT: Final[list[tuple[str, str]]] = [
    ("P_1 (explicit)", "L_1 (none)"),
    ("P_1 (explicit)", "L_2 (simple)"),
    ("P_1 (explicit)", "L_3 (hardened)"),
    ("P_2 (implicit)", "L_1 (none)"),
    ("P_2 (implicit)", "L_2 (simple)"),
    ("P_2 (implicit)", "L_3 (hardened)"),
]


def _pxs_cell_mean(sub: pd.DataFrame, phrasing: str, strictness: str) -> float:
    s = sub[
        (sub["user_prompt_phrasing"] == phrasing)
        & (sub["constraint_strictness"] == strictness)
    ]["compliant"]
    if len(s) == 0:
        return float("nan")
    return mean_pct(s)


def _pxs_per_model(df: pd.DataFrame, generic: bool) -> pd.DataFrame:
    """Per-model (phrasing, strictness) means for both tracks within the
    selected (generic vs domain) bucket."""
    sub = df[df["domain"].eq("generic") == generic]
    rows: list[dict[str, float | str]] = []
    for m, g in sub.groupby("model_clean", sort=True):
        row: dict[str, float | str] = {"model_clean": m}
        su = g[g["set"] == "System-User"]
        ut = g[g["set"] == "User-Tool"]
        for p, lvl in PXS_COLS_SU:
            row[("SU", p, lvl)] = _pxs_cell_mean(su, p, lvl)
        for p, lvl in PXS_COLS_UT:
            row[("UT", p, lvl)] = _pxs_cell_mean(ut, p, lvl)
        row["overall"] = mean_pct(g["compliant"])
        rows.append(row)
    return pd.DataFrame(rows)


def _pxs_avg(df: pd.DataFrame, generic: bool) -> dict[tuple[str, str, str], float]:
    sub = df[df["domain"].eq("generic") == generic]
    out: dict[tuple[str, str, str], float] = {}
    su = sub[sub["set"] == "System-User"]
    ut = sub[sub["set"] == "User-Tool"]
    for p, lvl in PXS_COLS_SU:
        out[("SU", p, lvl)] = _pxs_cell_mean(su, p, lvl)
    for p, lvl in PXS_COLS_UT:
        out[("UT", p, lvl)] = _pxs_cell_mean(ut, p, lvl)
    return out


def _pxs_full_block(df_full: pd.DataFrame, df_filt: pd.DataFrame, *, generic: bool) -> str:
    """Build a phrasing-x-strictness breakdown table for the (generic or
    domain) bucket, with a row per model sorted by overall compliance within
    the bucket and a final Average row over all 37 models."""
    out: list[str] = []
    out.append(
        r"\begin{tabular}{l "
        r"@{\hspace{3pt}\vrule width 0.3pt\hspace{3pt}} rrr "
        r"@{\hspace{3pt}\vrule width 0.3pt\hspace{3pt}} rrr "
        r"@{\hspace{3pt}\vrule width 0.3pt\hspace{3pt}} rrr "
        r"@{\hspace{3pt}\vrule width 0.3pt\hspace{3pt}} rrr}"
    )
    out.append(r"\toprule")
    out.append(r"& \multicolumn{6}{c}{\SU Compliance (\%)} ")
    out.append(r"  & \multicolumn{6}{c}{\UT Compliance (\%)} \\")
    out.append(r"\cmidrule(lr){2-7} \cmidrule(lr){8-13}")
    out.append(r"& \multicolumn{3}{c}{$P_1$ (explicit)} ")
    out.append(r"& \multicolumn{3}{c}{$P_2$ (implicit)} ")
    out.append(r"& \multicolumn{3}{c}{$P_1$ (explicit)} ")
    out.append(r"& \multicolumn{3}{c}{$P_2$ (implicit)} \\")
    out.append(r"\cmidrule(lr){2-4} \cmidrule(lr){5-7} \cmidrule(lr){8-10} \cmidrule(lr){11-13}")
    out.append(r"\textbf{Model} ")
    out.append(r"& \textbf{$L_1$} & \textbf{$L_2$} & \textbf{$L_3$} ")
    out.append(r"& \textbf{$L_1$} & \textbf{$L_2$} & \textbf{$L_3$} ")
    out.append(r"& \textbf{$L_1$} & \textbf{$L_2$} & \textbf{$L_3$} ")
    out.append(r"& \textbf{$L_1$} & \textbf{$L_2$} & \textbf{$L_3$} \\")
    out.append(r"\midrule")

    scores = _pxs_per_model(df_filt, generic)
    sorted_scores = sort_rounded_desc(scores, "overall")

    for _, row in sorted_scores.iterrows():
        cells = [display_name(row["model_clean"])]
        for p, lvl in PXS_COLS_SU:
            cells.append(fmt_pct(row[("SU", p, lvl)]))
        for p, lvl in PXS_COLS_UT:
            cells.append(fmt_pct(row[("UT", p, lvl)]))
        out.append(" & ".join(cells) + r" \\")

    out.append(r"\midrule")
    avg = _pxs_avg(df_full, generic)
    cells = ["Average"]
    for p, lvl in PXS_COLS_SU:
        cells.append(fmt_pct(avg[("SU", p, lvl)]))
    for p, lvl in PXS_COLS_UT:
        cells.append(fmt_pct(avg[("UT", p, lvl)]))
    out.append(" & ".join(cells) + r" \\")
    out.append(r"\bottomrule")
    out.append(r"\end{tabular}")
    return "\n".join(out)


# ---------------------------------------------------------------------------
# Section: Constraint group tables
# ---------------------------------------------------------------------------

CG_COLS_SU: Final[list[str]] = ["Output", "Topic", "Tool"]
CG_COLS_UT: Final[list[str]] = ["Format", "Content", "Tool", "High-severity"]


def _cg_per_model(df: pd.DataFrame) -> pd.DataFrame:
    """Per-model SU/UT constraint group means."""
    rows = []
    for m, g in df.groupby("model_clean", sort=True):
        row: dict[str, float | str] = {"model_clean": m}
        for grp_label, fams in SU_GROUPS.items():
            row[("SU", grp_label)] = mean_pct(
                g[(g["set"] == "System-User") & g["constraint_family"].isin(fams)]["compliant"]
            )
        for grp_label, fams in UT_GROUPS.items():
            row[("UT", grp_label)] = mean_pct(
                g[(g["set"] == "User-Tool") & g["constraint_family"].isin(fams)]["compliant"]
            )
        rows.append(row)
    return pd.DataFrame(rows)


def _cg_avg(df: pd.DataFrame) -> dict[tuple[str, str], float]:
    out: dict[tuple[str, str], float] = {}
    for grp_label, fams in SU_GROUPS.items():
        out[("SU", grp_label)] = mean_pct(
            df[(df["set"] == "System-User") & df["constraint_family"].isin(fams)]["compliant"]
        )
    for grp_label, fams in UT_GROUPS.items():
        out[("UT", grp_label)] = mean_pct(
            df[(df["set"] == "User-Tool") & df["constraint_family"].isin(fams)]["compliant"]
        )
    return out


def _cg_overall_per_model(df: pd.DataFrame) -> pd.Series:
    return df.groupby("model_clean", sort=True)["compliant"].mean()


def _cg_block(
    df_full: pd.DataFrame,
    df_filt: pd.DataFrame,
    *,
    models: list[str],
    subset_names: bool,
    ut_format_label: str,
) -> str:
    """Build the SELECTED constraint-group table (Table 3 main).

    `ut_format_label` is the LaTeX header text for the first UT column, which
    differs between the main and appendix versions ("Format" vs
    "Format/framing").
    """
    out: list[str] = []
    out.append(r"\begin{tabular}{l @{\hspace{3pt}\vrule width 0.3pt\hspace{3pt}} rrr @{\hspace{3pt}\vrule width 0.3pt\hspace{3pt}} rrrr}")
    out.append(r"\toprule")
    out.append(r"& \multicolumn{3}{c}{\SU Compliance (\%)} ")
    out.append(r"& \multicolumn{4}{c}{\UT Compliance (\%)} \\")
    out.append(r"\cmidrule(lr){2-4} \cmidrule(lr){5-8}")
    out.append(r"\textbf{Model} ")
    out.append(r"& \textbf{Output} ")
    out.append(r"& \textbf{Topic} ")
    out.append(r"& \textbf{Tool} ")
    out.append(rf"& \textbf{{{ut_format_label}}} ")
    out.append(r"& \textbf{Content} ")
    out.append(r"& \textbf{Tool} ")
    out.append(r"& \textbf{High-severity} \\")
    out.append(r"\midrule")

    df_sub = df_filt[df_filt["model_clean"].isin(models)]
    overall = _cg_overall_per_model(df_sub)
    cg_scores = _cg_per_model(df_sub).assign(
        score=lambda x: x["model_clean"].map(overall)
    )
    sel = top_bot_4(cg_scores)

    for _, row in sel.iterrows():
        cells = [display_name(row["model_clean"], subset=subset_names)]
        for grp_label in CG_COLS_SU:
            cells.append(fmt_pct(row[("SU", grp_label)]))
        for grp_label in CG_COLS_UT:
            cells.append(fmt_pct(row[("UT", grp_label)]))
        out.append(" & ".join(cells) + r" \\")

    out.append(r"\midrule")
    avg = _cg_avg(df_full)
    cells = ["Average"]
    for grp_label in CG_COLS_SU:
        cells.append(fmt_pct(avg[("SU", grp_label)]))
    for grp_label in CG_COLS_UT:
        cells.append(fmt_pct(avg[("UT", grp_label)]))
    out.append(" & ".join(cells) + r" \\")
    out.append(r"\bottomrule")
    out.append(r"\end{tabular}")
    return "\n".join(out)


def _cg_full_block(df_full: pd.DataFrame, df_filt: pd.DataFrame) -> str:
    """Build the FULL appendix constraint-group table (Table 1518)."""
    out: list[str] = []
    out.append(r"\begin{tabular}{l @{\hspace{3pt}\vrule width 0.3pt\hspace{3pt}} rrr @{\hspace{3pt}\vrule width 0.3pt\hspace{3pt}} rrrr}")
    out.append(r"\toprule")
    out.append(r"& \multicolumn{3}{c}{\SU Compliance (\%)} ")
    out.append(r"& \multicolumn{4}{c}{\UT Compliance (\%)} \\")
    out.append(r"\cmidrule(lr){2-4} \cmidrule(lr){5-8}")
    out.append(r"\textbf{Model} ")
    out.append(r"& \textbf{Output} ")
    out.append(r"& \textbf{Topic} ")
    out.append(r"& \textbf{Tool} ")
    out.append(r"& \textbf{Format/framing} ")
    out.append(r"& \textbf{Content} ")
    out.append(r"& \textbf{Tool} ")
    out.append(r"& \textbf{High-severity} \\")
    out.append(r"\midrule")

    overall = _cg_overall_per_model(df_filt)
    cg_scores = _cg_per_model(df_filt).assign(
        score=lambda x: x["model_clean"].map(overall)
    )
    cg_sorted = sort_rounded_desc(cg_scores, "score")

    for _, row in cg_sorted.iterrows():
        cells = [display_name(row["model_clean"])]
        for grp_label in CG_COLS_SU:
            cells.append(fmt_pct(row[("SU", grp_label)]))
        for grp_label in CG_COLS_UT:
            cells.append(fmt_pct(row[("UT", grp_label)]))
        out.append(" & ".join(cells) + r" \\")

    out.append(r"\midrule")
    avg = _cg_avg(df_full)
    cells = ["Average"]
    for grp_label in CG_COLS_SU:
        cells.append(fmt_pct(avg[("SU", grp_label)]))
    for grp_label in CG_COLS_UT:
        cells.append(fmt_pct(avg[("UT", grp_label)]))
    out.append(" & ".join(cells) + r" \\")
    out.append(r"\bottomrule")
    out.append(r"\end{tabular}")
    return "\n".join(out)


# ---------------------------------------------------------------------------
# Section: Phrasing/Delivery main heatmap tables
# ---------------------------------------------------------------------------

UPP_LEVELS: Final[list[str]] = ["P_1 (explicit)", "P_2 (implicit)"]
DV_LEVELS: Final[list[str]] = [
    "D_1 (plain)", "D_2 (breakout)", "D_3 (acknowledge)", "D_4 (switch)",
]


def _phrasing_per_model(df: pd.DataFrame, generic: bool) -> pd.DataFrame:
    sub = df[(df["set"] == "System-User") & (df["domain"].eq("generic") == generic)]
    rows = []
    for m, g in sub.groupby("model_clean", sort=True):
        row: dict[str, float | str] = {"model_clean": m}
        for lvl in UPP_LEVELS:
            row[lvl] = mean_pct(g[g["user_prompt_phrasing"] == lvl]["compliant"])
        rows.append(row)
    return pd.DataFrame(rows)


def _phrasing_avg(df: pd.DataFrame, generic: bool) -> dict[str, float]:
    sub = df[(df["set"] == "System-User") & (df["domain"].eq("generic") == generic)]
    return {lvl: mean_pct(sub[sub["user_prompt_phrasing"] == lvl]["compliant"]) for lvl in UPP_LEVELS}


def _delivery_per_model(df: pd.DataFrame, generic: bool) -> pd.DataFrame:
    sub = df[(df["set"] == "User-Tool") & (df["domain"].eq("generic") == generic)]
    rows = []
    for m, g in sub.groupby("model_clean", sort=True):
        row: dict[str, float | str] = {"model_clean": m}
        for lvl in DV_LEVELS:
            row[lvl] = mean_pct(g[g["conflict_presentation"] == lvl]["compliant"])
        rows.append(row)
    return pd.DataFrame(rows)


def _delivery_avg(df: pd.DataFrame, generic: bool) -> dict[str, float]:
    sub = df[(df["set"] == "User-Tool") & (df["domain"].eq("generic") == generic)]
    return {lvl: mean_pct(sub[sub["conflict_presentation"] == lvl]["compliant"]) for lvl in DV_LEVELS}


def _phrasing_heatmap(df_full: pd.DataFrame, df_filt: pd.DataFrame, *, models: list[str], subset_names: bool) -> str:
    """Main paper Table 4 (selected subset, conflict, SU)."""
    out: list[str] = []
    out.append(r"\begin{tabular}{l @{\hspace{3pt}\vrule width 0.3pt\hspace{3pt}} r @{\hspace{3pt}\vrule width 0.3pt\hspace{3pt}} rr}")
    out.append(r"\toprule")
    out.append(r"\textbf{Group}")
    out.append(r"& \textbf{Model} ")
    out.append(r"& \textbf{$P_1$} ")
    out.append(r"& \textbf{$P_2$} \\")
    out.append(r"\midrule")

    for i, generic in enumerate([True, False]):
        group_label = "Generic" if generic else r"\shortstack{Domain/\\Agentic}"
        out.append(r"\multirow{5}{*}{" + group_label + "}")

        df_sub = df_filt[df_filt["model_clean"].isin(models)]
        scores = _phrasing_per_model(df_sub, generic)
        sel = top_bot_4(scores.assign(score=scores["P_1 (explicit)"]))

        for _, row in sel.iterrows():
            cells = [
                "& " + display_name(row["model_clean"], subset=subset_names),
                fmt_pct(row["P_1 (explicit)"]),
                fmt_pct(row["P_2 (implicit)"]),
            ]
            out.append(" & ".join(cells) + r" \\")

        out.append(r"\cmidrule(lr){2-4}")
        avg = _phrasing_avg(df_full, generic)
        cells = ["& Average", fmt_pct(avg["P_1 (explicit)"]), fmt_pct(avg["P_2 (implicit)"])]
        out.append(" & ".join(cells) + r" \\")
        if i == 0:
            out.append(r"\midrule")

    out.append(r"\bottomrule")
    out.append(r"\end{tabular}")
    return "\n".join(out)


def _delivery_heatmap(df_full: pd.DataFrame, df_filt: pd.DataFrame, *, models: list[str], subset_names: bool) -> str:
    """Main paper Table 5 (selected subset, conflict, UT)."""
    out: list[str] = []
    out.append(r"\begin{tabular}{l @{\hspace{3pt}\vrule width 0.3pt\hspace{3pt}} r @{\hspace{3pt}\vrule width 0.3pt\hspace{3pt}} rrrr}")
    out.append(r"\toprule")
    out.append(r"\textbf{Group}")
    out.append(r"& \textbf{Model} ")
    out.append(r"& \textbf{$D_1$} ")
    out.append(r"& \textbf{$D_2$} ")
    out.append(r"& \textbf{$D_3$} ")
    out.append(r"& \textbf{$D_4$} \\")
    out.append(r"\midrule")

    for i, generic in enumerate([True, False]):
        group_label = "Generic" if generic else r"\shortstack{Domain/\\Agentic}"
        out.append(r"\multirow{5}{*}{" + group_label + "}")

        df_sub = df_filt[df_filt["model_clean"].isin(models)]
        scores = _delivery_per_model(df_sub, generic)
        sel = top_bot_4(scores.assign(score=scores["D_1 (plain)"]))

        for _, row in sel.iterrows():
            cells = ["& " + display_name(row["model_clean"], subset=subset_names)]
            for lvl in DV_LEVELS:
                cells.append(fmt_pct(row[lvl]))
            out.append(" & ".join(cells) + r" \\")

        out.append(r"\cmidrule(lr){2-6}")
        avg = _delivery_avg(df_full, generic)
        cells = ["& Average"] + [fmt_pct(avg[lvl]) for lvl in DV_LEVELS]
        out.append(" & ".join(cells) + r" \\")
        if i == 0:
            out.append(r"\midrule")

    out.append(r"\bottomrule")
    out.append(r"\end{tabular}")
    return "\n".join(out)


# ---------------------------------------------------------------------------
# Section: Phrasing/Delivery FULL appendix tables
# ---------------------------------------------------------------------------

def _phrasing_full(df_full: pd.DataFrame, df_filt: pd.DataFrame) -> str:
    out: list[str] = []
    out.append(r"\begin{tabular}{")
    out.append(r"l r r r")
    out.append(r"@{\hspace{8pt}\vrule width 0.3pt\hspace{8pt}}")
    out.append(r"l r r r")
    out.append(r"}")
    out.append(r"\toprule")
    out.append(r"\multicolumn{4}{c}{\textbf{Generic scenarios}}")
    out.append(r"&")
    out.append(r"\multicolumn{4}{c}{\textbf{Domain-specific/agentic scenarios}} \\")
    out.append(r"\cmidrule(lr){1-4} \cmidrule(lr){5-8}")
    out.append(r"\textbf{Group}")
    out.append(r"& \textbf{Model}")
    out.append(r"& \textbf{$P_1$}")
    out.append(r"& \textbf{$P_2$}")
    out.append(r"& \textbf{Group}")
    out.append(r"& \textbf{Model}")
    out.append(r"& \textbf{$P_1$}")
    out.append(r"& \textbf{$P_2$} \\")
    out.append(r"\midrule")

    gen_scores = sort_rounded_desc(_phrasing_per_model(df_filt, True), "P_1 (explicit)")
    dom_scores = sort_rounded_desc(_phrasing_per_model(df_filt, False), "P_1 (explicit)")

    n = len(gen_scores)
    for j in range(n):
        gen_row = gen_scores.iloc[j]
        dom_row = dom_scores.iloc[j]
        if j == 0:
            left_prefix = r"\multirow{37}{*}{Generic}"
            right_prefix = r"\multirow{37}{*}{\shortstack{Domain/\\Agentic}}"
        else:
            left_prefix = ""
            right_prefix = ""

        left_cells = [
            left_prefix,
            display_name(gen_row["model_clean"]),
            fmt_pct(gen_row["P_1 (explicit)"]),
            fmt_pct(gen_row["P_2 (implicit)"]),
        ]
        right_cells = [
            right_prefix,
            display_name(dom_row["model_clean"]),
            fmt_pct(dom_row["P_1 (explicit)"]),
            fmt_pct(dom_row["P_2 (implicit)"]),
        ]
        out.append(" & ".join(left_cells) + " & " + " & ".join(right_cells) + r" \\")

    out.append(r"\cmidrule(lr){2-4} \cmidrule(lr){6-8}")
    avg_g = _phrasing_avg(df_full, True)
    avg_d = _phrasing_avg(df_full, False)
    cells = [
        "& Average", fmt_pct(avg_g["P_1 (explicit)"]), fmt_pct(avg_g["P_2 (implicit)"]),
        "& Average", fmt_pct(avg_d["P_1 (explicit)"]), fmt_pct(avg_d["P_2 (implicit)"]),
    ]
    out.append(" & ".join(cells) + r" \\")
    out.append(r"\bottomrule")
    out.append(r"\end{tabular}")
    return "\n".join(out)


def _delivery_full(df_full: pd.DataFrame, df_filt: pd.DataFrame) -> str:
    out: list[str] = []
    out.append(r"\begin{tabular}{")
    out.append(r"l r r r r r")
    out.append(r"@{\hspace{8pt}\vrule width 0.3pt\hspace{8pt}}")
    out.append(r"l r r r r r")
    out.append(r"}")
    out.append(r"\toprule")
    out.append(r"\multicolumn{6}{c}{\textbf{Generic scenarios}}")
    out.append(r"&")
    out.append(r"\multicolumn{6}{c}{\textbf{Domain-specific/agentic scenarios}} \\")
    out.append(r"\cmidrule(lr){1-6} \cmidrule(lr){7-12}")
    out.append(r"\textbf{Group}")
    out.append(r"& \textbf{Model}")
    out.append(r"& \textbf{$D_1$}")
    out.append(r"& \textbf{$D_2$}")
    out.append(r"& \textbf{$D_3$}")
    out.append(r"& \textbf{$D_4$}")
    out.append(r"& \textbf{Group}")
    out.append(r"& \textbf{Model}")
    out.append(r"& \textbf{$D_1$}")
    out.append(r"& \textbf{$D_2$}")
    out.append(r"& \textbf{$D_3$}")
    out.append(r"& \textbf{$D_4$} \\")
    out.append(r"\midrule")

    gen_scores = sort_rounded_desc(_delivery_per_model(df_filt, True), "D_1 (plain)")
    dom_scores = sort_rounded_desc(_delivery_per_model(df_filt, False), "D_1 (plain)")

    n = len(gen_scores)
    for j in range(n):
        gen_row = gen_scores.iloc[j]
        dom_row = dom_scores.iloc[j]
        left_prefix = r"\multirow{37}{*}{Generic}" if j == 0 else ""
        right_prefix = r"\multirow{37}{*}{\shortstack{Domain/\\Agentic}}" if j == 0 else ""

        left_cells = [left_prefix, display_name(gen_row["model_clean"])] + [fmt_pct(gen_row[lvl]) for lvl in DV_LEVELS]
        right_cells = [right_prefix, display_name(dom_row["model_clean"])] + [fmt_pct(dom_row[lvl]) for lvl in DV_LEVELS]
        out.append(" & ".join(left_cells) + " & " + " & ".join(right_cells) + r" \\")

    out.append(r"\cmidrule(lr){2-6} \cmidrule(lr){8-12}")
    avg_g = _delivery_avg(df_full, True)
    avg_d = _delivery_avg(df_full, False)
    cells = ["& Average"] + [fmt_pct(avg_g[lvl]) for lvl in DV_LEVELS]
    cells += ["& Average"] + [fmt_pct(avg_d[lvl]) for lvl in DV_LEVELS]
    out.append(" & ".join(cells) + r" \\")
    out.append(r"\bottomrule")
    out.append(r"\end{tabular}")
    return "\n".join(out)


# ---------------------------------------------------------------------------
# Top-level driver
# ---------------------------------------------------------------------------

def main() -> None:
    df = pd.read_parquet(PATH_DATA)
    df = attach_display(df)

    df_conflict = df[df["scenario_type"] == "conflict"]
    df_non_conflict = df[df["scenario_type"] == "non-conflict"]

    blocks: list[tuple[str, str]] = []

    # --- Main paper, Section 4 -------------------------------------------------

    # Table 1 (tab:main-results-conflict-selected): selected subset, conflict
    blocks.append((
        "Table 1 (tab:main-results-conflict-selected)",
        _print_5x5_table(
            df_full=df_conflict,
            df_filt=df_conflict,
            models=SUBSET_MODELS,
            subset_names=True,
            average_label="Average (37 models)",
        ),
    ))

    # Table 2 (tab:constraint-strictness): selected subset
    blocks.append((
        "Table 2 (tab:constraint-strictness)",
        _strictness_block(df_conflict, df_conflict, models=SUBSET_MODELS, subset_names=True),
    ))

    # Table 3 (tab:constraint-groups): selected subset
    blocks.append((
        "Table 3 (tab:constraint-groups)",
        _cg_block(df_conflict, df_conflict, models=SUBSET_MODELS, subset_names=True, ut_format_label="Format"),
    ))

    # Table 4 (tab:phrasing-heatmap): selected subset SU
    blocks.append((
        "Table 4 (tab:phrasing-heatmap)",
        _phrasing_heatmap(df_conflict, df_conflict, models=SUBSET_MODELS, subset_names=True),
    ))

    # Table 5 (tab:delivery-heatmap): selected subset UT
    blocks.append((
        "Table 5 (tab:delivery-heatmap)",
        _delivery_heatmap(df_conflict, df_conflict, models=SUBSET_MODELS, subset_names=True),
    ))

    # --- Appendix: full evaluation results ------------------------------------

    all_models = sorted(df["model_clean"].unique().tolist())

    # Table tab:main-results-all (both conflict and non-conflict)
    blocks.append((
        "Appendix tab:main-results-all (both)",
        _print_5x5_table(
            df_full=df,
            df_filt=df,
            models=all_models,
            subset_names=False,
            average_label="Average (37 models)",
        ),
    ))

    # Table tab:main-results-conflict
    blocks.append((
        "Appendix tab:main-results-conflict",
        _print_5x5_table(
            df_full=df_conflict,
            df_filt=df_conflict,
            models=all_models,
            subset_names=False,
            average_label="Average (37 models)",
        ),
    ))

    # Table tab:main-results-non-conflict
    blocks.append((
        "Appendix tab:main-results-non-conflict",
        _print_5x5_table(
            df_full=df_non_conflict,
            df_filt=df_non_conflict,
            models=all_models,
            subset_names=False,
            average_label="Average (37 models)",
        ),
    ))

    # --- Appendix: constraint strictness results ------------------------------

    blocks.append((
        "Appendix tab:constraint-strictness-full-gen",
        _strictness_full_block(df_conflict, df_conflict, generic=True),
    ))
    blocks.append((
        "Appendix tab:constraint-strictness-full-domain",
        _strictness_full_block(df_conflict, df_conflict, generic=False, with_bottomrule=False),
    ))

    # --- Appendix: per-(phrasing, strictness) breakdown -----------------------

    blocks.append((
        "Appendix tab:phrasing-strictness-full-gen",
        _pxs_full_block(df_conflict, df_conflict, generic=True),
    ))
    blocks.append((
        "Appendix tab:phrasing-strictness-full-domain",
        _pxs_full_block(df_conflict, df_conflict, generic=False),
    ))

    # --- Appendix: phrasing and delivery --------------------------------------

    blocks.append((
        "Appendix tab:upp-full-gen-dom",
        _phrasing_full(df_conflict, df_conflict),
    ))
    blocks.append((
        "Appendix tab:dv-full-gen-dom",
        _delivery_full(df_conflict, df_conflict),
    ))

    # --- Appendix: constraint groups ------------------------------------------

    blocks.append((
        "Appendix tab:constraint-groups-full",
        _cg_full_block(df_conflict, df_conflict),
    ))

    # --- Emit all blocks -------------------------------------------------------
    for label, block in blocks:
        print(f"% ===== {label} =====")
        print(block)
        print()


if __name__ == "__main__":
    main()
