"""
因果推断分析处理函数
包含：DID、PSM、RDD、IV/2SLS
（从 analysis.py 拆分，逻辑不变）
"""
from __future__ import annotations

import streamlit as st
import pandas as pd

from ui.components.variable_selector import select_did_variables
from ui.components.chart_display import (
    display_figure, display_result_table,
    display_did_summary, display_test_result,
)
from i18n import t


def _run_did(df: pd.DataFrame, _show_cached_result, _save_result) -> None:
    _show_cached_result("did")

    from analysis.causal_did import (
        run_basic_did, run_twfe_did,
        run_parallel_trend_test, run_placebo_test,
    )

    st.markdown(t("did_title"))
    vars_config = select_did_variables(df, "did")

    step_opts = [
        t("did_step_basic"),
        t("did_step_twfe"),
        t("did_step_parallel"),
        t("did_step_placebo"),
    ]

    sub_analyses = st.multiselect(
        t("did_steps_label"),
        step_opts,
        default=[t("did_step_basic"), t("did_step_parallel"), t("did_step_placebo")],
        key="did_steps",
    )

    n_sim = 1000
    if t("did_step_placebo") in sub_analyses:
        n_sim = st.slider(t("did_nsim_label"), 100, 2000, 1000, 100, key="did_nsim")

    if st.button(t("did_run_btn"), type="primary"):
        with st.spinner(t("did_running")):
            basic_result = None
            if t("did_step_basic") in sub_analyses:
                st.markdown(t("did_basic_title"))
                basic_result = run_basic_did(
                    df,
                    dep_var   = vars_config["dep_var"],
                    treat_col = vars_config["treat_col"],
                    post_col  = vars_config["post_col"],
                    did_col   = vars_config["did_col"],
                    controls  = vars_config["controls"] or None,
                )
                display_did_summary(basic_result, t("did_display_basic"))

            if t("did_step_twfe") in sub_analyses:
                st.markdown(t("did_twfe_title"))
                twfe_result = run_twfe_did(
                    df,
                    dep_var   = vars_config["dep_var"],
                    did_col   = vars_config["did_col"],
                    id_col    = vars_config["id_col"],
                    time_col  = vars_config["time_col"],
                    controls  = vars_config["controls"] or None,
                )
                display_did_summary(twfe_result, t("did_display_twfe"))

            if t("did_step_parallel") in sub_analyses:
                st.markdown(t("did_parallel_title"))
                pt_result, pt_fig = run_parallel_trend_test(
                    df,
                    dep_var    = vars_config["dep_var"],
                    treat_col  = vars_config["treat_col"],
                    time_col   = vars_config["time_col"],
                    treat_year = vars_config["treat_year"],
                    id_col     = vars_config["id_col"],
                    controls   = vars_config["controls"] or None,
                )
                if "error" not in pt_result:
                    display_figure(pt_fig, t("did_parallel_fig_title"), "parallel_trend.png")
                    st.info(pt_result.get("conclusion", ""))
                else:
                    st.error(f"平行趋势检验失败：{pt_result['error']}")

            if t("did_step_placebo") in sub_analyses:
                st.markdown(t("did_placebo_title"))
                real_coef = basic_result["did_coef"] if basic_result else None
                _pbar = st.progress(0, text=f"安慰剂检验进行中（0/{n_sim}）...")
                _placebo_last_pct = [0.0]
                def _placebo_cb(pct: float) -> None:
                    if pct - _placebo_last_pct[0] >= 0.05 or pct >= 1.0:
                        _placebo_last_pct[0] = pct
                        _pbar.progress(min(pct, 1.0), text=f"安慰剂检验进行中（{int(pct*n_sim)}/{n_sim}）...")
                pl_result, pl_fig = run_placebo_test(
                    df,
                    dep_var    = vars_config["dep_var"],
                    treat_col  = vars_config["treat_col"],
                    post_col   = vars_config["post_col"],
                    controls   = vars_config["controls"] or None,
                    n_sim      = n_sim,
                    real_coef  = real_coef,
                    progress_callback = _placebo_cb,
                )
                _pbar.empty()
                display_figure(pl_fig, f"安慰剂检验（{n_sim}次置换）", "placebo_test.png")
                st.info(pl_result.get("conclusion", ""))


def _run_psm(df: pd.DataFrame, _show_cached_result, _save_result) -> None:
    _show_cached_result("psm")

    from analysis.causal_psm import (
        estimate_propensity_score, knn_matching,
        kernel_matching, check_covariate_balance, plot_psm_distributions,
    )

    st.markdown(t("psm_title"))
    all_cols     = list(df.columns)
    numeric_cols = df.select_dtypes(include="number").columns.tolist()

    col1, col2 = st.columns(2)
    with col1:
        treat_col = st.selectbox(t("psm_treat_label"), all_cols,
                                 index=next((i for i, c in enumerate(all_cols)
                                             if "treat" in c.lower()), 0),
                                 key="psm_treat")
        dep_var = st.selectbox(t("psm_dep_label"), numeric_cols, key="psm_dep")
    with col2:
        covariates = st.multiselect(t("psm_cov_label"),
                                    [c for c in numeric_cols if c != dep_var],
                                    key="psm_covs")
        method_opts = [t("psm_knn"), t("psm_kernel")]
        method = st.radio(t("psm_method_label"), method_opts,
                          horizontal=True, key="psm_method")

    k = st.slider(t("psm_k_label"), 1, 5, 1, key="psm_k") if method == t("psm_knn") else 1

    if not covariates:
        st.info(t("psm_covs_min"))
        return

    if st.button(t("psm_run_btn"), type="primary"):
        with st.spinner(t("label_matching")):
            ps_df = estimate_propensity_score(df, treat_col, covariates)
            fig_dist = plot_psm_distributions(ps_df, treat_col)
            display_figure(fig_dist, t("psm_dist_fig_title"), "psm_distribution.png")

            if method == t("psm_knn"):
                result = knn_matching(ps_df, df[dep_var].reset_index(drop=True),
                                      treat_col, k=k)
            else:
                result = kernel_matching(ps_df, df[dep_var].reset_index(drop=True),
                                         treat_col)

            st.markdown(f"#### ATT ({result['method']})")
            col_a, col_b, col_c = st.columns(3)
            col_a.metric(t("psm_att_label"), f"{result['att']}{result['stars']}")
            col_b.metric(t("psm_se_label"), str(result["att_se"]))
            col_c.metric(t("psm_pval_label"), str(result["p_value"]))


