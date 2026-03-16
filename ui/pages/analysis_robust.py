"""
稳健性与异质性分析处理函数
包含：Bootstrap、剔除特殊样本、分组回归、分位数回归、中介效应、调节效应
（从 analysis.py 拆分，逻辑不变）
"""
from __future__ import annotations

import streamlit as st
import pandas as pd

from ui.components.chart_display import (
    display_figure, display_result_table,
)
from i18n import t


def _run_bootstrap(df: pd.DataFrame, _show_cached_result, _save_result) -> None:
    _show_cached_result("bootstrap")

    from analysis.robustness import bootstrap_confidence_interval

    st.markdown(t("bootstrap_title"))
    numeric_cols = df.select_dtypes(include="number").columns.tolist()

    col1, col2 = st.columns(2)
    with col1:
        dep_var  = st.selectbox(t("bootstrap_dep_label"), numeric_cols, key="boot_dep")
        key_var  = st.selectbox(t("bootstrap_key_label"),
                                [c for c in numeric_cols if c != dep_var],
                                key="boot_key")
    with col2:
        n_boot = st.slider(t("bootstrap_n_label"), 200, 2000, 1000, 100, key="boot_n")
        indep_vars = st.multiselect(t("bootstrap_indep_label"),
                                    [c for c in numeric_cols if c != dep_var],
                                    key="boot_indep")

    if not indep_vars:
        return

    if st.button(t("bootstrap_run_btn"), type="primary"):
        _pbar = st.progress(0, text=f"Bootstrap 进行中（0/{n_boot}）...")
        _boot_last_pct = [0.0]
        def _boot_cb(pct: float) -> None:
            if pct - _boot_last_pct[0] >= 0.05 or pct >= 1.0:
                _boot_last_pct[0] = pct
                _pbar.progress(min(pct, 1.0), text=f"Bootstrap 进行中（{int(pct*n_boot)}/{n_boot}）...")
        result, fig = bootstrap_confidence_interval(
            df, dep_var, indep_vars, key_var, n_boot,
            progress_callback=_boot_cb,
        )
        _pbar.empty()
        display_figure(fig, t("bootstrap_fig_title"), "bootstrap.png")
        st.info(result.get("conclusion", ""))
        _save_result("bootstrap", result, fig)


def _run_exclude_samples(df: pd.DataFrame, _show_cached_result, _save_result) -> None:
    from analysis.robustness import exclude_special_samples

    st.markdown(t("exclude_title"))
    numeric_cols = df.select_dtypes(include="number").columns.tolist()

    dep_var    = st.selectbox(t("exclude_dep_label"), numeric_cols, key="excl_dep")
    key_var    = st.selectbox(t("exclude_key_label"),
                              [c for c in numeric_cols if c != dep_var],
                              key="excl_key")
    indep_vars = st.multiselect(t("exclude_indep_label"),
                                [c for c in numeric_cols if c != dep_var],
                                key="excl_indep")

    st.markdown(t("exclude_cond_title"))
    n_conditions = st.number_input(t("exclude_n_label"), 1, 5, 2, key="excl_n")
    conditions = []
    for i in range(int(n_conditions)):
        col_a, col_b = st.columns([1, 2])
        with col_a:
            label = st.text_input(f"条件{i+1}说明", f"排除条件{i+1}", key=f"excl_label_{i}")
        with col_b:
            query = st.text_input(f"Query（如 industry=='科技'）", "", key=f"excl_query_{i}")
        if query:
            conditions.append({"label": label, "query": query})

    if not indep_vars or not conditions:
        return

    if st.button(t("exclude_run_btn"), type="primary"):
        with st.spinner(t("label_checking")):
            result_df = exclude_special_samples(df, dep_var, indep_vars, key_var, conditions)
            display_result_table(result_df, t("exclude_result_title"))


def _run_subgroup(df: pd.DataFrame, _show_cached_result, _save_result) -> None:
    _show_cached_result("subgroup")

    from analysis.heterogeneity import run_subgroup_regression

    st.markdown(t("subgroup_title"))
    numeric_cols = df.select_dtypes(include="number").columns.tolist()
    all_cols     = list(df.columns)

    col1, col2 = st.columns(2)
    with col1:
        dep_var   = st.selectbox(t("subgroup_dep_label"), numeric_cols, key="sub_dep")
        key_var   = st.selectbox(t("subgroup_key_label"),
                                 [c for c in numeric_cols if c != dep_var],
                                 key="sub_key")
    with col2:
        group_col  = st.selectbox(t("subgroup_group_label"), all_cols, key="sub_group")
        indep_vars = st.multiselect(t("subgroup_indep_label"),
                                    [c for c in numeric_cols if c != dep_var],
                                    key="sub_indep")

    if not indep_vars:
        return

    if st.button(t("subgroup_run_btn"), type="primary"):
        with st.spinner(t("label_regressing")):
            result_df, fig = run_subgroup_regression(df, dep_var, indep_vars, key_var, group_col)
            display_figure(fig, t("subgroup_fig_title"), "subgroup.png")
            display_result_table(result_df, t("subgroup_result_title"))


