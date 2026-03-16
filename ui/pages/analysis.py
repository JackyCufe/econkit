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


def render_analysis() -> None:
    """渲染实证分析页面（步骤3）"""
    if "df" not in st.session_state or st.session_state["df"] is None:
        st.warning(t("analysis.no_data.warning"))
        if st.button(t("analysis.no_data.back"), key="analysis_back_home"):
            st.session_state["step"] = 1
            st.session_state["page"] = "🏠 首页"
            st.rerun()
        return

    df = st.session_state["df"]

    st.markdown(t("analysis.title"))

    # ── 顶部快速操作栏（完成分析 → 生成报告）────────────────────────────────
    top_col1, top_col2 = st.columns([3, 1])
    with top_col1:
        analysis_results = st.session_state.get("analysis_results", {})
        if analysis_results:
            n_done = len(analysis_results)
            st.success(t("analysis.done_count", n=n_done))
        else:
            st.info(t("analysis.tip"))
    with top_col2:
        if st.button(t("analysis.btn.to_report"), type="primary", key="goto_report"):
            # 步骤跳转：步骤3 → 步骤4
            st.session_state["step"] = 4
            st.session_state["page"] = "📄 下载报告"
            st.rerun()

    # ── 推荐路径联动区域 ────────────────────────────────────────────────────────
    recommended = st.session_state.get("recommended_methods", [])
    # 方法名 → 下拉选项 的映射
    _NAME_TO_OPTION: dict[str, str] = {
        "描述统计分析": t("method.descriptive"),
        "OLS 基准回归": t("method.ols"),
        "固定效应模型 (FE)": t("method.panel_fe"),
        "双向固定效应 (TWFE)": t("method.panel_fe"),
        "DID 双重差分": t("method.did"),
        "交错DID (Callaway-Sant'Anna)": t("method.did"),
        "PSM 倾向得分匹配": t("method.psm"),
        "RDD 断点回归": t("method.rdd"),
        "IV / 2SLS 工具变量": t("method.iv"),
        "动态面板 GMM (Arellano-Bond)": t("method.iv"),
        "中介效应分析": t("method.mediation"),
        "调节效应分析": t("method.moderation"),
        "分组回归": t("method.subgroup"),
        "稳健性检验": t("method.bootstrap"),
    }

    all_options = [
        t("group.describe"),
        t("method.descriptive"),
        t("method.correlation"),
        t("method.normality"),
        t("method.vif"),
        t("method.heterosked"),
        t("method.autocorrelation"),
        t("group.baseline"),
        t("method.ols"),
        t("method.panel_fe"),
        t("method.hausman"),
        t("method.unit_root"),
        t("group.causal"),
        t("method.did"),
        t("method.psm"),
        t("method.rdd"),
        t("method.iv"),
        t("method.gmm"),
        t("group.robust"),
        t("method.bootstrap"),
        t("method.exclude_samples"),
        t("group.hetero"),
        t("method.subgroup"),
        t("method.quantile"),
        t("method.mediation"),
        t("method.moderation"),
    ]

    default_index = 0

    if recommended:
        st.info(t("analysis.recommended.info", n=len(recommended)))
        cols = st.columns(min(len(recommended), 4))
        for i, name in enumerate(recommended[:8]):
            option = _NAME_TO_OPTION.get(name)
            if option and option in all_options:
                with cols[i % 4]:
                    if st.button(f"→ {option}", key=f"quick_{i}"):
                        st.session_state["analysis_type"] = option
                        st.rerun()
        st.divider()
        # 默认选中第一个推荐方法
        first_option = _NAME_TO_OPTION.get(recommended[0])
        if first_option and first_option in all_options:
            default_index = all_options.index(first_option)

    # 分析方法选择
    analysis_type = st.selectbox(
        t("analysis.method.select"),
        all_options,
        index=default_index,
        key="analysis_type",
    )

    st.divider()

    # 路由到各分析模块
    _group_labels = {
        t("group.describe"),
        t("group.baseline"),
        t("group.causal"),
        t("group.robust"),
        t("group.hetero"),
    }
    if analysis_type in _group_labels:
        st.info(t("analysis.method.placeholder"))
        return

    router = {
        t("method.descriptive"):      _run_descriptive,
        t("method.correlation"):      _run_correlation,
        t("method.normality"):        _run_normality,
        t("method.vif"):              _run_vif,
        t("method.heterosked"):       _run_heterosked,
        t("method.autocorrelation"):  _run_autocorrelation,
        t("method.ols"):              _run_ols,
        t("method.panel_fe"):         _run_panel_fe,
        t("method.hausman"):          _run_hausman,
        t("method.unit_root"):        _run_unit_root,
        t("method.did"):              _run_did,
        t("method.psm"):              _run_psm,
        t("method.rdd"):              _run_rdd,
        t("method.iv"):               _run_iv,
        t("method.gmm"):              _run_gmm,
        t("method.bootstrap"):        _run_bootstrap,
        t("method.exclude_samples"):  _run_exclude_samples,
        t("method.subgroup"):         _run_subgroup,
        t("method.quantile"):         _run_quantile,
        t("method.mediation"):        _run_mediation,
        t("method.moderation"):       _run_moderation,
    }

    handler = router.get(analysis_type)
    if handler:
        handler(df)
    else:
        st.info(f"「{analysis_type}」正在开发中，敬请期待 🚧")


