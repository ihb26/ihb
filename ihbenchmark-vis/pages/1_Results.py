import streamlit as st

from utils import (
    add_sidebar,
    load_overall_data,
    to_bar_chart,
)


def build_page() -> None:
    st.set_page_config(page_title="Results", layout="wide")
    add_sidebar()

    overall_both, overall_su, overall_ut = load_overall_data()
    if overall_both.empty:
        st.error("No overall data found")
        st.stop()

    st.markdown(
        "# Results"
        "\n\n"
        "Overall results across both the **System-User** and **User-Tool** subsets of the dataset."
    )

    if overall_both.empty:
        st.error("No overall data found")
    else:
        st.altair_chart(
            to_bar_chart(
                overall_both["model"].tolist(),
                overall_both["score"].tolist(),
                title="Overall Results",
                k="Model",
                v="Score"
            ),
            width="stretch",
        )

    st.divider()
    st.markdown(
        "## System-User Results"
        "\n\n"
        "Tests how well a model follows the **system/developer > user** instruction "
        "hierarchy while punishing over-refusals."
    )
    if overall_su.empty:
        st.error("No System-User data found")
    else:
        st.altair_chart(
            to_bar_chart(
                overall_su["model"].tolist(),
                overall_su["score"].tolist(),
                title="System-User Results",
                k="Model",
                v="Score"
            ),
            width="stretch",
        )

    st.divider()
    st.markdown(
        "## User-Tool Results"
        "\n\n"
        "Tests how well a model follows the **user > tool** instruction hierarchy "
        "while not following instructions injected into tool call outputs."
    )
    if overall_su.empty:
        st.error("No User-Tool data found")
    else:
        st.altair_chart(
            to_bar_chart(
                overall_ut["model"].tolist(),
                overall_ut["score"].tolist(),
                title="User-Tool Results",
                k="Model",
                v="Score"
            ),
            width="stretch",
        )


build_page()
