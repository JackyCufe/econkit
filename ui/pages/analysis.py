"""
实证分析主页面
提供所有分析方法的 UI 入口
"""
from __future__ import annotations

import streamlit as st
import pandas as pd

from ui.components.variable_selector import (
    select_variables, select_did_variables,
    select_panel_variables,
)
from ui.components.chart_display import (
    display_figure, display_result_table,
    display_regression_summary, display_did_summary,
    display_test_result,
)
from i18n import t

# ── 方法内部 key 列表（顺序决定下拉顺序）──────────────────────────────────────
# 分隔符用特殊前缀 "__group__" 标识
_MENU_ITEMS = [
    "__group_diagnostic__",
    "method_descriptive",
    "method_correlation",
    "method_normality",
    "method_vif",
    "method_heterosked",
    "method_autocorr",
    "__group_regression__",
    "method_ols",
    "method_panel_fe",
    "method_hausman",
    "method_unit_root",
    "__group_causal__",
    "method_did",
    "method_psm",
    "method_rdd",
    "method_iv",
    "method_gmm",
    "__group_robust__",
    "method_bootstrap",
    "method_exclude",
    "__group_hetero__",
    "method_subgroup",
    "method_quantile",
    "method_mediation",
    "method_moderation",
]

# 分隔符 key → 分组标签 key 映射
_GROUP_KEY_MAP = {
    "__group_diagnostic__": "group_diagnostic",
    "__group_regression__": "group_regression",
    "__group_causal__":     "group_causal",
    "__group_robust__":     "group_robust",
    "__group_hetero__":     "group_hetero",
}

# 推荐方法名称 → method key 映射
_NAME_TO_METHOD_KEY: dict[str, str] = {
    "描述统计分析":                    "method_descriptive",
    "OLS 基准回归":                   "method_ols",
    "固定效应模型 (FE)":               "method_panel_fe",
    "双向固定效应 (TWFE)":             "method_panel_fe",
    "DID 双重差分":                   "method_did",
    "交错DID (Callaway-Sant'Anna)":  "method_did",
    "PSM 倾向得分匹配":               "method_psm",
    "RDD 断点回归":                   "method_rdd",
    "IV / 2SLS 工具变量":             "method_iv",
    "动态面板 GMM (Arellano-Bond)":   "method_gmm",
    "中介效应分析":                   "method_mediation",
    "调节效应分析":                   "method_moderation",
    "分组回归":                       "method_subgroup",
    "稳健性检验":                     "method_bootstrap",
}

# method key → handler 函数映射
_METHOD_HANDLERS: dict[str, str] = {
    "method_descriptive": "_run_descriptive",
    "method_correlation": "_run_correlation",
    "method_normality":   "_run_normality",
    "method_vif":         "_run_vif",
    "method_heterosked":  "_run_heterosked",
    "method_autocorr":    "_run_autocorrelation",
    "method_ols":         "_run_ols",
    "method_panel_fe":    "_run_panel_fe",
    "method_hausman":     "_run_hausman",
    "method_unit_root":   "_run_unit_root",
    "method_did":         "_run_did",
    "method_psm":         "_run_psm",
    "method_rdd":         "_run_rdd",
    "method_iv":          "_run_iv",
    "method_gmm":         "_run_gmm",
    "method_bootstrap":   "_run_bootstrap",
    "method_exclude":     "_run_exclude_samples",
    "method_subgroup":    "_run_subgroup",
    "method_quantile":    "_run_quantile",
    "method_mediation":   "_run_mediation",
    "method_moderation":  "_run_moderation",
}


def _get_display_options() -> list[str]:
    """将内部 key 列表转为当前语言的显示文字列表"""
    options = []
    for key in _MENU_ITEMS:
        if key.startswith("__group_"):
            group_key = _GROUP_KEY_MAP.get(key, key)
            options.append(t(group_key))
        else:
            options.append(t(key))
    return options


def _display_to_method_key(display: str) -> str | None:
    """将当前语言的显示文字转回 method key（分隔符返回 None）"""
    for key in _MENU_ITEMS:
        if key.startswith("__group_"):
            continue
        if t(key) == display:
            return key
    return None