# ── 描述统计 ──────────────────────────────────────────────────────────────────
def _run_descriptive(df: pd.DataFrame) -> None:
    from analysis.descriptive import compute_descriptive_stats, plot_descriptive_stats

    numeric_cols = df.select_dtypes(include="number").columns.tolist()
    cols = st.multiselect(t("desc.vars.label"), numeric_cols, default=numeric_cols[:6],
                          key="desc_cols")
    if not cols:
        return

    if st.button(t("desc.btn.run"), type="primary"):
        with st.spinner("计算中..."):
            stats_df = compute_descriptive_stats(df, cols)
            display_result_table(stats_df, t("desc.result.title"),
                                 t("desc.result.note"))
            fig = plot_descriptive_stats(df, cols)
            display_figure(fig, t("desc.fig.title"), "distribution.png")
            _save_result("descriptive", {"stats_df": stats_df}, fig)


# ── 相关矩阵 ──────────────────────────────────────────────────────────────────
def _run_correlation(df: pd.DataFrame) -> None:
    from analysis.descriptive import compute_correlation_matrix, plot_correlation_matrix

    numeric_cols = df.select_dtypes(include="number").columns.tolist()
    cols   = st.multiselect(t("corr.vars.label"), numeric_cols, default=numeric_cols[:6],
                            key="corr_cols")
    method = st.radio(t("corr.method.label"), ["pearson", "spearman"], horizontal=True,
                      key="corr_method")
    if not cols:
        return

    if st.button(t("corr.btn.run"), type="primary"):
        with st.spinner("计算中..."):
            corr, pvals = compute_correlation_matrix(df, cols, method)
            display_result_table(corr, t("corr.result.title", method=method.capitalize()),
                                 t("corr.result.note"))
            fig = plot_correlation_matrix(corr, pvals)
            display_figure(fig, t("corr.fig.title"), "correlation.png")


# ── 正态性检验 ────────────────────────────────────────────────────────────────
def _run_normality(df: pd.DataFrame) -> None:
    from analysis.descriptive import test_normality

    numeric_cols = df.select_dtypes(include="number").columns.tolist()
    cols = st.multiselect(t("norm.vars.label"), numeric_cols, default=numeric_cols[:4],
                          key="norm_cols")
    if not cols:
        return

    if st.button(t("norm.btn.run"), type="primary"):
        with st.spinner("检验中..."):
            result_df = test_normality(df, cols)
            display_result_table(result_df, t("norm.result.title"))


# ── VIF ───────────────────────────────────────────────────────────────────────
def _run_vif(df: pd.DataFrame) -> None:
    from analysis.descriptive import compute_vif

    numeric_cols = df.select_dtypes(include="number").columns.tolist()
    cols = st.multiselect(t("vif.vars.label"), numeric_cols,
                          default=numeric_cols[:4], key="vif_cols")
    if len(cols) < 2:
        st.info(t("vif.vars.min"))
        return

    if st.button(t("vif.btn.run"), type="primary"):
        with st.spinner("计算中..."):
            vif_df = compute_vif(df, cols)
            display_result_table(vif_df, t("vif.result.title"),
                                 t("vif.result.note"))


