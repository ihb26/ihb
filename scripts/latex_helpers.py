# NOTE: This code is AI Generated

from typing import Final

import pandas as pd


STRICTNESS_LEVELS: Final[list[str]] = ["L1", "L2", "L3"]
PROMPT_PHRASINGS: Final[list[str]] = ["P1", "P2"]
DELIVERY_VARIANTS: Final[list[str]] = ["D1", "D2", "D3", "D4"]

SU_FAMILY_GROUPS: Final[list[str]] = [
    "Format Contract",
    "Content Fidelity",
    "Disclosure Control",
    "Capability Authorization",
    "Parameter Authorization",
    "Semantic Boundary",
]

UT_FAMILY_GROUPS: Final[list[str]] = [
    "Format Contract",
    "Content Fidelity",
    "Disclosure Control",
    "Capability Authorization",
    "Parameter Authorization",
    "Task Integrity",
]


def format_score(value: float, na: str = r"--", std_dev: float | None = None) -> str:
    if pd.isna(value):
        return na
    score = f"{float(value) * 100:.1f}"
    if std_dev is not None and not pd.isna(std_dev):
        return rf"\scoreSD{{{score}}}{{{float(std_dev) * 100:.1f}}}"
    return rf"\score{{{score}}}"


def display_model(model: str, subset: bool = False) -> str:
    if subset:
        return model.replace(" (medium)", "")
    return model


def _metric_rows(
    metrics: pd.DataFrame,
    model: str | None = None,
    models: list[str] | None = None,
    **filters: str | bool,
) -> pd.DataFrame:
    rows = metrics.reset_index()
    if model:
        rows = rows[rows["model"] == model]
    if models is not None:
        rows = rows[rows["model"].isin(models)]
    for column, value in filters.items():
        rows = rows[rows[column] == value]
    return rows


def _metric_value(
    metrics: pd.DataFrame,
    model: str | None = None,
    models: list[str] | None = None,
    **filters: str | bool,
) -> float:
    rows = _metric_rows(metrics, model=model, models=models, **filters)
    return float(rows["success"].mean())


def _metric_score(
    metrics: pd.DataFrame,
    model: str | None = None,
    models: list[str] | None = None,
    stddev: bool = False,
    **filters: str | bool,
) -> str:
    rows = _metric_rows(metrics, model=model, models=models, **filters)
    std_dev = None
    # An aggregate's SD cannot be recovered by averaging its constituents' SDs.
    if stddev and model is not None and len(rows) == 1 and "std_dev" in rows:
        std_dev = rows.iloc[0]["std_dev"]
    return format_score(float(rows["success"].mean()), std_dev=std_dev)


def _available_models(metrics: pd.DataFrame, models: list[str]) -> list[str]:
    available = set(metrics.reset_index()["model"])
    return [model for model in models if model in available]


def _sort_models(
    metrics: pd.DataFrame,
    models: list[str],
    **filters: str | bool,
) -> list[str]:
    models = _available_models(metrics, models)
    models = sorted(models)
    return sorted(
        models,
        key=lambda model: (
            float("-inf")
            if pd.isna(_metric_value(metrics, model=model, **filters))
            else _metric_value(metrics, model=model, **filters)
        ),
        reverse=True,
    )


def _top_bottom_models(
    metrics: pd.DataFrame,
    models: list[str],
    **filters: str | bool,
) -> list[str]:
    models = _sort_models(metrics, models, **filters)
    selected = models[:2] + models[-2:]
    return list(dict.fromkeys(selected))


def _main_results_row(
    label: str,
    metrics_overall: pd.DataFrame,
    metrics_su: pd.DataFrame,
    metrics_ut: pd.DataFrame,
    model: str | None = None,
    models: list[str] | None = None,
    stddev: bool = False,
) -> str:
    cells = [
        label,
        _metric_score(metrics_overall, model=model, models=models, stddev=stddev),
        _metric_score(metrics_su, model=model, models=models, stddev=stddev),
        _metric_score(metrics_ut, model=model, models=models, stddev=stddev),
    ]
    return " & ".join(cells) + r" \\"


def main_results_table(
    metrics_overall: pd.DataFrame,
    metrics_su: pd.DataFrame,
    metrics_ut: pd.DataFrame,
    models: list[str],
    average_models: list[str],
    subset_names: bool = False,
    stddev: bool = False,
) -> str:
    out = [
        r"\begin{tabular}{lrrr}",
        r"\toprule",
        r"\textbf{Model}",
        r"& \textbf{Overall}",
        r"& \textbf{\SU{} Average}",
        r"& \textbf{\UT{} Average} \\",
        r"\midrule",
    ]
    
    for model in _sort_models(metrics_overall, models):
        out.append(_main_results_row(display_model(model, subset_names), metrics_overall, metrics_su, metrics_ut, model=model, stddev=stddev))

    average_models = _available_models(metrics_overall, average_models)
    out.append(r"\midrule")
    out.append(_main_results_row(f"Average ({len(average_models)} models)", metrics_overall, metrics_su, metrics_ut, models=average_models, stddev=stddev))
    out.append(r"\bottomrule")
    out.append(r"\end{tabular}")
    return "\n".join(out)