def render_analysis() -> None:
    """渲染实证分析页面（步骤3）"""
    if "df" not in st.session_state or st.session_state["df"] is None:
        st.warning(t("analysis_no_data_warning"))
        if st.button(t("analysis_back_home"), key="analysis_back_home"):
            st.session_state["step"] = 1
            st.session_state["page"] = "🏠 首页"
            st.rerun()
        return

    df = st.session_state["df"]

    st.markdown(t("analysis_title"))

    # ── 顶部快速操作栏（完成分析 → 生成报告）────────────────────────────────
    top_col1, top_col2 = st.columns([3, 1])
    with top_col1:
        analysis_results = st.session_state.get("analysis_results", {})
        if analysis_results:
            n_done = len(analysis_results)
            st.success(t("analysis_done_count", n=n_done))
        else:
            st.info(t("analysis_hint"))
    with top_col2:
        if st.button(t("analysis_goto_report"), type="primary", key="goto_report"):
            # 步骤跳转：步骤3 → 步骤4
            st.session_state["step"] = 4
            st.session_state["page"] = "📄 下载报告"
            st.rerun()

    # ── 推荐路径联动区域 ────────────────────────────────────────────────────────
    recommended = st.session_state.get("recommended_methods", [])
    all_options = _get_display_options()

    default_index = 0

    if recommended:
        st.info(t("analysis_recommended_hint", n=len(recommended)))
        cols = st.columns(min(len(recommended), 4))
        for i, name in enumerate(recommended[:8]):
            method_key = _NAME_TO_METHOD_KEY.get(name)
            if method_key:
                option_display = t(method_key)
                if option_display in all_options:
                    with cols[i % 4]:
                        if st.button(f"→ {option_display}", key=f"quick_{i}"):
                            st.session_state["analysis_type"] = option_display
                            st.rerun()
        st.divider()
        # 默认选中第一个推荐方法
        first_method_key = _NAME_TO_METHOD_KEY.get(recommended[0])
        if first_method_key:
            first_display = t(first_method_key)
            if first_display in all_options:
                default_index = all_options.index(first_display)

    # 分析方法选择
    analysis_type = st.selectbox(
        t("analysis_select_label"),
        all_options,
        index=default_index,
        key="analysis_type",
    )

    st.divider()

    # 路由到各分析模块
    method_key = _display_to_method_key(analysis_type)
    if method_key is None:
        st.info(t("analysis_select_placeholder"))
        return

    handler_name = _METHOD_HANDLERS.get(method_key)
    if handler_name:
        handler_fn = globals().get(handler_name)
        if handler_fn:
            handler_fn(df)
        else:
            st.info(f"「{analysis_type}」正在开发中，敬请期待 🚧")
    else:
        st.info(f"「{analysis_type}」正在开发中，敬请期待 🚧")


# ── 描述统计 ──────────────────────────────────────────────────────────────────
def _run_descriptive(df: pd.DataFrame) -> None:
    from analysis.descriptive import compute_descriptive_stats, plot_descriptive_stats

    numeric_cols = df.select_dtypes(include="number").columns.tolist()
    cols = st.multiselect(t("desc_vars_label"), numeric_cols, default=numeric_cols[:6],
                          key="desc_cols")
    if not cols:
        return

    if st.button(t("desc_btn_run"), type="primary"):
        with st.spinner(t("label_computing")):
            stats_df = compute_descriptive_stats(df, cols)
            display_result_table(stats_df, t("desc_result_title"), t("desc_result_note"))
            fig = plot_descriptive_stats(df, cols)
            display_figure(fig, t("desc_fig_title"), "distribution.png")
            _save_result("descriptive", {"stats_df": stats_df}, fig)


# ── 相关矩阵 ──────────────────────────────────────────────────────────────────
def _run_correlation(df: pd.DataFrame) -> None:
    from analysis.descriptive import compute_correlation_matrix, plot_correlation_matrix

    numeric_cols = df.select_dtypes(include="number").columns.tolist()
    cols   = st.multiselect(t("corr_vars_label"), numeric_cols, default=numeric_cols[:6],
                            key="corr_cols")
    method = st.radio(t("corr_method_label"), ["pearson", "spearman"], horizontal=True,
                      key="corr_method")
    if not cols:
        return

    if st.button(t("corr_btn_run"), type="primary"):
        with st.spinner(t("label_computing")):
            corr, pvals = compute_correlation_matrix(df, cols, method)
            display_result_table(corr, f"{method.capitalize()} Correlation Matrix",
                                 t("corr_result_note"))
            fig = plot_correlation_matrix(corr, pvals)
            display_figure(fig, t("corr_fig_title"), "correlation.png")


# ── 正态性检验 ────────────────────────────────────────────────────────────────
def _run_normality(df: pd.DataFrame) -> None:
    from analysis.descriptive import test_normality

    numeric_cols = df.select_dtypes(include="number").columns.tolist()
    cols = st.multiselect(t("norm_vars_label"), numeric_cols, default=numeric_cols[:4],
                          key="norm_cols")
    if not cols:
        return

    if st.button(t("norm_btn_run"), type="primary"):
        with st.spinner(t("label_checking")):
            result_df = test_normality(df, cols)
            display_result_table(result_df, t("norm_result_title"))


# ── VIF ───────────────────────────────────────────────────────────────────────
def _run_vif(df: pd.DataFrame) -> None:
    from analysis.descriptive import compute_vif

    numeric_cols = df.select_dtypes(include="number").columns.tolist()
    cols = st.multiselect(t("vif_vars_label"), numeric_cols,
                          default=numeric_cols[:4], key="vif_cols")
    if len(cols) < 2:
        st.info(t("vif_vars_min"))
        return

    if st.button(t("vif_btn_run"), type="primary"):
        with st.spinner(t("label_computing")):
            vif_df = compute_vif(df, cols)
            display_result_table(vif_df, t("vif_result_title"), t("vif_result_note"))