# ── 自相关检验 ────────────────────────────────────────────────────────────────
def _run_autocorrelation(df: pd.DataFrame) -> None:
    from analysis.descriptive import test_autocorrelation

    st.markdown(t("autocorr.title"))
    numeric_cols = df.select_dtypes(include="number").columns.tolist()

    col1, col2 = st.columns(2)
    with col1:
        dep_var    = st.selectbox(t("autocorr.dep.label"), numeric_cols, key="ac_dep")
    with col2:
        indep_vars = st.multiselect(t("autocorr.indep.label"),
                                    [c for c in numeric_cols if c != dep_var],
                                    key="ac_indep")
    if not indep_vars:
        st.info(t("autocorr.indep.min"))
        return

    if st.button(t("autocorr.btn.run"), type="primary"):
        with st.spinner("检验中..."):
            result = test_autocorrelation(df, dep_var, indep_vars)
            display_test_result(result["durbin_watson"], t("autocorr.test.name"), "结论")
            st.info(f"{t('autocorr.recommend.prefix')}{result['recommendation']}")


# ── 异方差检验 ────────────────────────────────────────────────────────────────
def _run_heterosked(df: pd.DataFrame) -> None:
    from analysis.descriptive import test_heteroskedasticity

    numeric_cols = df.select_dtypes(include="number").columns.tolist()
    dep_var   = st.selectbox(t("het.dep.label"), numeric_cols, key="het_dep")
    indep_vars = st.multiselect(t("het.indep.label"),
                                [c for c in numeric_cols if c != dep_var],
                                key="het_indep")
    if not indep_vars:
        return

    if st.button(t("het.btn.run"), type="primary"):
        with st.spinner("检验中..."):
            result = test_heteroskedasticity(df, dep_var, indep_vars)
            st.markdown(t("het.bp.title"))
            display_test_result(result["breusch_pagan"], t("het.bp.name"))
            st.markdown(t("het.white.title"))
            display_test_result(result["white"], t("het.white.name"))
            st.info(f"{t('het.recommend.prefix')}{result['recommendation']}")


# ── 面板单位根检验 ─────────────────────────────────────────────────────────────
def _run_unit_root(df: pd.DataFrame) -> None:
    from analysis.panel_regression import test_panel_unit_root

    st.markdown(t("unit_root.title"))
    numeric_cols = df.select_dtypes(include="number").columns.tolist()
    all_cols     = list(df.columns)

    col1, col2 = st.columns(2)
    with col1:
        test_col = st.selectbox(t("unit_root.col.label"), numeric_cols, key="ur_col")
    with col2:
        id_col   = st.selectbox(t("unit_root.id.label"), all_cols, key="ur_id")
        time_col = st.selectbox(t("unit_root.time.label"), all_cols, key="ur_time")

    if st.button(t("unit_root.btn.run"), type="primary"):
        with st.spinner("检验中..."):
            result = test_panel_unit_root(df, test_col, id_col, time_col)
            if "error" in result:
                st.error(result["error"])
            else:
                display_test_result(result, t("unit_root.result.name"), "结论")
                st.info(f"💡 建议：{result.get('建议', '')}")


# ── OLS 回归 ──────────────────────────────────────────────────────────────────
def _run_ols(df: pd.DataFrame) -> None:
    from analysis.panel_regression import run_ols

    st.markdown(t("ols.title"))
    numeric_cols = df.select_dtypes(include="number").columns.tolist()

    col1, col2 = st.columns(2)
    with col1:
        dep_var = st.selectbox(t("ols.dep.label"), numeric_cols, key="ols_dep")
    with col2:
        cov_options = [t("ols.cov.robust"), t("ols.cov.plain")]
        cov_type = st.selectbox(t("ols.cov.label"), cov_options, key="ols_cov")
    indep_vars = st.multiselect(t("ols.indep.label"),
                                [c for c in numeric_cols if c != dep_var],
                                key="ols_indep")
    if not indep_vars:
        st.info(t("ols.indep.min"))
        return

    if st.button(t("ols.btn.run"), type="primary"):
        with st.spinner("回归中..."):
            # Extract code prefix before （
            cov_code = "HC3" if "HC3" in cov_type else "nonrobust"
            result = run_ols(df, dep_var, indep_vars, cov_code)
            display_regression_summary(result)
            _save_result("ols", result, None)


