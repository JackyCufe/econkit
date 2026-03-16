"""
回归分析处理函数
包含：OLS、面板FE、Hausman检验、面板单位根、GMM
（从 analysis.py 拆分，逻辑不变）
"""
from __future__ import annotations

import streamlit as st
import pandas as pd

from ui.components.variable_selector import select_panel_variables
from ui.components.chart_display import (
    display_regression_summary, display_test_result,
)
from i18n import t


def _run_ols(df: pd.DataFrame, _show_cached_result, _save_result) -> None:
    _show_cached_result("ols")

    from analysis.panel_regression import run_ols

    st.markdown(t("ols_title"))
    numeric_cols = df.select_dtypes(include="number").columns.tolist()

    col1, col2 = st.columns(2)
    with col1:
        dep_var = st.selectbox(t("ols_dep_label"), numeric_cols, key="ols_dep")
    with col2:
        cov_opts = [t("ols_se_robust"), t("ols_se_plain")]
        cov_type = st.selectbox(t("ols_se_label"), cov_opts, key="ols_cov")
    indep_vars = st.multiselect(t("ols_indep_label"),
                                [c for c in numeric_cols if c != dep_var],
                                key="ols_indep")
    if not indep_vars:
        st.info(t("ols_indep_min"))
        return

    if st.button(t("ols_run_btn"), type="primary"):
        with st.spinner(t("label_regressing")):
            cov_param = "HC3" if cov_type == t("ols_se_robust") else "nonrobust"
            result = run_ols(df, dep_var, indep_vars, cov_param)
            display_regression_summary(result)
            _save_result("ols", result, None)


def _run_panel_fe(df: pd.DataFrame, _show_cached_result, _save_result) -> None:
    _show_cached_result("panel_fe")

    from analysis.panel_regression import run_panel_model

    st.markdown(t("panel_fe_title"))
    vars_config = select_panel_variables(df, "panel")

    if not vars_config["indep_vars"]:
        st.info(t("panel_indep_min"))
        return

    if st.button(t("panel_run_btn"), type="primary"):
        with st.spinner(t("label_regressing")):
            result = run_panel_model(
                df,
                dep_var    = vars_config["dep_var"],
                indep_vars = vars_config["indep_vars"],
                id_col     = vars_config["id_col"],
                time_col   = vars_config["time_col"],
                model_type = vars_config["model_type"],
            )
            display_regression_summary(result)
            _save_result("panel_fe", result)


def _run_hausman(df: pd.DataFrame, _show_cached_result, _save_result) -> None:
    from analysis.panel_regression import run_hausman_test

    st.markdown(t("hausman_title"))
    numeric_cols = df.select_dtypes(include="number").columns.tolist()
    all_cols     = list(df.columns)

    col1, col2 = st.columns(2)
    with col1:
        id_col   = st.selectbox(t("hausman_id_label"), all_cols, key="hm_id")
        dep_var  = st.selectbox(t("hausman_dep_label"), numeric_cols, key="hm_dep")
    with col2:
        time_col = st.selectbox(t("hausman_time_label"), all_cols, key="hm_time")
        indep_vars = st.multiselect(t("hausman_indep_label"),
                                    [c for c in numeric_cols if c != dep_var],
                                    key="hm_indep")

    if not indep_vars:
        return

    if st.button(t("hausman_run_btn"), type="primary"):
        with st.spinner(t("label_checking")):
            result = run_hausman_test(df, dep_var, indep_vars, id_col, time_col)
            if "error" in result:
                st.error(result["error"])
            else:
                display_test_result(result, t("hausman_result_name"), "结论")


def _run_unit_root(df: pd.DataFrame, _show_cached_result, _save_result) -> None:
    from analysis.panel_regression import test_panel_unit_root

    st.markdown(t("unit_root_title"))
    numeric_cols = df.select_dtypes(include="number").columns.tolist()
    all_cols     = list(df.columns)

    col1, col2 = st.columns(2)
    with col1:
        test_col = st.selectbox(t("unit_root_var_label"), numeric_cols, key="ur_col")
    with col2:
        id_col   = st.selectbox(t("unit_root_id_label"), all_cols, key="ur_id")
        time_col = st.selectbox(t("unit_root_time_label"), all_cols, key="ur_time")

    if st.button(t("unit_root_run_btn"), type="primary"):
        with st.spinner(t("label_checking")):
            result = test_panel_unit_root(df, test_col, id_col, time_col)
            if "error" in result:
                st.error(result["error"])
            else:
                display_test_result(result, t("unit_root_result_name"), "结论")
                st.info(f"{t('label_recommend')}{result.get('建议', '')}")


def _run_gmm(df: pd.DataFrame, _show_cached_result, _save_result) -> None:
    _show_cached_result("gmm")

    from analysis.panel_regression import run_dynamic_panel_gmm

    st.markdown(t("gmm_title"))
    numeric_cols = df.select_dtypes(include="number").columns.tolist()
    all_cols     = list(df.columns)

    col1, col2 = st.columns(2)
    with col1:
        dep_var  = st.selectbox(t("gmm_dep_label"), numeric_cols, key="gmm_dep")
        id_col   = st.selectbox(t("gmm_id_label"), all_cols, key="gmm_id")
    with col2:
        indep_vars = st.multiselect(
            t("gmm_indep_label"),
            [c for c in numeric_cols if c != dep_var],
            key="gmm_indep",
        )
        time_col = st.selectbox(t("gmm_time_label"), all_cols, key="gmm_time")

    gmm_type_opts = [t("gmm_diff"), t("gmm_sys")]
    gmm_type_display = st.radio(t("gmm_type_label"), gmm_type_opts,
                                horizontal=True, key="gmm_type")
    st.info(t("gmm_info"))

    if not indep_vars:
        st.info(t("gmm_indep_min"))
        return

    if st.button(t("gmm_run_btn"), type="primary"):
        with st.spinner(t("gmm_running")):
            gmm_type_param = "difference" if gmm_type_display == t("gmm_diff") else "system"
            result = run_dynamic_panel_gmm(
                df, dep_var, indep_vars, id_col, time_col,
                gmm_type=gmm_type_param,
            )
            if "error" in result:
                st.error(f"❌ {result['error']}")
            else:
                display_regression_summary(result)

                if result.get("ar_tests"):
                    st.markdown(t("gmm_ar_title"))
                    ar_df = pd.DataFrame(result["ar_tests"])
                    st.dataframe(ar_df, use_container_width=True)
                    st.caption(t("gmm_ar_caption"))

                if result.get("hansen"):
                    st.markdown(t("gmm_hansen_title"))
                    h = result["hansen"]
                    col_a, col_b, col_c = st.columns(3)
                    col_a.metric(t("gmm_hansen_chi2_label"), str(h["chi2统计量"]))
                    col_b.metric(t("gmm_hansen_df_label"), str(h["自由度"]))
                    col_c.metric(t("gmm_hansen_pval_label"), str(h["p值"]))
                    st.info(h["结论"])

                if result.get("ar_note"):
                    st.success(result["ar_note"])
                _save_result("gmm", result)
