import pandas as pd
import streamlit as st

from utils import (
    COLUMNS,
    DESCRIPTIONS,
    add_sidebar,
    load_breakdown_data,
    load_column_splits,
    to_bar_chart,
)


# @st.dialog("Dataset")
# def d_set() -> None: st.markdown(DESCRIPTIONS["set"])

@st.dialog("Domain")
def d_domain() -> None: st.markdown(DESCRIPTIONS["domain"])

@st.dialog("Prompt Type")
def d_prompt_type() -> None: st.markdown(DESCRIPTIONS["prompt_type"])

@st.dialog("Attack Type")
def d_attack_type() -> None: st.markdown(DESCRIPTIONS["attack_type"])

@st.dialog("User Prompt Type")
def d_user_prompt_type() -> None: st.markdown(DESCRIPTIONS["user_prompt_type"])

@st.dialog("System Prompt Complexity")
def d_sys_prompt_complexity() -> None: st.markdown(DESCRIPTIONS["sys_prompt_complexity"])

@st.dialog("Rule Complexity")
def d_rule_complexity() -> None: st.markdown(DESCRIPTIONS["rule_complexity"])

@st.dialog("Rule")
def d_rule() -> None: st.markdown(DESCRIPTIONS["rule"])

dmap = {
    # "set": d_set,
    "domain": d_domain,
    "prompt_type": d_prompt_type,
    "attack_type": d_attack_type,
    "user_prompt_type": d_user_prompt_type,
    "sys_prompt_complexity": d_sys_prompt_complexity,
    "rule_complexity": d_rule_complexity,
    "rule": d_rule,
}


def apply_filter(
    df: pd.DataFrame,
    keys: dict[str, list[str]],
    select: dict[str, list[str]]
) -> pd.DataFrame:
    out = df
    for col, opts in keys.items():
        picked = select.get(col)
        if (picked is None) or (len(picked) == 0) or (len(picked) == len(opts)):
            continue
        out = out[out[col].isin(picked)]
    return out


def apply_breakdown(
    df: pd.DataFrame,
    keys: dict[str, list[str]]
) -> tuple[float, dict[str, list[tuple[str, float]]]]:
    if df.empty or ("success" not in df.columns):
        return (0.0, { k: [] for k in keys })
    
    percent = round(float(df["success"].mean() * 100), 2)

    breakdown: dict[str, list[tuple[str, float]]] = {}
    for column in keys:
        part = (
            (
                df[df[column] != "control"]
                if column in ["attack_type", "user_prompt_type", "rule"] else
                df
            )
            .groupby(column, dropna=False)["success"]
            .mean()
            .mul(100)
            .round(2)
            .reset_index(name="percent")
            .sort_values("percent", ascending=False)
        )
        breakdown[column] = list(zip(part[column].tolist(), part["percent"].tolist()))

    return (percent, breakdown)


def format_select(opt: str, column: str = "") -> str:
    if column in ["model"]:
        return opt
    column_splits = load_column_splits()
    sets = column_splits.get(column, {}).get(opt)
    icon = {
        "both": None,
        "su": "◽",
        "ut": "◾",
    }.get(sets, None)
    return f"{icon} {opt}" if icon else opt


def build_breakdown(df: pd.DataFrame, keys: dict[str, list[str]]) -> None:
    filt_state: dict[str, list[str]] = {}
    filt_cols = [key for _, key in COLUMNS if key in keys]
    titles = { key: title for title, key in COLUMNS }
    
    st.divider()
    st.markdown("### Filters")
    st.badge("Option only relevant for System-User dataset", icon="▫️")
    st.badge("Option only relevant for User-Tool dataset", icon="▪️")

    n = len(filt_cols)
    if n == 0:
        return
    n_cols = min(n, 3)
    rows = (n + n_cols - 1) // n_cols
    idx = 0
    for _ in range(rows):
        cols = st.columns(n_cols)
        for col in cols:
            if idx >= n:
                break
            name = filt_cols[idx]
            opts = keys[name]
            title = titles[name]
            picked = col.multiselect(
                title,
                options=opts,
                default=opts,
                key=f"ms_{name}",
                format_func=lambda opt: format_select(opt, column=name)
            )
            filt_state[name] = picked
            idx += 1
    
    st.divider()
    st.markdown("### Filtered Results")

    filt_df = apply_filter(df, keys, filt_state)
    percent, breakdown = apply_breakdown(filt_df, keys)
    
    st.metric("Mean Filtered Score", percent)

    for title, key in COLUMNS:
        rows = breakdown.get(key, [])
        st.markdown(f"##### {title}")
        if key in dmap:
            if st.button("More Details", key=f"details-{key}"):
                dmap[key]()
                
        st.altair_chart(
            to_bar_chart(
                [row[0] for row in rows],
                [float(row[1]) for row in rows],
                "",
                k=title,
                v="Score",
                set_colors=False,
                strip_org=(key == "model"),
                max_height=(1100 if key == "rule" else None)
            ),
            width="stretch"
        )
        st.divider()


def build_page() -> None:
    st.set_page_config(page_title="Breakdown", layout="wide")
    add_sidebar()

    df, keys = load_breakdown_data()

    st.markdown(
        "# Breakdown"
        "\n\n"
        "Explore the benchmark results with numerous filters and a feature-by-feature breakdown."
    )

    if df.empty:
        st.error("No breakdown data found")
    else:
        build_breakdown(df, keys)

build_page()