# ── 面板固定效应 ──────────────────────────────────────────────────────────────
def _run_panel_fe(df: pd.DataFrame) -> None:
    from analysis.panel_regression import run_panel_model

    st.markdown(t("panel.title"))
    vars_config = select_panel_variables(df, "panel")

    if not vars_config["indep_vars"]:
        st.info(t("panel.indep.min"))
        return

    if st.button(t("panel.btn.run"), type="primary"):
        with st.spinner("回归中..."):
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

    st.markdown(t("hausman.title"))
    numeric_cols = df.select_dtypes(include="number").columns.tolist()
    all_cols     = list(df.columns)

    col1, col2 = st.columns(2)
    with col1:
        id_col   = st.selectbox(t("hausman.id.label"), all_cols, key="hm_id")
        dep_var  = st.selectbox(t("hausman.dep.label"), numeric_cols, key="hm_dep")
    with col2:
        time_col = st.selectbox(t("hausman.time.label"), all_cols, key="hm_time")
        indep_vars = st.multiselect(t("hausman.indep.label"),
                                    [c for c in numeric_cols if c != dep_var],
                                    key="hm_indep")

    if not indep_vars:
        return

    if st.button(t("hausman.btn.run"), type="primary"):
        with st.spinner("检验中..."):
            result = run_hausman_test(df, dep_var, indep_vars, id_col, time_col)
            if "error" in result:
                st.error(result["error"])
            else:
                display_test_result(result, t("hausman.result.name"), "结论")


# ── DID ───────────────────────────────────────────────────────────────────────
def _run_did(df: pd.DataFrame) -> None:
    from analysis.causal_did import (
        run_basic_did, run_twfe_did,
        run_parallel_trend_test, run_placebo_test,
    )

    st.markdown(t("did.title"))
    vars_config = select_did_variables(df, "did")

    sub_analyses = st.multiselect(
        t("did.steps.label"),
        [t("did.step.basic"), t("did.step.twfe"), t("did.step.parallel"), t("did.step.placebo")],
        default=[t("did.step.basic"), t("did.step.parallel"), t("did.step.placebo")],
        key="did_steps",
    )

    n_sim = st.slider(t("did.nsim.label"), 100, 2000, 1000, 100,
                      key="did_nsim") if t("did.step.placebo") in sub_analyses else 1000

    if st.button(t("did.btn.run"), type="primary"):
        with st.spinner(t("did.running")):
            basic_result = None
            if t("did.step.basic") in sub_analyses:
                st.markdown(t("did.basic.title"))
                basic_result = run_basic_did(
                    df,
                    dep_var   = vars_config["dep_var"],
                    treat_col = vars_config["treat_col"],
                    post_col  = vars_config["post_col"],
                    did_col   = vars_config["did_col"],
                    controls  = vars_config["controls"] or None,
                )
                display_did_summary(basic_result, t("did.display.basic"))

            if t("did.step.twfe") in sub_analyses:
                st.markdown(t("did.twfe.title"))
                twfe_result = run_twfe_did(
                    df,
                    dep_var   = vars_config["dep_var"],
                    did_col   = vars_config["did_col"],
                    id_col    = vars_config["id_col"],
                    time_col  = vars_config["time_col"],
                    controls  = vars_config["controls"] or None,
                )
                display_did_summary(twfe_result, t("did.display.twfe"))

            if t("did.step.parallel") in sub_analyses:
                st.markdown(t("did.parallel.title"))
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
                    display_figure(pt_fig, t("did.parallel.fig.title"), "parallel_trend.png")
                    st.info(pt_result.get("conclusion", ""))
                else:
                    st.error(t("did.parallel.error", error=pt_result["error"]))

            if t("did.step.placebo") in sub_analyses:
                st.markdown(t("did.placebo.title"))
                real_coef = basic_result["did_coef"] if basic_result else None
                _pbar = st.progress(0, text=t("did.placebo.progress", done=0, n=n_sim))
                def _placebo_cb(pct: float) -> None:
                    _pbar.progress(pct, text=t("did.placebo.progress", done=int(pct*n_sim), n=n_sim))
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
                display_figure(pl_fig, t("did.placebo.fig.title", n=n_sim), "placebo_test.png")
                st.info(pl_result.get("conclusion", ""))