def _strictness_value(
    metrics: pd.DataFrame,
    is_domain: bool,
    strictness: str,
    model: str | None = None,
    models: list[str] | None = None,
) -> float:
    return _metric_value(metrics, model=model, models=models, is_domain=is_domain, constraint_strictness=strictness)


def constraint_strictness_table(
    metrics_su: pd.DataFrame,
    metrics_ut: pd.DataFrame,
    models: list[str],
    average_models: list[str],
) -> str:
    out = [
        r"\begin{tabular}{l @{\hspace{3pt}\vrule width 0.3pt\hspace{3pt}} r @{\hspace{3pt}\vrule width 0.3pt\hspace{3pt}} rrr @{\hspace{3pt}\vrule width 0.3pt\hspace{3pt}} r @{\hspace{3pt}\vrule width 0.3pt\hspace{3pt}} rrr}",
        r"\toprule",
        r"& \multicolumn{4}{c}{\SU Compliance (\%)}",
        r"  & \multicolumn{4}{c}{\UT Compliance (\%)} \\",
        r"\cmidrule(lr){2-5} \cmidrule(lr){6-9}",
        r"\textbf{Group}",
        r"& \textbf{Model}",
        r"& \textbf{$L_1$}",
        r"& \textbf{$L_2$}",
        r"& \textbf{$L_3$}",
        r"& \textbf{Model}",
        r"& \textbf{$L_1$}",
        r"& \textbf{$L_2$}",
        r"& \textbf{$L_3$} \\",
        r"\midrule",
    ]

    for i, is_domain in enumerate([False, True]):
        group_label = "Generic" if not is_domain else r"\shortstack{Domain/\\Agentic}"
        su_models = _top_bottom_models(metrics_su, models, is_domain=is_domain, constraint_strictness="L1")
        ut_models = _top_bottom_models(metrics_ut, models, is_domain=is_domain, constraint_strictness="L1")
        out.append(rf"\multirow{{{min(len(su_models), len(ut_models)) + 1}}}{{*}}{{{group_label}}}")

        for su_model, ut_model in zip(su_models, ut_models):
            cells = ["& " + display_model(su_model, True)]
            for strictness in STRICTNESS_LEVELS:
                cells.append(format_score(_strictness_value(metrics_su, is_domain, strictness, model=su_model)))
            cells.append(display_model(ut_model, True))
            for strictness in STRICTNESS_LEVELS:
                cells.append(format_score(_strictness_value(metrics_ut, is_domain, strictness, model=ut_model)))
            out.append(" & ".join(cells) + r" \\")

        out.append(r"\cmidrule(lr){2-9}")
        cells = ["& Average"]
        for strictness in STRICTNESS_LEVELS:
            cells.append(format_score(_strictness_value(metrics_su, is_domain, strictness, models=average_models)))
        cells.append("Average")
        for strictness in STRICTNESS_LEVELS:
            cells.append(format_score(_strictness_value(metrics_ut, is_domain, strictness, models=average_models)))
        out.append(" & ".join(cells) + r" \\")
        if i == 0:
            out.append(r"\midrule")

    out.append(r"\bottomrule")
    out.append(r"\end{tabular}")
    return "\n".join(out)


