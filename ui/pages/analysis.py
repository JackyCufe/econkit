"""
实证分析主页面
提供所有分析方法的 UI 入口
"""
from __future__ import annotations

import streamlit as st
import pandas as pd

from ui.components.chart_display import (
    display_figure, display_result_table,
    display_test_result,
)
from i18n import t

# ── 方法内部 key 列表（顺序决定下拉顺序）──────────────────────────────────────
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

_GROUP_KEY_MAP = {
    "__group_diagnostic__": "group_diagnostic",
    "__group_regression__": "group_regression",
    "__group_causal__":     "group_causal",
    "__group_robust__":     "group_robust",
    "__group_hetero__":     "group_hetero",
}

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
    options = []
    for key in _MENU_ITEMS:
        if key.startswith("__group_"):
            group_key = _GROUP_KEY_MAP.get(key, key)
            options.append(t(group_key))
        else:
            options.append(t(key))
    return options


def _display_to_method_key(display: str) -> str | None:
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
            st.session_state["step"] = 4
            st.session_state["page"] = "📄 下载报告"
            st.rerun()

    recommended = st.session_state.get("recommended_methods", [])
    all_options = _get_display_options()
    default_index = 0

    if recommended:
        rec_names = [t(_NAME_TO_METHOD_KEY[n]) for n in recommended
                     if n in _NAME_TO_METHOD_KEY and t(_NAME_TO_METHOD_KEY[n]) in all_options]
        if rec_names:
            st.info(t("analysis_recommended_hint", n=len(rec_names))
                    + "  \n" + "、".join(f"**{r}**" for r in rec_names[:6]))
        st.divider()
        first_method_key = _NAME_TO_METHOD_KEY.get(recommended[0])
        if first_method_key:
            first_display = t(first_method_key)
            if first_display in all_options:
                default_index = all_options.index(first_display)

    analysis_type = st.selectbox(
        t("analysis_select_label"),
        all_options,
        index=default_index,
        key="analysis_type",
    )

    st.divider()

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


# ── 诊断类函数（保留在此文件）────────────────────────────────────────────────

def _run_descriptive(df: pd.DataFrame) -> None:
    from analysis.descriptive import compute_descriptive_stats, plot_descriptive_stats

    _show_cached_result("descriptive")

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


# ── 回归分析（委托给 analysis_regression.py）──────────────────────────────────
def _run_ols(df: pd.DataFrame) -> None:
    from ui.pages.analysis_regression import _run_ols as _impl
    _impl(df, _show_cached_result, _save_result)


def _run_panel_fe(df: pd.DataFrame) -> None:
    from ui.pages.analysis_regression import _run_panel_fe as _impl
    _impl(df, _show_cached_result, _save_result)


def _run_hausman(df: pd.DataFrame) -> None:
    from ui.pages.analysis_regression import _run_hausman as _impl
    _impl(df, _show_cached_result, _save_result)


def _run_unit_root(df: pd.DataFrame) -> None:
    from ui.pages.analysis_regression import _run_unit_root as _impl
    _impl(df, _show_cached_result, _save_result)


def _run_gmm(df: pd.DataFrame) -> None:
    from ui.pages.analysis_regression import _run_gmm as _impl
    _impl(df, _show_cached_result, _save_result)


# ── 因果推断（委托给 analysis_causal.py）──────────────────────────────────────
def _run_did(df: pd.DataFrame) -> None:
    from ui.pages.analysis_causal import _run_did as _impl
    _impl(df, _show_cached_result, _save_result)


def _run_psm(df: pd.DataFrame) -> None:
    from ui.pages.analysis_causal import _run_psm as _impl
    _impl(df, _show_cached_result, _save_result)


def _run_rdd(df: pd.DataFrame) -> None:
    from ui.pages.analysis_causal import _run_rdd as _impl
    _impl(df, _show_cached_result, _save_result)


def _run_iv(df: pd.DataFrame) -> None:
    from ui.pages.analysis_causal import _run_iv as _impl
    _impl(df, _show_cached_result, _save_result)


# ── 稳健性/异质性（委托给 analysis_robust.py）────────────────────────────────
def _run_bootstrap(df: pd.DataFrame) -> None:
    from ui.pages.analysis_robust import _run_bootstrap as _impl
    _impl(df, _show_cached_result, _save_result)


def _run_exclude_samples(df: pd.DataFrame) -> None:
    from ui.pages.analysis_robust import _run_exclude_samples as _impl
    _impl(df, _show_cached_result, _save_result)


def _run_subgroup(df: pd.DataFrame) -> None:
    from ui.pages.analysis_robust import _run_subgroup as _impl
    _impl(df, _show_cached_result, _save_result)


def _run_quantile(df: pd.DataFrame) -> None:
    from ui.pages.analysis_robust import _run_quantile as _impl
    _impl(df, _show_cached_result, _save_result)


def _run_mediation(df: pd.DataFrame) -> None:
    from ui.pages.analysis_robust import _run_mediation as _impl
    _impl(df, _show_cached_result, _save_result)


def _run_moderation(df: pd.DataFrame) -> None:
    from ui.pages.analysis_robust import _run_moderation as _impl
    _impl(df, _show_cached_result, _save_result)


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


def _show_cached_result(key: str) -> bool:
    """
    若 session_state 中已有该 key 的分析结果，则展示并返回 True，
    否则返回 False（调用方继续渲染运行按钮）。
    """
    result = st.session_state.get("analysis_results", {}).get(key)
    fig    = st.session_state.get("analysis_figures",  {}).get(key)

    if result is None:
        return False

    st.success("✅ " + ("已有分析结果（点击下方按钮重新运行可更新）" if st.session_state.get("lang","zh")=="zh"
                        else "Results available (click the button below to re-run)"))

    df_r = result.get("summary_df") or result.get("stats_df")
    if df_r is not None and not df_r.empty:
        display_result_table(df_r, key)

    if fig is not None:
        try:
            import matplotlib.pyplot as plt
            if plt.fignum_exists(fig.number):
                display_figure(fig, key)
        except Exception as e:
            import logging
            logging.getLogger(__name__).debug("cached figure unavailable: %s", e)

    return True