# ── 自相关检验 ────────────────────────────────────────────────────────────────
def _run_autocorrelation(df: pd.DataFrame) -> None:
    from analysis.descriptive import test_autocorrelation

    st.markdown(t("autocorr_title"))
    numeric_cols = df.select_dtypes(include="number").columns.tolist()

    col1, col2 = st.columns(2)
    with col1:
        dep_var    = st.selectbox(t("autocorr_dep_label"), numeric_cols, key="ac_dep")
    with col2:
        indep_vars = st.multiselect(t("autocorr_indep_label"),
                                    [c for c in numeric_cols if c != dep_var],
                                    key="ac_indep")
    if not indep_vars:
        st.info(t("autocorr_indep_min"))
        return

    if st.button(t("autocorr_btn_run"), type="primary"):
        with st.spinner(t("label_checking")):
            result = test_autocorrelation(df, dep_var, indep_vars)
            display_test_result(result["durbin_watson"], t("autocorr_test_name"), "结论")
            st.info(f"{t('label_recommend')}{result['recommendation']}")


# ── 异方差检验 ────────────────────────────────────────────────────────────────
def _run_heterosked(df: pd.DataFrame) -> None:
    from analysis.descriptive import test_heteroskedasticity

    numeric_cols = df.select_dtypes(include="number").columns.tolist()
    dep_var   = st.selectbox(t("het_dep_label"), numeric_cols, key="het_dep")
    indep_vars = st.multiselect(t("het_indep_label"),
                                [c for c in numeric_cols if c != dep_var],
                                key="het_indep")
    if not indep_vars:
        return

    if st.button(t("het_btn_run"), type="primary"):
        with st.spinner(t("label_checking")):
            result = test_heteroskedasticity(df, dep_var, indep_vars)
            st.markdown(t("het_bp_title"))
            display_test_result(result["breusch_pagan"], t("het_bp_name"))
            st.markdown(t("het_white_title"))
            display_test_result(result["white"], t("het_white_name"))
            st.info(f"{t('label_recommend')}{result['recommendation']}")


# ── 面板单位根检验 ─────────────────────────────────────────────────────────────
def _run_unit_root(df: pd.DataFrame) -> None:
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


# ── OLS 回归 ──────────────────────────────────────────────────────────────────
def _run_ols(df: pd.DataFrame) -> None:
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
            # 将显示文字映射回 cov_type 参数
            cov_param = "HC3" if cov_type == t("ols_se_robust") else "nonrobust"
            result = run_ols(df, dep_var, indep_vars, cov_param)
            display_regression_summary(result)
            _save_result("ols", result, None)


# ── 面板固定效应 ──────────────────────────────────────────────────────────────
def _run_panel_fe(df: pd.DataFrame) -> None:
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


# ── Hausman 检验 ──────────────────────────────────────────────────────────────
def _run_hausman(df: pd.DataFrame) -> None:
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


# ── DID ───────────────────────────────────────────────────────────────────────
def _run_did(df: pd.DataFrame) -> None:
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
                    # 节流：每 5% 更新一次，避免高频重渲染导致页面抖动
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


# ── PSM ───────────────────────────────────────────────────────────────────────
def _run_psm(df: pd.DataFrame) -> None:
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


# ── RDD ───────────────────────────────────────────────────────────────────────
def _run_rdd(df: pd.DataFrame) -> None:
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


# ── IV/2SLS ───────────────────────────────────────────────────────────────────
def _run_iv(df: pd.DataFrame) -> None:
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


# ── 动态面板 GMM ───────────────────────────────────────────────────────────────
def _run_gmm(df: pd.DataFrame) -> None:
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
            # 将显示文字映射回参数
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


# ── Bootstrap ─────────────────────────────────────────────────────────────────
def _run_bootstrap(df: pd.DataFrame) -> None:
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
            # 节流：每 5% 更新一次，避免高频重渲染导致页面抖动
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


# ── 剔除特殊样本 ──────────────────────────────────────────────────────────────
def _run_exclude_samples(df: pd.DataFrame) -> None:
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


# ── 分组回归 ──────────────────────────────────────────────────────────────────
def _run_subgroup(df: pd.DataFrame) -> None:
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


# ── 分位数回归 ────────────────────────────────────────────────────────────────
def _run_quantile(df: pd.DataFrame) -> None:
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


# ── 中介效应 ──────────────────────────────────────────────────────────────────
def _run_mediation(df: pd.DataFrame) -> None:
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
            # 节流：每 5% 更新一次，避免高频重渲染导致页面抖动
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


# ── 调节效应 ──────────────────────────────────────────────────────────────────
def _run_moderation(df: pd.DataFrame) -> None:
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


# ── 工具函数 ──────────────────────────────────────────────────────────────────
def _save_result(key: str, result: dict, fig=None) -> None:
    """将分析结果保存到 session_state，可附带 figure"""
    if "analysis_results" not in st.session_state:
        st.session_state["analysis_results"] = {}
    st.session_state["analysis_results"][key] = result
    if fig is not None:
        if "analysis_figures" not in st.session_state:
            st.session_state["analysis_figures"] = {}
        st.session_state["analysis_figures"][key] = fig