def constraint_strictness_full_table(
    metrics_su: pd.DataFrame,
    metrics_ut: pd.DataFrame,
    models: list[str],
    average_models: list[str],
    is_domain: bool,
) -> str:
    out = [
        r"\begin{tabular}{l @{\hspace{3pt}\vrule width 0.3pt\hspace{3pt}} r @{\hspace{3pt}\vrule width 0.3pt\hspace{3pt}} rrr @{\hspace{3pt}\vrule width 0.3pt\hspace{3pt}} r @{\hspace{3pt}\vrule width 0.3pt\hspace{3pt}} rrr}",
        r"\toprule",
        r"& \multicolumn{4}{c}{\SU Compliance (\%)}",
        r"  & \multicolumn{4}{c}{\UT Compliance (\%)} \\",
        r"\cmidrule(lr){2-5} \cmidrule(lr){6-9}",
        r"\textbf{Group}",
        r"& \textbf{Model}",
        r"& \textbf{$L_1$}",
        r"& \textbf{$L_2$}",
        r"& \textbf{$L_3$}",
        r"& \textbf{Model}",
        r"& \textbf{$L_1$}",
        r"& \textbf{$L_2$}",
        r"& \textbf{$L_3$} \\",
        r"\midrule",
    ]

    group_label = r"\shortstack{Domain/\\Agentic}" if is_domain else "Generic"
    su_models = _sort_models(metrics_su, models, is_domain=is_domain, constraint_strictness="L1")
    ut_models = _sort_models(metrics_ut, models, is_domain=is_domain, constraint_strictness="L1")
    out.append(rf"\multirow{{{min(len(su_models), len(ut_models)) + 1}}}{{*}}{{{group_label}}}")

    for su_model, ut_model in zip(su_models, ut_models):
        cells = ["& " + display_model(su_model)]
        for strictness in STRICTNESS_LEVELS:
            cells.append(format_score(_strictness_value(metrics_su, is_domain, strictness, model=su_model)))
        cells.append(display_model(ut_model))
        for strictness in STRICTNESS_LEVELS:
            cells.append(format_score(_strictness_value(metrics_ut, is_domain, strictness, model=ut_model)))
        out.append(" & ".join(cells) + r" \\")

    out.append(r"\cmidrule(lr){2-9}")
    cells = ["& Average"]
    for strictness in STRICTNESS_LEVELS:
        cells.append(format_score(_strictness_value(metrics_su, is_domain, strictness, models=average_models)))
    cells.append("Average")
    for strictness in STRICTNESS_LEVELS:
        cells.append(format_score(_strictness_value(metrics_ut, is_domain, strictness, models=average_models)))
    out.append(" & ".join(cells) + r" \\")
    out.append(r"\bottomrule")
    out.append(r"\end{tabular}")
    return "\n".join(out)


def prompt_phrasing_constraint_strictness_table(
    metrics_overall: pd.DataFrame,
    metrics_su: pd.DataFrame,
    metrics_ut: pd.DataFrame,
    models: list[str],
    average_models: list[str],
    is_domain: bool,
) -> str:
    out = [
        r"\begin{tabular}{l @{\hspace{3pt}\vrule width 0.3pt\hspace{3pt}} rrr @{\hspace{3pt}\vrule width 0.3pt\hspace{3pt}} rrr @{\hspace{3pt}\vrule width 0.3pt\hspace{3pt}} rrr @{\hspace{3pt}\vrule width 0.3pt\hspace{3pt}} rrr}",
        r"\toprule",
        r"& \multicolumn{6}{c}{\SU Compliance (\%)}",
        r"  & \multicolumn{6}{c}{\UT Compliance (\%)} \\",
        r"\cmidrule(lr){2-7} \cmidrule(lr){8-13}",
        r"& \multicolumn{3}{c}{$P_1$ (explicit)}",
        r"& \multicolumn{3}{c}{$P_2$ (implicit)}",
        r"& \multicolumn{3}{c}{$P_1$ (explicit)}",
        r"& \multicolumn{3}{c}{$P_2$ (implicit)} \\",
        r"\cmidrule(lr){2-4} \cmidrule(lr){5-7} \cmidrule(lr){8-10} \cmidrule(lr){11-13}",
        r"\textbf{Model}",
        r"& \textbf{$L_1$} & \textbf{$L_2$} & \textbf{$L_3$}",
        r"& \textbf{$L_1$} & \textbf{$L_2$} & \textbf{$L_3$}",
        r"& \textbf{$L_1$} & \textbf{$L_2$} & \textbf{$L_3$}",
        r"& \textbf{$L_1$} & \textbf{$L_2$} & \textbf{$L_3$} \\",
        r"\midrule",
    ]

    for model in _sort_models(metrics_overall, models, is_domain=is_domain):
        cells = [display_model(model)]
        for phrasing in PROMPT_PHRASINGS:
            for strictness in STRICTNESS_LEVELS:
                cells.append(format_score(_metric_value(metrics_su, model=model, is_domain=is_domain, prompt_phrasing=phrasing, constraint_strictness=strictness)))
        for phrasing in PROMPT_PHRASINGS:
            for strictness in STRICTNESS_LEVELS:
                cells.append(format_score(_metric_value(metrics_ut, model=model, is_domain=is_domain, prompt_phrasing=phrasing, constraint_strictness=strictness)))
        out.append(" & ".join(cells) + r" \\")

    out.append(r"\midrule")
    cells = ["Average"]
    for phrasing in PROMPT_PHRASINGS:
        for strictness in STRICTNESS_LEVELS:
            cells.append(format_score(_metric_value(metrics_su, models=average_models, is_domain=is_domain, prompt_phrasing=phrasing, constraint_strictness=strictness)))
    for phrasing in PROMPT_PHRASINGS:
        for strictness in STRICTNESS_LEVELS:
            cells.append(format_score(_metric_value(metrics_ut, models=average_models, is_domain=is_domain, prompt_phrasing=phrasing, constraint_strictness=strictness)))
    out.append(" & ".join(cells) + r" \\")
    out.append(r"\bottomrule")
    out.append(r"\end{tabular}")
    return "\n".join(out)