def _run_rdd(df: pd.DataFrame, _show_cached_result, _save_result) -> None:
    _show_cached_result("rdd")

    from analysis.causal_rdd import (
        run_rdd_local_linear, select_optimal_bandwidth,
        mccrary_density_test, plot_rdd,
    )

    st.markdown(t("rdd_title"))
    numeric_cols = df.select_dtypes(include="number").columns.tolist()

    col1, col2 = st.columns(2)
    with col1:
        dep_var     = st.selectbox(t("rdd_dep_label"), numeric_cols, key="rdd_dep")
        running_var = st.selectbox(t("rdd_run_label"), numeric_cols, key="rdd_run")
    with col2:
        cutoff    = st.number_input(t("rdd_cutoff_label"), value=60.0, key="rdd_cutoff")
        bw        = st.number_input(t("rdd_bw_label"), value=0.0, step=0.1, key="rdd_bw")
        poly      = st.radio(t("rdd_poly_label"), [1, 2], horizontal=True, key="rdd_poly")

    bandwidth = bw if bw > 0 else None

    if st.button(t("rdd_run_btn"), type="primary"):
        with st.spinner(t("label_analyzing")):
            fig = plot_rdd(df, dep_var, running_var, cutoff, bandwidth)
            display_figure(fig, t("rdd_fig_title"), "rdd_plot.png")

            if bandwidth is None:
                bw_result = select_optimal_bandwidth(df, dep_var, running_var, cutoff)
                bandwidth = bw_result["optimal_bandwidth"]
                st.info(f"📏 建议带宽：{bandwidth}（score 标准差 × 1.0）")
                if not bw_result["sensitivity_table"].empty:
                    display_result_table(bw_result["sensitivity_table"], "带宽敏感性分析")

            result = run_rdd_local_linear(df, dep_var, running_var, cutoff, bandwidth, poly)
            if "error" in result:
                st.error(result["error"])
            else:
                col_a, col_b, col_c, col_d = st.columns(4)
                col_a.metric(t("rdd_coef_label"), f"{result['coef']}{result['stars']}")
                col_b.metric(t("rdd_se_label"), str(result["se"]))
                col_c.metric(t("rdd_pval_label"), str(result["pval"]))
                col_d.metric(t("rdd_n_label"), str(result["n_obs"]))

            st.markdown(t("rdd_density_title"))
            density_result, density_fig = mccrary_density_test(df, running_var, cutoff)
            display_figure(density_fig, t("rdd_density_fig_title"), "mccrary.png")
            display_test_result(density_result, t("rdd_density_result_title"))


def _run_iv(df: pd.DataFrame, _show_cached_result, _save_result) -> None:
    _show_cached_result("iv")

    from analysis.causal_iv import run_iv_2sls

    st.markdown(t("iv_title"))
    numeric_cols = df.select_dtypes(include="number").columns.tolist()

    col1, col2 = st.columns(2)
    with col1:
        dep_var   = st.selectbox(t("iv_dep_label"), numeric_cols, key="iv_dep")
        endog_var = st.selectbox(t("iv_endog_label"),
                                 [c for c in numeric_cols if c != dep_var],
                                 key="iv_endog")
    with col2:
        instruments = st.multiselect(
            t("iv_instr_label"),
            [c for c in numeric_cols if c not in [dep_var, endog_var]],
            key="iv_instruments",
        )

    controls = st.multiselect(
        t("iv_ctrl_label"),
        [c for c in numeric_cols if c not in [dep_var, endog_var] + instruments],
        key="iv_controls",
    )

    if not instruments:
        st.info(t("iv_instruments_min"))
        return

    if st.button(t("iv_run_btn"), type="primary"):
        with st.spinner(t("label_estimating")):
            result = run_iv_2sls(df, dep_var, endog_var, instruments, controls or None)
            if "error" in result:
                st.error(result["error"])
                return

            col_a, col_b, col_c = st.columns(3)
            col_a.metric(t("iv_coef_label"), f"{result['coef']}{result['stars']}")
            col_b.metric(t("iv_se_label"), str(result["se"]))
            col_c.metric(t("iv_f_label"),
                         f"{result['first_stage_f']:.2f}"
                         + (" ✅" if result["weak_iv_pass"] else " ⚠️弱工具"))

            display_test_result(result["wu_hausman"], t("iv_wu_hausman_name"), "结论")
            if "p值" in result.get("sargan", {}):
                display_test_result(result["sargan"], t("iv_sargan_name"), "结论")
