from pathlib import Path
from typing import Final

import pandas as pd


DIR_MATS: Final[Path] = Path(__file__).resolve().parent.parent / "materials"
PATH_SRC: Final[Path] = DIR_MATS / "results_simple.parquet"
PATH_DST: Final[Path] = DIR_MATS / "results_paper.parquet"


GENERIC_DOMAINS: Final[frozenset[str]] = frozenset({
    "generic",
    "generic-calendar",
    "generic-email",
    "generic-file",
    "generic-webpage",
})

DOMAIN_SIMPLIFIED: Final[dict[str, str]] = {
    "generic": "generic",
    "generic-calendar": "generic",
    "generic-email": "generic",
    "generic-file": "generic",
    "generic-webpage": "generic",
    "finance": "finance",
    "health": "health",
    "retail": "retail",
    "agent-coding": "coding",
    "agent-health": "health",
    "agent-retail": "retail",
}

CONSTRAINT_STRICTNESS_SU: Final[dict[str, str]] = {
    "simple":   "L_1 (simple)",
    "hardened": "L_2 (hardened)",
    "refusal":  "L_3 (refusal)",
}
CONSTRAINT_STRICTNESS_UT: Final[dict[str, str]] = {
    "none":     "L_1 (none)",
    "simple":   "L_2 (simple)",
    "hardened": "L_3 (hardened)",
}

CONFLICT_PRESENTATION_SU: Final[dict[str, str]] = {
    "direct":  "P_1 (explicit)",
    "implied": "P_2 (implicit)",
    "control": "non-conflict",
}
CONFLICT_PRESENTATION_UT: Final[dict[str, str]] = {
    "plain":       "D_1 (plain)",
    "breakout":    "D_2 (breakout)",
    "acknowledge": "D_3 (acknowledge)",
    "switch":      "D_4 (switch)",
    "control":     "non-conflict",
}

USER_PROMPT_PHRASING: Final[dict[str, str]] = {
    "direct":  "P_1 (explicit)",
    "casual":  "P_2 (implicit)",
    "summary": "P_2 (implicit)",
    "implied": "P_2 (implicit)",
    "control": "non-conflict",
}


def apply_filters(df: pd.DataFrame) -> pd.DataFrame:
    # Exclude simple/complex SU domain-specific base system prompt complexities
    df = df[~(
        (df["set"] == "System-User")
        & (~df["domain"].isin(GENERIC_DOMAINS))
        & (df["sys_prompt_complexity"] != "full")
    )].copy()

    # Exclude *-jsonkv UT attack type sub-variants
    df = df[~(
        (df["set"] == "User-Tool")
        & df["attack_type"].str.endswith("-jsonkv")
    )].copy()
    
    return df


def apply_mappings(df: pd.DataFrame) -> pd.DataFrame:
    su_mask = df["set"] == "System-User"
    ut_mask = df["set"] == "User-Tool"

    # Clean up domains and provide a couple extra columns of detail
    df = df.rename(columns={"domain": "domain_exact"})
    df["domain"] = df["domain_exact"].map(DOMAIN_SIMPLIFIED)
    df["is_generic"] = df["domain_exact"].isin(GENERIC_DOMAINS)

    # rule_complexity -> constraint_strictness
    df["constraint_strictness"] = pd.NA
    df.loc[su_mask, "constraint_strictness"] = (
        df.loc[su_mask, "rule_complexity"].map(CONSTRAINT_STRICTNESS_SU)
    )
    df.loc[ut_mask, "constraint_strictness"] = (
        df.loc[ut_mask, "rule_complexity"].map(CONSTRAINT_STRICTNESS_UT)
    )

    # attack_type -> conflict_presentation
    df["conflict_presentation"] = pd.NA
    df.loc[su_mask, "conflict_presentation"] = (
        df.loc[su_mask, "attack_type"].map(CONFLICT_PRESENTATION_SU)
    )
    df.loc[ut_mask, "conflict_presentation"] = (
        df.loc[ut_mask, "attack_type"].map(CONFLICT_PRESENTATION_UT)
    )

    # user_prompt_type -> user_prompt_phrasing
    df["user_prompt_phrasing"] = df["user_prompt_type"].map(USER_PROMPT_PHRASING)

    # prompt_type -> scenario_type
    df["scenario_type"] = df["prompt_type"].map({"attack": "conflict", "control": "non-conflict"})

    # Rename remaining columns
    df = df.rename(columns={
        "success": "compliant",
        "sys_prompt_complexity": "system_persona",
        "rule": "constraint_family",
        "subrule": "constraint_instance",
    })

    # Drop redundant columns
    df = df.drop(columns=["rule_complexity", "attack_type", "prompt_type", "user_prompt_type"])

    return df[[
        "model",
        "set",
        "domain",
        "domain_exact",
        "is_generic",
        "system_persona",
        "constraint_family",
        "constraint_instance",
        "constraint_strictness",
        "conflict_presentation",
        "user_prompt_phrasing",
        "scenario_type",
        "compliant",
    ]]


def main() -> None:
    df = pd.read_parquet(PATH_SRC)
    n0 = len(df)
    df = apply_filters(df)
    df = apply_mappings(df)
    df.to_parquet(PATH_DST, index=False)
    print(f"Wrote dataframe to {PATH_DST} and filtered out {n0 - len(df)} row(s)")


if __name__ == "__main__":
    main()