# ── PSM ───────────────────────────────────────────────────────────────────────
def _run_psm(df: pd.DataFrame) -> None:
    from analysis.causal_psm import (
        estimate_propensity_score, knn_matching,
        kernel_matching, check_covariate_balance, plot_psm_distributions,
    )

    st.markdown(t("psm.title"))
    all_cols     = list(df.columns)
    numeric_cols = df.select_dtypes(include="number").columns.tolist()

    col1, col2 = st.columns(2)
    with col1:
        treat_col = st.selectbox(t("psm.treat.label"), all_cols,
                                 index=next((i for i, c in enumerate(all_cols)
                                             if "treat" in c.lower()), 0),
                                 key="psm_treat")
        dep_var = st.selectbox(t("psm.dep.label"), numeric_cols, key="psm_dep")
    with col2:
        covariates = st.multiselect(t("psm.covs.label"),
                                    [c for c in numeric_cols if c != dep_var],
                                    key="psm_covs")
        method = st.radio(t("psm.method.label"),
                          [t("psm.method.knn"), t("psm.method.kernel")],
                          horizontal=True, key="psm_method")

    k = st.slider(t("psm.k.label"), 1, 5, 1, key="psm_k") if "KNN" in method or "Nearest" in method else 1

    if not covariates:
        st.info(t("psm.covs.min"))
        return

    if st.button(t("psm.btn.run"), type="primary"):
        with st.spinner(t("psm.matching")):
            ps_df = estimate_propensity_score(df, treat_col, covariates)
            fig_dist = plot_psm_distributions(ps_df, treat_col)
            display_figure(fig_dist, t("psm.dist.fig.title"), "psm_distribution.png")

            if "KNN" in method or "Nearest" in method:
                result = knn_matching(ps_df, df[dep_var].reset_index(drop=True),
                                      treat_col, k=k)
            else:
                result = kernel_matching(ps_df, df[dep_var].reset_index(drop=True),
                                         treat_col)

            st.markdown(t("psm.att.title", method=result["method"]))
            col_a, col_b, col_c = st.columns(3)
            col_a.metric(t("psm.att.label"), f"{result['att']}{result['stars']}")
            col_b.metric(t("psm.se.label"), str(result["att_se"]))
            col_c.metric(t("psm.pval.label"), str(result["p_value"]))


# ── RDD ───────────────────────────────────────────────────────────────────────
def _run_rdd(df: pd.DataFrame) -> None:
    from analysis.causal_rdd import (
        run_rdd_local_linear, select_optimal_bandwidth,
        mccrary_density_test, plot_rdd,
    )

    st.markdown(t("rdd.title"))
    numeric_cols = df.select_dtypes(include="number").columns.tolist()

    col1, col2 = st.columns(2)
    with col1:
        dep_var     = st.selectbox(t("rdd.dep.label"), numeric_cols, key="rdd_dep")
        running_var = st.selectbox(t("rdd.run.label"), numeric_cols, key="rdd_run")
    with col2:
        cutoff    = st.number_input(t("rdd.cutoff.label"), value=60.0, key="rdd_cutoff")
        bw        = st.number_input(t("rdd.bw.label"), value=0.0, step=0.1, key="rdd_bw")
        poly      = st.radio(t("rdd.poly.label"), [1, 2], horizontal=True, key="rdd_poly")

    bandwidth = bw if bw > 0 else None

    if st.button(t("rdd.btn.run"), type="primary"):
        with st.spinner(t("rdd.analyzing")):
            # RDD 可视化
            fig = plot_rdd(df, dep_var, running_var, cutoff, bandwidth)
            display_figure(fig, t("rdd.fig.title"), "rdd_plot.png")

            # 最优带宽
            if bandwidth is None:
                bw_result = select_optimal_bandwidth(df, dep_var, running_var, cutoff)
                bandwidth = bw_result["optimal_bandwidth"]
                st.info(t("rdd.bw.info", bw=bandwidth))
                if not bw_result["sensitivity_table"].empty:
                    display_result_table(bw_result["sensitivity_table"],
                                         t("rdd.bw.sens.title"))

            # 局部线性回归
            result = run_rdd_local_linear(df, dep_var, running_var, cutoff,
                                           bandwidth, poly)
            if "error" in result:
                st.error(result["error"])
            else:
                col_a, col_b, col_c, col_d = st.columns(4)
                col_a.metric(t("rdd.coef.label"), f"{result['coef']}{result['stars']}")
                col_b.metric(t("rdd.se.label"), str(result["se"]))
                col_c.metric(t("rdd.pval.label"), str(result["pval"]))
                col_d.metric(t("rdd.n.label"), str(result["n_obs"]))

            # McCrary 密度检验
            st.markdown(t("rdd.density.title"))
            density_result, density_fig = mccrary_density_test(df, running_var, cutoff)
            display_figure(density_fig, t("rdd.density.fig.title"), "mccrary.png")
            display_test_result(density_result, t("rdd.density.result.title"))