def family_group_table(
    metrics_overall: pd.DataFrame,
    metrics_su: pd.DataFrame,
    metrics_ut: pd.DataFrame,
    models: list[str],
    average_models: list[str],
    selected: bool = False,
) -> str:
    out = [
        r"\begin{tabular}{l @{\hspace{3pt}\vrule width 0.3pt\hspace{3pt}} rrrrrr @{\hspace{3pt}\vrule width 0.3pt\hspace{3pt}} rrrrrr}",
        r"\toprule",
        r"& \multicolumn{6}{c}{\SU Compliance (\%)}",
        r"& \multicolumn{6}{c}{\UT Compliance (\%)} \\",
        r"\cmidrule(lr){2-7} \cmidrule(lr){8-13}",
        r"\textbf{Model}",
    ]
    for family_group in SU_FAMILY_GROUPS:
        out.append(rf"& \textbf{{{family_group}}}")
    for family_group in UT_FAMILY_GROUPS:
        out.append(rf"& \textbf{{{family_group}}}")
    out[-1] += r" \\"
    out.append(r"\midrule")

    if selected:
        models = _top_bottom_models(metrics_overall, models)
    else:
        models = _sort_models(metrics_overall, models)

    for model in models:
        cells = [display_model(model, selected)]
        for family_group in SU_FAMILY_GROUPS:
            cells.append(format_score(_metric_value(metrics_su, model=model, family_group=family_group)))
        for family_group in UT_FAMILY_GROUPS:
            cells.append(format_score(_metric_value(metrics_ut, model=model, family_group=family_group)))
        out.append(" & ".join(cells) + r" \\")

    out.append(r"\midrule")
    cells = ["Average"]
    for family_group in SU_FAMILY_GROUPS:
        cells.append(format_score(_metric_value(metrics_su, models=average_models, family_group=family_group)))
    for family_group in UT_FAMILY_GROUPS:
        cells.append(format_score(_metric_value(metrics_ut, models=average_models, family_group=family_group)))
    out.append(" & ".join(cells) + r" \\")
    out.append(r"\bottomrule")
    out.append(r"\end{tabular}")
    return "\n".join(out)


def family_average_table(
    metrics: pd.DataFrame,
    models: list[str],
) -> str:
    """Show mean compliance for each family, lowest first within each track."""
    rows = metrics.reset_index()
    rows = rows[rows["model"].isin(models)]
    averages = (
        rows.groupby(["track", "family_group", "family"], as_index=False)["success"]
        .mean()
        .sort_values(["track", "success", "family"])
    )
    out = [
        r"\begin{tabular}{l l l r}",
        r"\toprule",
        r"\textbf{Track} & \textbf{Family} & \textbf{Family group} & \textbf{Average (\%)} \\",
        r"\midrule",
    ]
    for i, (track, label) in enumerate([("system-user", r"\SU"), ("user-tool", r"\UT")]):
        if i:
            out.append(r"\midrule")
        for row in averages[averages["track"] == track].itertuples(index=False):
            cells = [label, rf"\texttt{{{row.family}}}", row.family_group, format_score(row.success)]
            out.append(" & ".join(cells) + r" \\")
    out.append(r"\bottomrule")
    out.append(r"\end{tabular}")
    return "\n".join(out)