def _run_quantile(df: pd.DataFrame, _show_cached_result, _save_result) -> None:
    _show_cached_result("quantile")

    from analysis.heterogeneity import run_quantile_regression

    st.markdown(t("quantile_title"))
    numeric_cols = df.select_dtypes(include="number").columns.tolist()

    dep_var    = st.selectbox(t("quantile_dep_label"), numeric_cols, key="qr_dep")
    key_var    = st.selectbox(t("quantile_key_label"),
                              [c for c in numeric_cols if c != dep_var],
                              key="qr_key")
    indep_vars = st.multiselect(t("quantile_indep_label"),
                                [c for c in numeric_cols if c != dep_var],
                                key="qr_indep")

    if not indep_vars or key_var not in indep_vars:
        st.info(t("quantile_include_key"))
        return

    if st.button(t("quantile_run_btn"), type="primary"):
        with st.spinner(t("label_regressing")):
            result_df, fig = run_quantile_regression(df, dep_var, indep_vars, key_var)
            display_figure(fig, t("quantile_fig_title"), "quantile_reg.png")
            display_result_table(result_df, t("quantile_result_title"))


def _run_mediation(df: pd.DataFrame, _show_cached_result, _save_result) -> None:
    _show_cached_result("mediation")

    from analysis.heterogeneity import run_mediation_analysis

    st.markdown(t("mediation_title"))
    numeric_cols = df.select_dtypes(include="number").columns.tolist()

    col1, col2, col3 = st.columns(3)
    with col1:
        treatment = st.selectbox(t("mediation_x_label"), numeric_cols, key="med_x")
    with col2:
        mediator  = st.selectbox(t("mediation_m_label"),
                                 [c for c in numeric_cols if c != treatment],
                                 key="med_m")
    with col3:
        dep_var   = st.selectbox(t("mediation_y_label"),
                                 [c for c in numeric_cols
                                  if c not in [treatment, mediator]],
                                 key="med_y")

    controls = st.multiselect(t("mediation_ctrl_label"),
                              [c for c in numeric_cols
                               if c not in [treatment, mediator, dep_var]],
                              key="med_controls")
    n_boot   = st.slider(t("mediation_boot_label"), 200, 2000, 1000, 100, key="med_boot")

    if st.button(t("mediation_run_btn"), type="primary"):
        _pbar = st.progress(0, text=f"Bootstrap 中介检验中（0/{n_boot}）...")
        _med_last_pct = [0.0]
        def _med_cb(pct: float) -> None:
            if pct - _med_last_pct[0] >= 0.05 or pct >= 1.0:
                _med_last_pct[0] = pct
                _pbar.progress(min(pct, 1.0), text=f"Bootstrap 中介检验中（{int(pct*n_boot)}/{n_boot}）...")
        result, fig = run_mediation_analysis(
            df, dep_var, mediator, treatment, controls or None, n_boot,
            progress_callback=_med_cb,
        )
        _pbar.empty()
        display_figure(fig, t("mediation_fig_title"), "mediation.png")
        col_a, col_b, col_c = st.columns(3)
        col_a.metric(t("mediation_indirect_label"), str(result["indirect_effect"]))
        col_b.metric(t("mediation_direct_label"), str(result["direct_effect"]))
        col_c.metric(t("mediation_pct_label"), f"{result['pct_mediated']}%")
        st.info(result.get("conclusion", ""))
        _save_result("mediation", result, fig)


def _run_moderation(df: pd.DataFrame, _show_cached_result, _save_result) -> None:
    _show_cached_result("moderation")

    from analysis.heterogeneity import run_moderation_analysis

    st.markdown(t("moderation_title"))
    numeric_cols = df.select_dtypes(include="number").columns.tolist()

    col1, col2, col3 = st.columns(3)
    with col1:
        treatment = st.selectbox(t("moderation_x_label"), numeric_cols, key="mod_x")
    with col2:
        moderator = st.selectbox(t("moderation_m_label"),
                                 [c for c in numeric_cols if c != treatment],
                                 key="mod_m")
    with col3:
        dep_var   = st.selectbox(t("moderation_y_label"),
                                 [c for c in numeric_cols
                                  if c not in [treatment, moderator]],
                                 key="mod_y")

    controls = st.multiselect(t("moderation_ctrl_label"),
                              [c for c in numeric_cols
                               if c not in [treatment, moderator, dep_var]],
                              key="mod_controls")

    if st.button(t("moderation_run_btn"), type="primary"):
        with st.spinner(t("label_analyzing")):
            result, fig = run_moderation_analysis(df, dep_var, treatment, moderator,
                                                  controls or None)
            display_figure(fig, t("moderation_fig_title"), "moderation.png")
            col_a, col_b, col_c = st.columns(3)
            col_a.metric(t("moderation_coef_label"),
                         f"{result['interaction_coef']}{result['stars']}")
            col_b.metric(t("moderation_se_label"), str(result["interaction_se"]))
            col_c.metric(t("moderation_pval_label"), str(result["interaction_pval"]))
            st.info(result.get("conclusion", ""))
            _save_result("moderation", result, fig)
