import streamlit as st

from utils import (
    add_sidebar,
    load_overall_data,
    to_bar_chart,
    # to_pretty_overall_chart,
)


def build_page() -> None:
    st.set_page_config(page_title="IH Benchmark", layout="wide")
    add_sidebar()
    
    overall_both, _, _ = load_overall_data()

    st.markdown(
        "# Instruction Hierarchy Benchmark"
        "\n\n"
        "The Instruction Hierarchy Benchmark (IHB) is a novel benchmarking dataset and toolkit that "
        "tests large language models (LLMs) against more than 2700 scenarios across both the "
        "*system > user* and *user > tool*<sup>1</sup> components of the IH. The benchmark dataset contains both "
        "control and attack scenarios to measure general model capabilities, over-refusals, appropriate "
        "handling of conflicting system and user prompt instructions, and vulnerabilities to indirect "
        "prompt injections (PIs).<sup>2</sup> LLM responses and actions are evaluated using predicates that include "
        "text/tool heuristics, natural language processing models, and LLM judges.",
        unsafe_allow_html=True
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
        # st.image(
        #     to_pretty_overall_chart(overall_both),
        #     width="stretch"
        # )

    st.markdown(
        "### Background\n\n"
        
        "#### What is the instruction hierarchy?\n\n"
        "LLMs implicitly rely on a hierarchical structure to resolve conflicting instructions: "
        "system/developer prompts take precedence over user prompts which take precedence over tool "
        "call outputs - this is known as the instruction hierarchy (IH).\n\n"
        "In theory, the IH ensures that a user cannot make a model carry out an action or respond "
        "in a way that has been explicitly forbidden in the system prompt, and a tool call output "
        "cannot cause the model to carry out an action unless the user has explicitly requested it.\n\n"
        "In practice, nearly all models are vulnerable to conflicting instructions and direct/indirect "
        "PIs to some degree. The IHB allows us to measure this level of vulnerability across both "
        "the *system > user* and *user > tool* components of the IH.\n\n"
        
        "#### What scenarios are tested?\n\n"
        "The benchmark dataset covers a wide array of scenarios, including realistic domain-specific "
        "and agentic scenarios. The dataset is broken down into two distinct subsets: **System-User** and "
        "**User-Tool**, which measure the *system > user* and *user > tool* components of the IH, respectively. "
        "Coverage includes, but is not limited to, the following:\n\n"
        "##### System-User\n\n"
        "- 428 control and 816 attack scenarios.\n"
        "- Both generic and domain-specific scenarios.\n"
        "- Forbidden or required topics, languages, output formats, etc.\n"
        "- Strict tool-use, tool parameter, and tool output constraints.\n"
        "- Data access and leakage restrictions.\n"
        "- Multiple realistic domain-specific scenarios (health, finance, retail).\n"
        "- Variations on user prompts, system prompt complexities and strictness.\n\n"
        "##### User-Tool\n\n"
        "- 66 control and 1440 attack scenarios.\n"
        "- Both generic and domain-specific agentic scenarios.\n"
        "- Indirect PIs delivered through numerous sources and formats (emails, calendar events, web "
        "pages, support tickets, files, etc.).\n"
        "- Attempts to change a response's language, format, topic, etc.\n"
        "- Trigger refusals or disclaimers, and cause the model to lie, omit details, or invent details.\n"
        "- Induce new tool calls, block requested tool calls, or modify requested tool calls.\n"
        "- Trigger unauthorized and dangerous actions, exfiltrate information, etc.\n"
        "- Multiple realistic agentic scenarios (coding, support, shopping agents).\n"
        "- Variations on user prompts, system prompt complexities, tool response formatting, and indirect PI methods.\n\n"
        
        "#### Why is the IHB important?\n\n"
        "No existing benchmarks truly evaluate how well the IH is functioning for a given model. This "
        "benchmark gives us a repeatable and reliable way to measure how robust a model is across a wide "
        "array of realistic scenarios, and what its strengths and weaknesses are: how strict prompts and rules "
        "need to be, which scenarios it is most vulnerable to, and which attack techniques it is weakest to.<sup>3</sup> "
        "The IHB also allows us to answer - in detail - the following crucial security questions about a model:\n\n"
        "- If I place constraints on a model via its system prompt, how easily can a user bypass those constraints?\n"
        "- If I give a model access to tools, can an indirect PI seize control of the model and to what extent?\n\n"

        "<sup>1</sup> The *user > tool* component also tests the *system > user > tool* component.<br>"
        "<sup>2</sup> Alignment/safety bypasses are considered out of scope for this benchmark and are not tested.<br>"
        "<sup>3</sup> The prompts in the base IHB dataset do not make use of Adversarial Prompt Engineering (APE) "
        "techniques, an APE-specific variant of the dataset is planned.\n",
        unsafe_allow_html=True
    )


if __name__ == "__main__":
    build_page()