def prompt_phrasing_table(
    metrics: pd.DataFrame,
    models: list[str],
    average_models: list[str],
) -> str:
    out = [
        r"\begin{tabular}{l @{\hspace{3pt}\vrule width 0.3pt\hspace{3pt}} r @{\hspace{3pt}\vrule width 0.3pt\hspace{3pt}} rr}",
        r"\toprule",
        r"\textbf{Group}",
        r"& \textbf{Model}",
        r"& \textbf{$P_1$}",
        r"& \textbf{$P_2$} \\",
        r"\midrule",
    ]

    for i, is_domain in enumerate([False, True]):
        group_label = "Generic" if not is_domain else r"\shortstack{Domain/\\Agentic}"
        selected_models = _top_bottom_models(metrics, models, is_domain=is_domain, prompt_phrasing="P1")
        out.append(rf"\multirow{{{len(selected_models) + 1}}}{{*}}{{{group_label}}}")

        for model in selected_models:
            cells = ["& " + display_model(model, True)]
            for phrasing in PROMPT_PHRASINGS:
                cells.append(format_score(_metric_value(metrics, model=model, is_domain=is_domain, prompt_phrasing=phrasing)))
            out.append(" & ".join(cells) + r" \\")

        out.append(r"\cmidrule(lr){2-4}")
        cells = ["& Average"]
        for phrasing in PROMPT_PHRASINGS:
            cells.append(format_score(_metric_value(metrics, models=average_models, is_domain=is_domain, prompt_phrasing=phrasing)))
        out.append(" & ".join(cells) + r" \\")
        if i == 0:
            out.append(r"\midrule")

    out.append(r"\bottomrule")
    out.append(r"\end{tabular}")
    return "\n".join(out)


def prompt_phrasing_full_table(
    metrics: pd.DataFrame,
    models: list[str],
    average_models: list[str],
) -> str:
    out = [
        r"\begin{tabular}{l r r r @{\hspace{8pt}\vrule width 0.3pt\hspace{8pt}} l r r r}",
        r"\toprule",
        r"\multicolumn{4}{c}{\textbf{Generic scenarios}}",
        r"& \multicolumn{4}{c}{\textbf{Domain-specific/agentic scenarios}} \\",
        r"\cmidrule(lr){1-4} \cmidrule(lr){5-8}",
        r"\textbf{Group} & \textbf{Model} & \textbf{$P_1$} & \textbf{$P_2$}",
        r"& \textbf{Group} & \textbf{Model} & \textbf{$P_1$} & \textbf{$P_2$} \\",
        r"\midrule",
    ]

    generic_models = _sort_models(metrics, models, is_domain=False, prompt_phrasing="P1")
    domain_models = _sort_models(metrics, models, is_domain=True, prompt_phrasing="P1")
    n_rows = min(len(generic_models), len(domain_models))

    for i, (generic_model, domain_model) in enumerate(zip(generic_models, domain_models)):
        generic_label = rf"\multirow{{{n_rows}}}{{*}}{{Generic}}" if i == 0 else ""
        domain_label = rf"\multirow{{{n_rows}}}{{*}}{{\shortstack{{Domain/\\Agentic}}}}" if i == 0 else ""
        cells = [generic_label, display_model(generic_model)]
        for phrasing in PROMPT_PHRASINGS:
            cells.append(format_score(_metric_value(metrics, model=generic_model, is_domain=False, prompt_phrasing=phrasing)))
        cells += [domain_label, display_model(domain_model)]
        for phrasing in PROMPT_PHRASINGS:
            cells.append(format_score(_metric_value(metrics, model=domain_model, is_domain=True, prompt_phrasing=phrasing)))
        out.append(" & ".join(cells) + r" \\")

    out.append(r"\cmidrule(lr){2-4} \cmidrule(lr){6-8}")
    cells = ["", "Average"]
    for phrasing in PROMPT_PHRASINGS:
        cells.append(format_score(_metric_value(metrics, models=average_models, is_domain=False, prompt_phrasing=phrasing)))
    cells += ["", "Average"]
    for phrasing in PROMPT_PHRASINGS:
        cells.append(format_score(_metric_value(metrics, models=average_models, is_domain=True, prompt_phrasing=phrasing)))
    out.append(" & ".join(cells) + r" \\")
    out.append(r"\bottomrule")
    out.append(r"\end{tabular}")
    return "\n".join(out)


def delivery_variant_table(
    metrics: pd.DataFrame,
    models: list[str],
    average_models: list[str],
) -> str:
    out = [
        r"\begin{tabular}{l @{\hspace{3pt}\vrule width 0.3pt\hspace{3pt}} r @{\hspace{3pt}\vrule width 0.3pt\hspace{3pt}} rrrr}",
        r"\toprule",
        r"\textbf{Group}",
        r"& \textbf{Model}",
        r"& \textbf{$D_1$}",
        r"& \textbf{$D_2$}",
        r"& \textbf{$D_3$}",
        r"& \textbf{$D_4$} \\",
        r"\midrule",
    ]

    for i, is_domain in enumerate([False, True]):
        group_label = "Generic" if not is_domain else r"\shortstack{Domain/\\Agentic}"
        selected_models = _top_bottom_models(metrics, models, is_domain=is_domain, delivery_variant="D1")
        out.append(rf"\multirow{{{len(selected_models) + 1}}}{{*}}{{{group_label}}}")

        for model in selected_models:
            cells = ["& " + display_model(model, True)]
            for delivery_variant in DELIVERY_VARIANTS:
                cells.append(format_score(_metric_value(metrics, model=model, is_domain=is_domain, delivery_variant=delivery_variant)))
            out.append(" & ".join(cells) + r" \\")

        out.append(r"\cmidrule(lr){2-6}")
        cells = ["& Average"]
        for delivery_variant in DELIVERY_VARIANTS:
            cells.append(format_score(_metric_value(metrics, models=average_models, is_domain=is_domain, delivery_variant=delivery_variant)))
        out.append(" & ".join(cells) + r" \\")
        if i == 0:
            out.append(r"\midrule")

    out.append(r"\bottomrule")
    out.append(r"\end{tabular}")
    return "\n".join(out)