# ── IV/2SLS ───────────────────────────────────────────────────────────────────
def _run_iv(df: pd.DataFrame) -> None:
    from analysis.causal_iv import run_iv_2sls

    st.markdown(t("iv.title"))
    numeric_cols = df.select_dtypes(include="number").columns.tolist()

    col1, col2 = st.columns(2)
    with col1:
        dep_var   = st.selectbox(t("iv.dep.label"), numeric_cols, key="iv_dep")
        endog_var = st.selectbox(t("iv.endog.label"),
                                 [c for c in numeric_cols if c != dep_var],
                                 key="iv_endog")
    with col2:
        instruments = st.multiselect(
            t("iv.instruments.label"),
            [c for c in numeric_cols if c not in [dep_var, endog_var]],
            key="iv_instruments",
        )

    controls = st.multiselect(
        t("iv.controls.label"),
        [c for c in numeric_cols if c not in [dep_var, endog_var] + instruments],
        key="iv_controls",
    )

    if not instruments:
        st.info(t("iv.instruments.min"))
        return

    if st.button(t("iv.btn.run"), type="primary"):
        with st.spinner(t("iv.estimating")):
            result = run_iv_2sls(df, dep_var, endog_var, instruments,
                                  controls or None)
            if "error" in result:
                st.error(result["error"])
                return

            col_a, col_b, col_c = st.columns(3)
            col_a.metric(t("iv.coef.label"), f"{result['coef']}{result['stars']}")
            col_b.metric(t("iv.se.label"), str(result["se"]))
            weak_note = " ✅" if result["weak_iv_pass"] else f" {t('iv.weak_iv')}"
            col_c.metric(t("iv.f.label"), f"{result['first_stage_f']:.2f}{weak_note}")

            display_test_result(result["wu_hausman"], t("iv.wu_hausman.name"), "结论")
            if "p值" in result.get("sargan", {}):
                display_test_result(result["sargan"], t("iv.sargan.name"), "结论")


# ── 动态面板 GMM ───────────────────────────────────────────────────────────────
def _run_gmm(df: pd.DataFrame) -> None:
    from analysis.panel_regression import run_dynamic_panel_gmm

    st.markdown(t("gmm.title"))
    numeric_cols = df.select_dtypes(include="number").columns.tolist()
    all_cols     = list(df.columns)

    col1, col2 = st.columns(2)
    with col1:
        dep_var  = st.selectbox(t("gmm.dep.label"), numeric_cols, key="gmm_dep")
        id_col   = st.selectbox(t("gmm.id.label"), all_cols, key="gmm_id")
    with col2:
        indep_vars = st.multiselect(
            t("gmm.indep.label"),
            [c for c in numeric_cols if c != dep_var],
            key="gmm_indep",
        )
        time_col = st.selectbox(t("gmm.time.label"), all_cols, key="gmm_time")

    gmm_type = st.radio(
        t("gmm.type.label"),
        [t("gmm.type.diff"), t("gmm.type.sys")],
        horizontal=True, key="gmm_type",
    )
    st.info(t("gmm.info"))

    if not indep_vars:
        st.info(t("gmm.indep.min"))
        return

    if st.button(t("gmm.btn.run"), type="primary"):
        with st.spinner(t("gmm.running")):
            # Extract type code: "difference" or "system"
            gmm_code = "difference" if "difference" in gmm_type or "差分" in gmm_type else "system"
            result = run_dynamic_panel_gmm(
                df, dep_var, indep_vars, id_col, time_col,
                gmm_type=gmm_code,
            )
            if "error" in result:
                st.error(f"❌ {result['error']}")
            else:
                display_regression_summary(result)

                # AR 序列相关检验
                if result.get("ar_tests"):
                    st.markdown(t("gmm.ar.title"))
                    ar_df = pd.DataFrame(result["ar_tests"])
                    st.dataframe(ar_df, use_container_width=True)
                    st.caption(t("gmm.ar.caption"))

                # Hansen 过度识别检验
                if result.get("hansen"):
                    st.markdown(t("gmm.hansen.title"))
                    h = result["hansen"]
                    col_a, col_b, col_c = st.columns(3)
                    col_a.metric(t("gmm.hansen.chi2.label"), str(h["chi2统计量"]))
                    col_b.metric(t("gmm.hansen.df.label"), str(h["自由度"]))
                    col_c.metric(t("gmm.hansen.pval.label"), str(h["p值"]))
                    st.info(h["结论"])

                if result.get("ar_note"):
                    st.success(result["ar_note"])
                _save_result("gmm", result)


