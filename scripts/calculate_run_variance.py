import statistics
from pathlib import Path

import pandas as pd


DIR_MATS = Path(__file__).resolve().parent.parent / "materials"

DISPLAY = {
    "amazon/nova-2-lite": "Nova 2 Lite",
    "openai/gpt-5.4 (medium)": "GPT 5.4 (med)",
    "xai/grok-4.20-0309-reasoning": "Grok 4.20 (R)",
}

SU_GROUPS = {
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
UT_GROUPS = {
    "Format": [
        "format-language", "format-topic", "format-emoji",
        "format-disclaimer", "format-refusal", "format-failed",
        "format-emergency",
    ],
    "Content": [
        "content-lie", "content-omit", "content-invent",
        "only-mention", "flawed",
    ],
    "Tool": [
        "tool-cause", "tool-block", "tool-change", "search",
        "escalate", "flagged",
    ],
    "High-severity": [
        "exec", "read", "web", "memory", "purchase",
        "close", "exfil",
    ],
}


def calculate_variance():
    df0 = pd.read_parquet(DIR_MATS / "results_postproc" / "results_paper.parquet")
    df0 = df0[df0["model"].isin(["amazon/nova-2-lite", "openai/gpt-5.4 (medium)", "xai/grok-4.20-0309-reasoning"])].copy()
    df1 = pd.read_parquet(DIR_MATS / "results_variance" / "results_paper_var_01.parquet")
    df2 = pd.read_parquet(DIR_MATS / "results_variance" / "results_paper_var_02.parquet")
    runs = [df0, df1, df2]


    track_specs = [
        ("Overall", lambda d: d),
        ("SU", lambda d: d[d["set"] == "System-User"]),
        ("UT", lambda d: d[d["set"] == "User-Tool"]),
    ]
    rows = []
    for raw, name in DISPLAY.items():
        for track_label, track_fn in track_specs:
            per_run = [
                round(track_fn(d[d["model"] == raw])["compliant"].mean() * 100, 1)
                for d in runs
            ]
            rows.append({
                "Model": name,
                "Track": track_label,
                "Run 1": per_run[0],
                "Run 2": per_run[1],
                "Run 3": per_run[2],
                "Mean": round(statistics.fmean(per_run), 2),
                "SD": round(statistics.stdev(per_run), 2),
            })
    variance = pd.DataFrame(rows).set_index(["Model", "Track"])

    group_specs = (
        [
            (f"SU / {g}", "System-User", fams)
            for g, fams in SU_GROUPS.items()
        ] +
        [
            (f"UT / {g}", "User-Tool",   fams)
            for g, fams in UT_GROUPS.items()
        ]
    )
    rows = []
    for label, set_, fams in group_specs:
        row = {"group": label}
        for raw, name in DISPLAY.items():
            per_run_vals = []
            for d in runs:
                sub = d[(d["model"] == raw) & (d["set"] == set_) & (d["constraint_family"].isin(fams))]["compliant"]
                per_run_vals.append(round(sub.mean() * 100, 1))
            row[(name, "mean")] = round(statistics.fmean(per_run_vals), 1)
            row[(name, "sd")] = round(statistics.stdev(per_run_vals), 2)
        rows.append(row)

    per_group = pd.DataFrame(rows).set_index("group")
    per_group.columns = pd.MultiIndex.from_tuples(per_group.columns)

    print(variance)
    print()
    print(per_group)


if __name__ == "__main__":
    calculate_variance()