def delivery_variant_full_table(
    metrics: pd.DataFrame,
    models: list[str],
    average_models: list[str],
) -> str:
    out = [
        r"\begin{tabular}{l r r r r r @{\hspace{8pt}\vrule width 0.3pt\hspace{8pt}} l r r r r r}",
        r"\toprule",
        r"\multicolumn{6}{c}{\textbf{Generic scenarios}}",
        r"& \multicolumn{6}{c}{\textbf{Domain-specific/agentic scenarios}} \\",
        r"\cmidrule(lr){1-6} \cmidrule(lr){7-12}",
        r"\textbf{Group} & \textbf{Model} & \textbf{$D_1$} & \textbf{$D_2$} & \textbf{$D_3$} & \textbf{$D_4$}",
        r"& \textbf{Group} & \textbf{Model} & \textbf{$D_1$} & \textbf{$D_2$} & \textbf{$D_3$} & \textbf{$D_4$} \\",
        r"\midrule",
    ]

    generic_models = _sort_models(metrics, models, is_domain=False, delivery_variant="D1")
    domain_models = _sort_models(metrics, models, is_domain=True, delivery_variant="D1")
    n_rows = min(len(generic_models), len(domain_models))

    for i, (generic_model, domain_model) in enumerate(zip(generic_models, domain_models)):
        generic_label = rf"\multirow{{{n_rows}}}{{*}}{{Generic}}" if i == 0 else ""
        domain_label = rf"\multirow{{{n_rows}}}{{*}}{{\shortstack{{Domain/\\Agentic}}}}" if i == 0 else ""
        cells = [generic_label, display_model(generic_model)]
        for delivery_variant in DELIVERY_VARIANTS:
            cells.append(format_score(_metric_value(metrics, model=generic_model, is_domain=False, delivery_variant=delivery_variant)))
        cells += [domain_label, display_model(domain_model)]
        for delivery_variant in DELIVERY_VARIANTS:
            cells.append(format_score(_metric_value(metrics, model=domain_model, is_domain=True, delivery_variant=delivery_variant)))
        out.append(" & ".join(cells) + r" \\")

    out.append(r"\cmidrule(lr){2-6} \cmidrule(lr){8-12}")
    cells = ["", "Average"]
    for delivery_variant in DELIVERY_VARIANTS:
        cells.append(format_score(_metric_value(metrics, models=average_models, is_domain=False, delivery_variant=delivery_variant)))
    cells += ["", "Average"]
    for delivery_variant in DELIVERY_VARIANTS:
        cells.append(format_score(_metric_value(metrics, models=average_models, is_domain=True, delivery_variant=delivery_variant)))
    out.append(" & ".join(cells) + r" \\")
    out.append(r"\bottomrule")
    out.append(r"\end{tabular}")
    return "\n".join(out)


def track_family_group_table(
    metrics_track: pd.DataFrame,
    metrics_family_group: pd.DataFrame,
    family_groups: list[str],
    models: list[str],
    average_models: list[str],
) -> str:
    headers = ["Model", "Track Average"] + family_groups
    out = [
        r"\begin{tabular}{lrrrrrrr}",
        r"\toprule",
        " & ".join(rf"\textbf{{{label}}}" for label in headers) + r" \\",
        r"\midrule",
    ]
    for model in _sort_models(metrics_track, models) + [None]:
        if model is None:
            out.append(r"\midrule")
        filters = {"models": average_models} if model is None else {"model": model}
        cells = [model if model is not None else f"Average ({len(average_models)} configs.)"]
        cells.append(_metric_score(metrics_track, stddev=True, **filters))
        for family_group in family_groups:
            cells.append(_metric_score(metrics_family_group, family_group=family_group, stddev=True, **filters))
        out.append(" & ".join(cells) + r" \\")
    out += [r"\bottomrule", r"\end{tabular}"]
    return "\n".join(out)