# ── Bootstrap ─────────────────────────────────────────────────────────────────
def _run_bootstrap(df: pd.DataFrame) -> None:
    from analysis.robustness import bootstrap_confidence_interval

    st.markdown(t("boot.title"))
    numeric_cols = df.select_dtypes(include="number").columns.tolist()

    col1, col2 = st.columns(2)
    with col1:
        dep_var  = st.selectbox(t("boot.dep.label"), numeric_cols, key="boot_dep")
        key_var  = st.selectbox(t("boot.key.label"),
                                [c for c in numeric_cols if c != dep_var],
                                key="boot_key")
    with col2:
        n_boot = st.slider(t("boot.n.label"), 200, 2000, 1000, 100, key="boot_n")
        indep_vars = st.multiselect(t("boot.indep.label"),
                                    [c for c in numeric_cols if c != dep_var],
                                    key="boot_indep")

    if not indep_vars:
        return

    if st.button(t("boot.btn.run"), type="primary"):
        _pbar = st.progress(0, text=t("boot.progress", done=0, n=n_boot))
        def _boot_cb(pct: float) -> None:
            _pbar.progress(pct, text=t("boot.progress", done=int(pct*n_boot), n=n_boot))
        result, fig = bootstrap_confidence_interval(
            df, dep_var, indep_vars, key_var, n_boot,
            progress_callback=_boot_cb,
        )
        _pbar.empty()
        display_figure(fig, t("boot.fig.title"), "bootstrap.png")
        st.info(result.get("conclusion", ""))
        _save_result("bootstrap", result, fig)


# ── 剔除特殊样本 ──────────────────────────────────────────────────────────────
def _run_exclude_samples(df: pd.DataFrame) -> None:
    from analysis.robustness import exclude_special_samples

    st.markdown(t("excl.title"))
    numeric_cols = df.select_dtypes(include="number").columns.tolist()

    dep_var    = st.selectbox(t("excl.dep.label"), numeric_cols, key="excl_dep")
    key_var    = st.selectbox(t("excl.key.label"),
                              [c for c in numeric_cols if c != dep_var],
                              key="excl_key")
    indep_vars = st.multiselect(t("excl.indep.label"),
                                [c for c in numeric_cols if c != dep_var],
                                key="excl_indep")

    st.markdown(t("excl.conditions.title"))
    n_conditions = st.number_input(t("excl.n_conditions.label"), 1, 5, 2, key="excl_n")
    conditions = []
    for i in range(int(n_conditions)):
        col_a, col_b = st.columns([1, 2])
        with col_a:
            label = st.text_input(
                t("excl.condition.label_prefix", i=i+1),
                t("excl.condition.default_label", i=i+1),
                key=f"excl_label_{i}",
            )
        with col_b:
            query = st.text_input(
                t("excl.condition.query_label"),
                "",
                key=f"excl_query_{i}",
            )
        if query:
            conditions.append({"label": label, "query": query})

    if not indep_vars or not conditions:
        return

    if st.button(t("excl.btn.run"), type="primary"):
        with st.spinner(t("excl.running")):
            result_df = exclude_special_samples(df, dep_var, indep_vars,
                                                key_var, conditions)
            display_result_table(result_df, t("excl.result.title"))


# ── 分组回归 ──────────────────────────────────────────────────────────────────
def _run_subgroup(df: pd.DataFrame) -> None:
    from analysis.heterogeneity import run_subgroup_regression

    st.markdown(t("subgroup.title"))
    numeric_cols = df.select_dtypes(include="number").columns.tolist()
    all_cols     = list(df.columns)

    col1, col2 = st.columns(2)
    with col1:
        dep_var   = st.selectbox(t("subgroup.dep.label"), numeric_cols, key="sub_dep")
        key_var   = st.selectbox(t("subgroup.key.label"),
                                 [c for c in numeric_cols if c != dep_var],
                                 key="sub_key")
    with col2:
        group_col  = st.selectbox(t("subgroup.group.label"), all_cols, key="sub_group")
        indep_vars = st.multiselect(t("subgroup.indep.label"),
                                    [c for c in numeric_cols if c != dep_var],
                                    key="sub_indep")

    if not indep_vars:
        return

    if st.button(t("subgroup.btn.run"), type="primary"):
        with st.spinner(t("subgroup.running")):
            result_df, fig = run_subgroup_regression(
                df, dep_var, indep_vars, key_var, group_col
            )
            display_figure(fig, t("subgroup.fig.title"), "subgroup.png")
            display_result_table(result_df, t("subgroup.result.title"))