def paired_factor_table(
    metrics_track_su: pd.DataFrame,
    metrics_track_ut: pd.DataFrame,
    metrics_su: pd.DataFrame,
    metrics_ut: pd.DataFrame,
    factor: str,
    levels: list[str],
    models: list[str],
    average_models: list[str],
) -> str:
    n = len(levels) + 1
    columns = "l" + "r" * len(levels)
    headers = [r"\textbf{Model}"] + [rf"\textbf{{${level[0]}_{level[1:]}$}}" for level in levels]
    out = [
        rf"\begin{{tabular}}{{{columns}|{columns}}}",
        r"\toprule",
        rf"\multicolumn{{{n}}}{{c}}{{\SU{{}}}} & \multicolumn{{{n}}}{{c}}{{\UT{{}}}} \\",
        rf"\cmidrule(lr){{1-{n}}} \cmidrule(lr){{{n + 1}-{2 * n}}}",
        " & ".join(headers + headers) + r" \\",
        r"\midrule",
    ]
    su_models = _sort_models(metrics_track_su, models)
    ut_models = _sort_models(metrics_track_ut, models)
    mean_label = f"Mean ({len(average_models)} configs.)" if len(models) == len(average_models) else f"Mean ({len(average_models)})"
    for su_model, ut_model in list(zip(su_models, ut_models)) + [(None, None)]:
        if su_model is None:
            out.append(r"\midrule")
        cells = []
        for metrics, model in [(metrics_su, su_model), (metrics_ut, ut_model)]:
            filters = {"models": average_models} if model is None else {"model": model}
            cells.append(model if model is not None else mean_label)
            for level in levels:
                cells.append(_metric_score(metrics, stddev=True, **filters, **{factor: level}))
        out.append(" & ".join(cells) + r" \\")
    out += [r"\bottomrule", r"\end{tabular}"]
    return "\n".join(out)


def factor_table(
    metrics_track: pd.DataFrame,
    metrics: pd.DataFrame,
    factor: str,
    levels: list[str],
    models: list[str],
    average_models: list[str],
) -> str:
    headers = [r"\textbf{Model}"] + [rf"\textbf{{${level[0]}_{level[1:]}$}}" for level in levels]
    out = [
        r"\begin{tabular}{l" + "r" * len(levels) + "}",
        r"\toprule",
        " & ".join(headers) + r" \\",
        r"\midrule",
    ]
    for model in _sort_models(metrics_track, models) + [None]:
        if model is None:
            out.append(r"\midrule")
        filters = {"models": average_models} if model is None else {"model": model}
        cells = [model if model is not None else f"Mean ({len(average_models)} configs.)"]
        for level in levels:
            cells.append(_metric_score(metrics, stddev=True, **filters, **{factor: level}))
        out.append(" & ".join(cells) + r" \\")
    out += [r"\bottomrule", r"\end{tabular}"]
    return "\n".join(out)


def conflict_family_group_table(
    metrics_overall: pd.DataFrame,
    metrics_track_su: pd.DataFrame,
    metrics_track_ut: pd.DataFrame,
    metrics_su: pd.DataFrame,
    metrics_ut: pd.DataFrame,
    models: list[str],
    average_models: list[str],
) -> str:
    headers = ["Model", "Overall", "Average", "FC", "CF", "DC", "CA", "PA", "SB", "Average", "FC", "CF", "DC", "CA", "PA", "TI"]
    out = [
        r"\begin{tabular}{lr|rrrrrrr|rrrrrrr}",
        r"\toprule",
        r"& & \multicolumn{7}{c}{\SU{} Compliance (\%)} & \multicolumn{7}{c}{\UT{} Compliance (\%)} \\",
        r"\cmidrule(lr){3-9} \cmidrule(lr){10-16}",
        " & ".join(rf"\textbf{{{label}}}" for label in headers) + r" \\",
        r"\midrule",
    ]
    for model in _sort_models(metrics_overall, models) + [None]:
        if model is None:
            out.append(r"\midrule")
        filters = {"models": average_models} if model is None else {"model": model}
        cells = [model if model is not None else f"Mean ({len(average_models)} configs.)"]
        cells.append(_metric_score(metrics_overall, stddev=True, **filters))
        for track, categories, groups in [(metrics_track_su, metrics_su, SU_FAMILY_GROUPS), (metrics_track_ut, metrics_ut, UT_FAMILY_GROUPS)]:
            cells.append(_metric_score(track, stddev=True, **filters))
            for family_group in groups:
                cells.append(_metric_score(categories, family_group=family_group, stddev=True, **filters))
        out.append(" & ".join(cells) + r" \\")
    out += [r"\bottomrule", r"\end{tabular}"]
    return "\n".join(out)