# ── 分位数回归 ────────────────────────────────────────────────────────────────
def _run_quantile(df: pd.DataFrame) -> None:
    from analysis.heterogeneity import run_quantile_regression

    st.markdown(t("quantile.title"))
    numeric_cols = df.select_dtypes(include="number").columns.tolist()

    dep_var    = st.selectbox(t("quantile.dep.label"), numeric_cols, key="qr_dep")
    key_var    = st.selectbox(t("quantile.key.label"),
                              [c for c in numeric_cols if c != dep_var],
                              key="qr_key")
    indep_vars = st.multiselect(t("quantile.indep.label"),
                                [c for c in numeric_cols if c != dep_var],
                                key="qr_indep")

    if not indep_vars or key_var not in indep_vars:
        st.info(t("quantile.indep.min"))
        return

    if st.button(t("quantile.btn.run"), type="primary"):
        with st.spinner(t("quantile.running")):
            result_df, fig = run_quantile_regression(df, dep_var, indep_vars, key_var)
            display_figure(fig, t("quantile.fig.title"), "quantile_reg.png")
            display_result_table(result_df, t("quantile.result.title"))


# ── 中介效应 ──────────────────────────────────────────────────────────────────
def _run_mediation(df: pd.DataFrame) -> None:
    from analysis.heterogeneity import run_mediation_analysis

    st.markdown(t("mediation.title"))
    numeric_cols = df.select_dtypes(include="number").columns.tolist()

    col1, col2, col3 = st.columns(3)
    with col1:
        treatment = st.selectbox(t("mediation.x.label"), numeric_cols, key="med_x")
    with col2:
        mediator  = st.selectbox(t("mediation.m.label"),
                                 [c for c in numeric_cols if c != treatment],
                                 key="med_m")
    with col3:
        dep_var   = st.selectbox(t("mediation.y.label"),
                                 [c for c in numeric_cols
                                  if c not in [treatment, mediator]],
                                 key="med_y")

    controls = st.multiselect(t("mediation.controls.label"),
                              [c for c in numeric_cols
                               if c not in [treatment, mediator, dep_var]],
                              key="med_controls")
    n_boot   = st.slider(t("mediation.boot.label"), 200, 2000, 1000, 100, key="med_boot")

    if st.button(t("mediation.btn.run"), type="primary"):
        _pbar = st.progress(0, text=t("mediation.progress", done=0, n=n_boot))
        def _med_cb(pct: float) -> None:
            _pbar.progress(pct, text=t("mediation.progress", done=int(pct*n_boot), n=n_boot))
        result, fig = run_mediation_analysis(
            df, dep_var, mediator, treatment, controls or None, n_boot,
            progress_callback=_med_cb,
        )
        _pbar.empty()
        display_figure(fig, t("mediation.fig.title"), "mediation.png")
        col_a, col_b, col_c = st.columns(3)
        col_a.metric(t("mediation.indirect.label"), str(result["indirect_effect"]))
        col_b.metric(t("mediation.direct.label"), str(result["direct_effect"]))
        col_c.metric(t("mediation.pct.label"), f"{result['pct_mediated']}%")
        st.info(result.get("conclusion", ""))
        _save_result("mediation", result, fig)


# ── 调节效应 ──────────────────────────────────────────────────────────────────
def _run_moderation(df: pd.DataFrame) -> None:
    from analysis.heterogeneity import run_moderation_analysis

    st.markdown(t("moderation.title"))
    numeric_cols = df.select_dtypes(include="number").columns.tolist()

    col1, col2, col3 = st.columns(3)
    with col1:
        treatment = st.selectbox(t("moderation.x.label"), numeric_cols, key="mod_x")
    with col2:
        moderator = st.selectbox(t("moderation.m.label"),
                                 [c for c in numeric_cols if c != treatment],
                                 key="mod_m")
    with col3:
        dep_var   = st.selectbox(t("moderation.y.label"),
                                 [c for c in numeric_cols
                                  if c not in [treatment, moderator]],
                                 key="mod_y")

    controls = st.multiselect(t("moderation.controls.label"),
                              [c for c in numeric_cols
                               if c not in [treatment, moderator, dep_var]],
                              key="mod_controls")

    if st.button(t("moderation.btn.run"), type="primary"):
        with st.spinner(t("moderation.analyzing")):
            result, fig = run_moderation_analysis(
                df, dep_var, treatment, moderator, controls or None
            )
            display_figure(fig, t("moderation.fig.title"), "moderation.png")
            col_a, col_b, col_c = st.columns(3)
            col_a.metric(t("moderation.coef.label"), f"{result['interaction_coef']}{result['stars']}")
            col_b.metric(t("moderation.se.label"), str(result["interaction_se"]))
            col_c.metric(t("moderation.pval.label"), str(result["interaction_pval"]))
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