def non_conflict_table(
    metrics_overall: pd.DataFrame,
    metrics_su: pd.DataFrame,
    metrics_ut: pd.DataFrame,
    models: list[str],
    average_models: list[str],
) -> str:
    out = [
        r"\begin{tabular}{lrr}",
        r"\toprule",
        r"\textbf{Model} & \textbf{\SU{}} & \textbf{\UT{}} \\",
        r"\midrule",
    ]
    for model in _sort_models(metrics_overall, models) + [None]:
        if model is None:
            out.append(r"\midrule")
        filters = {"models": average_models} if model is None else {"model": model}
        cells = [model if model is not None else f"Mean ({len(average_models)} configs.)"]
        cells += [_metric_score(metrics, stddev=True, **filters) for metrics in [metrics_su, metrics_ut]]
        out.append(" & ".join(cells) + r" \\")
    out += [r"\bottomrule", r"\end{tabular}"]
    return "\n".join(out)


def joint_factors_table(
    metrics_overall: pd.DataFrame,
    metrics_su: pd.DataFrame,
    metrics_ut: pd.DataFrame,
    metrics_phrasing_su: pd.DataFrame,
    metrics_phrasing_ut: pd.DataFrame,
    models: list[str],
    average_models: list[str],
) -> str:
    headers = [r"\textbf{Model}"] + [r"\textbf{$L_1$}", r"\textbf{$L_2$}", r"\textbf{$L_3$}", r"\textbf{Average}"] * 4
    out = [
        r"\begin{tabular}{l|rrrr|rrrr|rrrr|rrrr}",
        r"\toprule",
        r"& \multicolumn{8}{c}{\SU{} Compliance (\%)} & \multicolumn{8}{c}{\UT{} Compliance (\%)} \\",
        r"\cmidrule(lr){2-9} \cmidrule(lr){10-17}",
        r"& \multicolumn{4}{c}{$P_1$} & \multicolumn{4}{c}{$P_2$} & \multicolumn{4}{c}{$P_1$} & \multicolumn{4}{c}{$P_2$} \\",
        r"\cmidrule(lr){2-5} \cmidrule(lr){6-9} \cmidrule(lr){10-13} \cmidrule(lr){14-17}",
        " & ".join(headers) + r" \\",
        r"\midrule",
    ]
    for model in _sort_models(metrics_overall, models) + [None]:
        if model is None:
            out.append(r"\midrule")
        filters = {"models": average_models} if model is None else {"model": model}
        cells = [model if model is not None else f"Mean ({len(average_models)} configs.)"]
        for metrics, phrasing_metrics in [(metrics_su, metrics_phrasing_su), (metrics_ut, metrics_phrasing_ut)]:
            for phrasing in PROMPT_PHRASINGS:
                for strictness in STRICTNESS_LEVELS:
                    score = _metric_score(metrics, prompt_phrasing=phrasing, constraint_strictness=strictness, stddev=True, **filters)
                    cells.append("---" if score == "--" else score)
                cells.append(_metric_score(phrasing_metrics, prompt_phrasing=phrasing, stddev=True, **filters))
        out.append(" & ".join(cells) + r" \\")
    out += [r"\bottomrule", r"\end{tabular}"]
    return "\n".join(out)


def delivery_strictness_table(
    metrics_track: pd.DataFrame,
    metrics: pd.DataFrame,
    models: list[str],
    average_models: list[str],
) -> str:
    headers = [r"\textbf{Model}"] + [r"\textbf{$L_1$}", r"\textbf{$L_2$}", r"\textbf{$L_3$}"] * 4
    out = [
        r"\begin{tabular}{lrrr|rrr|rrr|rrr}",
        r"\toprule",
        r"& \multicolumn{3}{c}{$D_1$} & \multicolumn{3}{c}{$D_2$} & \multicolumn{3}{c}{$D_3$} & \multicolumn{3}{c}{$D_4$} \\",
        r"\cmidrule(lr){2-4} \cmidrule(lr){5-7} \cmidrule(lr){8-10} \cmidrule(lr){11-13}",
        " & ".join(headers) + r" \\",
        r"\midrule",
    ]
    for model in _sort_models(metrics_track, models) + [None]:
        if model is None:
            out.append(r"\midrule")
        filters = {"models": average_models} if model is None else {"model": model}
        cells = [model if model is not None else f"Mean ({len(average_models)} models)"]
        for delivery in DELIVERY_VARIANTS:
            for strictness in STRICTNESS_LEVELS:
                cells.append(_metric_score(metrics, delivery_variant=delivery, constraint_strictness=strictness, stddev=True, **filters))
        out.append(" & ".join(cells) + r" \\")
    out += [r"\bottomrule", r"\end{tabular}"]
    return "\n".join(out)
