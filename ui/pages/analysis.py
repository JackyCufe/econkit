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


def render_analysis() -> None:
    """渲染实证分析页面（步骤3）"""
    if "df" not in st.session_state or st.session_state["df"] is None:
        st.warning("⚠️ 请先在首页上传数据")
        if st.button("← 返回上传数据", key="analysis_back_home"):
            st.session_state["step"] = 1
            st.session_state["page"] = "🏠 首页"
            st.rerun()
        return

    df = st.session_state["df"]

    st.markdown("## 📈 步骤3：实证分析")

    # ── 顶部快速操作栏（完成分析 → 生成报告）────────────────────────────────
    top_col1, top_col2 = st.columns([3, 1])
    with top_col1:
        analysis_results = st.session_state.get("analysis_results", {})
        if analysis_results:
            n_done = len(analysis_results)
            st.success(f"✅ 已完成 {n_done} 项分析")
        else:
            st.info("💡 选择下方分析方法并运行，完成后点击右侧按钮生成报告")
    with top_col2:
        if st.button("📄 完成分析，生成报告 →", type="primary", key="goto_report"):
            # 步骤跳转：步骤3 → 步骤4
            st.session_state["step"] = 4
            st.session_state["page"] = "📄 下载报告"
            st.rerun()

    # ── 推荐路径联动区域 ────────────────────────────────────────────────────────
    recommended = st.session_state.get("recommended_methods", [])
    # 方法名 → 下拉选项 的映射
    _NAME_TO_OPTION: dict[str, str] = {
        "描述统计分析": "描述统计",
        "OLS 基准回归": "OLS 回归",
        "固定效应模型 (FE)": "面板固定效应（FE/RE/TWFE）",
        "双向固定效应 (TWFE)": "面板固定效应（FE/RE/TWFE）",
        "DID 双重差分": "DID 双重差分",
        "交错DID (Callaway-Sant'Anna)": "DID 双重差分",
        "PSM 倾向得分匹配": "PSM 倾向得分匹配",
        "RDD 断点回归": "RDD 断点回归",
        "IV / 2SLS 工具变量": "IV / 2SLS",
        "动态面板 GMM (Arellano-Bond)": "IV / 2SLS",
        "中介效应分析": "中介效应",
        "调节效应分析": "调节效应",
        "分组回归": "分组回归",
        "稳健性检验": "Bootstrap 置信区间",
    }

    default_index = 0
    all_options = [
        "── 🔵 描述与诊断 ──",
        "描述统计",
        "相关矩阵",
        "正态性检验",
        "VIF 多重共线性",
        "异方差检验",
        "── 🟡 基准回归 ──",
        "OLS 回归",
        "面板固定效应（FE/RE/TWFE）",
        "Hausman 检验",
        "── 🔴 因果推断 ──",
        "DID 双重差分",
        "PSM 倾向得分匹配",
        "RDD 断点回归",
        "IV / 2SLS",
        "── 🟢 稳健性检验 ──",
        "Bootstrap 置信区间",
        "剔除特殊样本",
        "── 🟣 异质性与机制 ──",
        "分组回归",
        "分位数回归",
        "中介效应",
        "调节效应",
    ]

    if recommended:
        st.info(f"🎯 智能引导为你推荐了 **{len(recommended)}** 个分析方法，点击快速跳转：")
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
        "🔬 选择分析方法",
        all_options,
        index=default_index,
        key="analysis_type",
    )

    st.divider()

    # 路由到各分析模块
    if "──" in analysis_type:
        st.info("👆 请从下拉菜单选择具体分析方法")
        return

    router = {
        "描述统计":               _run_descriptive,
        "相关矩阵":               _run_correlation,
        "正态性检验":             _run_normality,
        "VIF 多重共线性":         _run_vif,
        "异方差检验":             _run_heterosked,
        "OLS 回归":               _run_ols,
        "面板固定效应（FE/RE/TWFE）": _run_panel_fe,
        "Hausman 检验":           _run_hausman,
        "DID 双重差分":           _run_did,
        "PSM 倾向得分匹配":       _run_psm,
        "RDD 断点回归":           _run_rdd,
        "IV / 2SLS":              _run_iv,
        "Bootstrap 置信区间":     _run_bootstrap,
        "剔除特殊样本":           _run_exclude_samples,
        "分组回归":               _run_subgroup,
        "分位数回归":             _run_quantile,
        "中介效应":               _run_mediation,
        "调节效应":               _run_moderation,
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
    cols = st.multiselect("选择分析变量", numeric_cols, default=numeric_cols[:6],
                          key="desc_cols")
    if not cols:
        return

    if st.button("▶ 运行描述统计", type="primary"):
        with st.spinner("计算中..."):
            stats_df = compute_descriptive_stats(df, cols)
            display_result_table(stats_df, "描述统计结果",
                                 "均值/标准差/分位数/偏度/峰度")
            fig = plot_descriptive_stats(df, cols)
            display_figure(fig, "变量分布图", "distribution.png")
            _save_result("descriptive", {"stats_df": stats_df})


# ── 相关矩阵 ──────────────────────────────────────────────────────────────────
def _run_correlation(df: pd.DataFrame) -> None:
    from analysis.descriptive import compute_correlation_matrix, plot_correlation_matrix

    numeric_cols = df.select_dtypes(include="number").columns.tolist()
    cols   = st.multiselect("选择变量", numeric_cols, default=numeric_cols[:6],
                            key="corr_cols")
    method = st.radio("相关系数方法", ["pearson", "spearman"], horizontal=True,
                      key="corr_method")
    if not cols:
        return

    if st.button("▶ 运行相关矩阵", type="primary"):
        with st.spinner("计算中..."):
            corr, pvals = compute_correlation_matrix(df, cols, method)
            display_result_table(corr, f"{method.capitalize()} 相关矩阵",
                                 "下三角为相关系数，***p<0.01，**p<0.05，*p<0.1")
            fig = plot_correlation_matrix(corr, pvals)
            display_figure(fig, "相关矩阵热力图", "correlation.png")


# ── 正态性检验 ────────────────────────────────────────────────────────────────
def _run_normality(df: pd.DataFrame) -> None:
    from analysis.descriptive import test_normality

    numeric_cols = df.select_dtypes(include="number").columns.tolist()
    cols = st.multiselect("选择检验变量", numeric_cols, default=numeric_cols[:4],
                          key="norm_cols")
    if not cols:
        return

    if st.button("▶ 运行正态性检验", type="primary"):
        with st.spinner("检验中..."):
            result_df = test_normality(df, cols)
            display_result_table(result_df, "正态性检验结果（Shapiro-Wilk / Jarque-Bera）")


# ── VIF ───────────────────────────────────────────────────────────────────────
def _run_vif(df: pd.DataFrame) -> None:
    from analysis.descriptive import compute_vif

    numeric_cols = df.select_dtypes(include="number").columns.tolist()
    cols = st.multiselect("选择变量（将计算两两VIF）", numeric_cols,
                          default=numeric_cols[:4], key="vif_cols")
    if len(cols) < 2:
        st.info("请至少选择 2 个变量")
        return

    if st.button("▶ 计算 VIF", type="primary"):
        with st.spinner("计算中..."):
            vif_df = compute_vif(df, cols)
            display_result_table(vif_df, "VIF 多重共线性检验",
                                 "VIF>10 严重共线性，VIF>5 中度共线性")


# ── 异方差检验 ────────────────────────────────────────────────────────────────
def _run_heterosked(df: pd.DataFrame) -> None:
    from analysis.descriptive import test_heteroskedasticity

    numeric_cols = df.select_dtypes(include="number").columns.tolist()
    dep_var   = st.selectbox("被解释变量", numeric_cols, key="het_dep")
    indep_vars = st.multiselect("解释变量", [c for c in numeric_cols if c != dep_var],
                                key="het_indep")
    if not indep_vars:
        return

    if st.button("▶ 运行异方差检验", type="primary"):
        with st.spinner("检验中..."):
            result = test_heteroskedasticity(df, dep_var, indep_vars)
            st.markdown("**Breusch-Pagan 检验**")
            display_test_result(result["breusch_pagan"], "BP 检验")
            st.markdown("**White 检验**")
            display_test_result(result["white"], "White 检验")
            st.info(f"💡 建议：{result['recommendation']}")


# ── OLS 回归 ──────────────────────────────────────────────────────────────────
def _run_ols(df: pd.DataFrame) -> None:
    from analysis.panel_regression import run_ols

    st.markdown("### OLS 普通最小二乘回归")
    numeric_cols = df.select_dtypes(include="number").columns.tolist()

    col1, col2 = st.columns(2)
    with col1:
        dep_var = st.selectbox("被解释变量（Y）", numeric_cols, key="ols_dep")
    with col2:
        cov_type = st.selectbox("标准误类型", ["HC3（稳健）", "nonrobust（普通）"],
                                key="ols_cov")
    indep_vars = st.multiselect("解释变量（X）",
                                [c for c in numeric_cols if c != dep_var],
                                key="ols_indep")
    if not indep_vars:
        st.info("请选择至少一个解释变量")
        return

    if st.button("▶ 运行 OLS 回归", type="primary"):
        with st.spinner("回归中..."):
            result = run_ols(df, dep_var, indep_vars,
                             cov_type.split("（")[0])
            display_regression_summary(result)
            _save_result("ols", result)


# ── 面板固定效应 ──────────────────────────────────────────────────────────────
def _run_panel_fe(df: pd.DataFrame) -> None:
    from analysis.panel_regression import run_panel_model

    st.markdown("### 面板固定/随机效应回归")
    vars_config = select_panel_variables(df, "panel")

    if not vars_config["indep_vars"]:
        st.info("请选择至少一个解释变量")
        return

    if st.button("▶ 运行面板模型", type="primary"):
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

    st.markdown("### Hausman 检验（FE vs RE）")
    numeric_cols = df.select_dtypes(include="number").columns.tolist()
    all_cols     = list(df.columns)

    col1, col2 = st.columns(2)
    with col1:
        id_col   = st.selectbox("个体变量", all_cols, key="hm_id")
        dep_var  = st.selectbox("被解释变量", numeric_cols, key="hm_dep")
    with col2:
        time_col = st.selectbox("时间变量", all_cols, key="hm_time")
        indep_vars = st.multiselect("解释变量", [c for c in numeric_cols if c != dep_var],
                                    key="hm_indep")

    if not indep_vars:
        return

    if st.button("▶ 运行 Hausman 检验", type="primary"):
        with st.spinner("检验中..."):
            result = run_hausman_test(df, dep_var, indep_vars, id_col, time_col)
            if "error" in result:
                st.error(result["error"])
            else:
                display_test_result(result, "Hausman 检验（FE vs RE）", "结论")


# ── DID ───────────────────────────────────────────────────────────────────────
def _run_did(df: pd.DataFrame) -> None:
    from analysis.causal_did import (
        run_basic_did, run_twfe_did,
        run_parallel_trend_test, run_placebo_test,
    )

    st.markdown("### DID 双重差分分析")
    vars_config = select_did_variables(df, "did")

    sub_analyses = st.multiselect(
        "选择分析步骤",
        ["基准 DID（OLS）", "双向固定效应 DID", "平行趋势检验", "安慰剂检验"],
        default=["基准 DID（OLS）", "平行趋势检验", "安慰剂检验"],
        key="did_steps",
    )

    n_sim = st.slider("安慰剂检验模拟次数", 100, 2000, 1000, 100,
                      key="did_nsim") if "安慰剂检验" in sub_analyses else 1000

    if st.button("▶ 运行 DID 分析", type="primary"):
        with st.spinner("分析中（可能需要 1-3 分钟）..."):
            basic_result = None
            if "基准 DID（OLS）" in sub_analyses:
                st.markdown("#### 基准 DID")
                basic_result = run_basic_did(
                    df,
                    dep_var   = vars_config["dep_var"],
                    treat_col = vars_config["treat_col"],
                    post_col  = vars_config["post_col"],
                    did_col   = vars_config["did_col"],
                    controls  = vars_config["controls"] or None,
                )
                display_did_summary(basic_result, "基准 DID（OLS + 稳健SE）")

            if "双向固定效应 DID" in sub_analyses:
                st.markdown("#### 双向固定效应 DID")
                twfe_result = run_twfe_did(
                    df,
                    dep_var   = vars_config["dep_var"],
                    did_col   = vars_config["did_col"],
                    id_col    = vars_config["id_col"],
                    time_col  = vars_config["time_col"],
                    controls  = vars_config["controls"] or None,
                )
                display_did_summary(twfe_result, "TWFE DID（个体+时间双向FE）")

            if "平行趋势检验" in sub_analyses:
                st.markdown("#### 平行趋势检验（事件研究法）")
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
                    display_figure(pt_fig, "平行趋势检验图", "parallel_trend.png")
                    st.info(pt_result.get("conclusion", ""))
                else:
                    st.error(f"平行趋势检验失败：{pt_result['error']}")

            if "安慰剂检验" in sub_analyses:
                st.markdown("#### 安慰剂检验（随机置换处理组）")
                real_coef = basic_result["did_coef"] if basic_result else None
                pl_result, pl_fig = run_placebo_test(
                    df,
                    dep_var    = vars_config["dep_var"],
                    treat_col  = vars_config["treat_col"],
                    post_col   = vars_config["post_col"],
                    controls   = vars_config["controls"] or None,
                    n_sim      = n_sim,
                    real_coef  = real_coef,
                )
                display_figure(pl_fig, f"安慰剂检验（{n_sim}次置换）", "placebo_test.png")
                st.info(pl_result.get("conclusion", ""))


# ── PSM ───────────────────────────────────────────────────────────────────────
def _run_psm(df: pd.DataFrame) -> None:
    from analysis.causal_psm import (
        estimate_propensity_score, knn_matching,
        kernel_matching, check_covariate_balance, plot_psm_distributions,
    )

    st.markdown("### PSM 倾向得分匹配")
    all_cols     = list(df.columns)
    numeric_cols = df.select_dtypes(include="number").columns.tolist()

    col1, col2 = st.columns(2)
    with col1:
        treat_col = st.selectbox("处理组变量（0/1）", all_cols,
                                 index=next((i for i, c in enumerate(all_cols)
                                             if "treat" in c.lower()), 0),
                                 key="psm_treat")
        dep_var = st.selectbox("结果变量（Y）", numeric_cols, key="psm_dep")
    with col2:
        covariates = st.multiselect("匹配协变量",
                                    [c for c in numeric_cols if c != dep_var],
                                    key="psm_covs")
        method = st.radio("匹配方法", ["KNN（最近邻）", "核匹配"],
                          horizontal=True, key="psm_method")

    k = st.slider("KNN 近邻数", 1, 5, 1, key="psm_k") if "KNN" in method else 1

    if not covariates:
        st.info("请选择匹配协变量")
        return

    if st.button("▶ 运行 PSM 匹配", type="primary"):
        with st.spinner("匹配中..."):
            ps_df = estimate_propensity_score(df, treat_col, covariates)
            fig_dist = plot_psm_distributions(ps_df, treat_col)
            display_figure(fig_dist, "倾向得分分布图", "psm_distribution.png")

            if "KNN" in method:
                result = knn_matching(ps_df, df[dep_var].reset_index(drop=True),
                                      treat_col, k=k)
            else:
                result = kernel_matching(ps_df, df[dep_var].reset_index(drop=True),
                                         treat_col)

            st.markdown(f"#### ATT 估计（{result['method']}）")
            col_a, col_b, col_c = st.columns(3)
            col_a.metric("ATT（平均处理效应）", f"{result['att']}{result['stars']}")
            col_b.metric("标准误", str(result["att_se"]))
            col_c.metric("p 值", str(result["p_value"]))


# ── RDD ───────────────────────────────────────────────────────────────────────
def _run_rdd(df: pd.DataFrame) -> None:
    from analysis.causal_rdd import (
        run_rdd_local_linear, select_optimal_bandwidth,
        mccrary_density_test, plot_rdd,
    )

    st.markdown("### RDD 断点回归")
    numeric_cols = df.select_dtypes(include="number").columns.tolist()

    col1, col2 = st.columns(2)
    with col1:
        dep_var     = st.selectbox("被解释变量（Y）", numeric_cols, key="rdd_dep")
        running_var = st.selectbox("运行变量（评分/指标）", numeric_cols,
                                   key="rdd_run")
    with col2:
        cutoff    = st.number_input("断点值", value=60.0, key="rdd_cutoff")
        bw        = st.number_input("带宽（0=自动选择）", value=0.0, step=0.1,
                                    key="rdd_bw")
        poly      = st.radio("多项式阶数", [1, 2], horizontal=True, key="rdd_poly")

    bandwidth = bw if bw > 0 else None

    if st.button("▶ 运行 RDD 分析", type="primary"):
        with st.spinner("分析中..."):
            # RDD 可视化
            fig = plot_rdd(df, dep_var, running_var, cutoff, bandwidth)
            display_figure(fig, "RDD 断点图", "rdd_plot.png")

            # 最优带宽
            if bandwidth is None:
                bw_result = select_optimal_bandwidth(df, dep_var, running_var, cutoff)
                bandwidth = bw_result["optimal_bandwidth"]
                st.info(f"📏 建议带宽：{bandwidth}（score 标准差 × 1.0）")
                if not bw_result["sensitivity_table"].empty:
                    display_result_table(bw_result["sensitivity_table"],
                                         "带宽敏感性分析")

            # 局部线性回归
            result = run_rdd_local_linear(df, dep_var, running_var, cutoff,
                                           bandwidth, poly)
            if "error" in result:
                st.error(result["error"])
            else:
                col_a, col_b, col_c, col_d = st.columns(4)
                col_a.metric("断点处跳跃（RDD系数）",
                             f"{result['coef']}{result['stars']}")
                col_b.metric("标准误", str(result["se"]))
                col_c.metric("p 值", str(result["pval"]))
                col_d.metric("带宽内 N", str(result["n_obs"]))

            # McCrary 密度检验
            st.markdown("#### McCrary 密度检验")
            density_result, density_fig = mccrary_density_test(
                df, running_var, cutoff
            )
            display_figure(density_fig, "密度连续性检验", "mccrary.png")
            display_test_result(density_result, "密度检验结果")


# ── IV/2SLS ───────────────────────────────────────────────────────────────────
def _run_iv(df: pd.DataFrame) -> None:
    from analysis.causal_iv import run_iv_2sls, plot_iv_diagnostics

    st.markdown("### IV / 2SLS 工具变量回归")
    numeric_cols = df.select_dtypes(include="number").columns.tolist()

    col1, col2 = st.columns(2)
    with col1:
        dep_var   = st.selectbox("被解释变量（Y）", numeric_cols, key="iv_dep")
        endog_var = st.selectbox("内生变量（X）",
                                 [c for c in numeric_cols if c != dep_var],
                                 key="iv_endog")
    with col2:
        instruments = st.multiselect(
            "工具变量（Z）",
            [c for c in numeric_cols if c not in [dep_var, endog_var]],
            key="iv_instruments",
        )

    controls = st.multiselect(
        "外生控制变量",
        [c for c in numeric_cols if c not in [dep_var, endog_var] + instruments],
        key="iv_controls",
    )

    if not instruments:
        st.info("请选择工具变量")
        return

    if st.button("▶ 运行 IV/2SLS", type="primary"):
        with st.spinner("估计中..."):
            result = run_iv_2sls(df, dep_var, endog_var, instruments,
                                  controls or None)
            if "error" in result:
                st.error(result["error"])
                return

            col_a, col_b, col_c = st.columns(3)
            col_a.metric("IV 系数", f"{result['coef']}{result['stars']}")
            col_b.metric("标准误", str(result["se"]))
            col_c.metric("第一阶段 F", f"{result['first_stage_f']:.2f}"
                         + (" ✅" if result["weak_iv_pass"] else " ⚠️弱工具"))

            display_test_result(result["wu_hausman"], "Wu-Hausman 内生性检验", "结论")
            if "p值" in result.get("sargan", {}):
                display_test_result(result["sargan"], "Sargan 过度识别检验", "结论")


# ── Bootstrap ─────────────────────────────────────────────────────────────────
def _run_bootstrap(df: pd.DataFrame) -> None:
    from analysis.robustness import bootstrap_confidence_interval

    st.markdown("### Bootstrap 置信区间")
    numeric_cols = df.select_dtypes(include="number").columns.tolist()

    col1, col2 = st.columns(2)
    with col1:
        dep_var  = st.selectbox("被解释变量", numeric_cols, key="boot_dep")
        key_var  = st.selectbox("关注变量（计算CI）",
                                [c for c in numeric_cols if c != dep_var],
                                key="boot_key")
    with col2:
        n_boot = st.slider("Bootstrap 次数", 200, 2000, 1000, 100, key="boot_n")
        indep_vars = st.multiselect("所有解释变量",
                                    [c for c in numeric_cols if c != dep_var],
                                    key="boot_indep")

    if not indep_vars:
        return

    if st.button("▶ 运行 Bootstrap", type="primary"):
        with st.spinner(f"Bootstrap 中（{n_boot}次）..."):
            result, fig = bootstrap_confidence_interval(
                df, dep_var, indep_vars, key_var, n_boot
            )
            display_figure(fig, "Bootstrap 分布", "bootstrap.png")
            st.info(result.get("conclusion", ""))


# ── 剔除特殊样本 ──────────────────────────────────────────────────────────────
def _run_exclude_samples(df: pd.DataFrame) -> None:
    from analysis.robustness import exclude_special_samples

    st.markdown("### 剔除特殊样本稳健性检验")
    numeric_cols = df.select_dtypes(include="number").columns.tolist()

    dep_var    = st.selectbox("被解释变量", numeric_cols, key="excl_dep")
    key_var    = st.selectbox("核心解释变量",
                              [c for c in numeric_cols if c != dep_var],
                              key="excl_key")
    indep_vars = st.multiselect("所有解释变量",
                                [c for c in numeric_cols if c != dep_var],
                                key="excl_indep")

    st.markdown("**排除条件（pandas query 语法）**")
    n_conditions = st.number_input("条件数量", 1, 5, 2, key="excl_n")
    conditions = []
    for i in range(int(n_conditions)):
        col_a, col_b = st.columns([1, 2])
        with col_a:
            label = st.text_input(f"条件{i+1}说明", f"排除条件{i+1}",
                                  key=f"excl_label_{i}")
        with col_b:
            query = st.text_input(f"Query（如 industry=='科技'）", "",
                                  key=f"excl_query_{i}")
        if query:
            conditions.append({"label": label, "query": query})

    if not indep_vars or not conditions:
        return

    if st.button("▶ 运行稳健性检验", type="primary"):
        with st.spinner("检验中..."):
            result_df = exclude_special_samples(df, dep_var, indep_vars,
                                                key_var, conditions)
            display_result_table(result_df, "剔除特殊样本稳健性结果")


# ── 分组回归 ──────────────────────────────────────────────────────────────────
def _run_subgroup(df: pd.DataFrame) -> None:
    from analysis.heterogeneity import run_subgroup_regression

    st.markdown("### 分组回归（异质性分析）")
    numeric_cols = df.select_dtypes(include="number").columns.tolist()
    all_cols     = list(df.columns)

    col1, col2 = st.columns(2)
    with col1:
        dep_var   = st.selectbox("被解释变量", numeric_cols, key="sub_dep")
        key_var   = st.selectbox("核心解释变量",
                                 [c for c in numeric_cols if c != dep_var],
                                 key="sub_key")
    with col2:
        group_col  = st.selectbox("分组变量", all_cols, key="sub_group")
        indep_vars = st.multiselect("解释变量（含核心变量）",
                                    [c for c in numeric_cols if c != dep_var],
                                    key="sub_indep")

    if not indep_vars:
        return

    if st.button("▶ 运行分组回归", type="primary"):
        with st.spinner("回归中..."):
            result_df, fig = run_subgroup_regression(
                df, dep_var, indep_vars, key_var, group_col
            )
            display_figure(fig, "分组回归系数比较图", "subgroup.png")
            display_result_table(result_df, "分组回归结果对比")


# ── 分位数回归 ────────────────────────────────────────────────────────────────
def _run_quantile(df: pd.DataFrame) -> None:
    from analysis.heterogeneity import run_quantile_regression

    st.markdown("### 分位数回归")
    numeric_cols = df.select_dtypes(include="number").columns.tolist()

    dep_var    = st.selectbox("被解释变量", numeric_cols, key="qr_dep")
    key_var    = st.selectbox("核心解释变量",
                              [c for c in numeric_cols if c != dep_var],
                              key="qr_key")
    indep_vars = st.multiselect("所有解释变量（含核心）",
                                [c for c in numeric_cols if c != dep_var],
                                key="qr_indep")

    if not indep_vars or key_var not in indep_vars:
        st.info("请将核心解释变量包含在解释变量中")
        return

    if st.button("▶ 运行分位数回归", type="primary"):
        with st.spinner("回归中..."):
            result_df, fig = run_quantile_regression(df, dep_var, indep_vars, key_var)
            display_figure(fig, "分位数回归系数图", "quantile_reg.png")
            display_result_table(result_df, "分位数回归结果")


# ── 中介效应 ──────────────────────────────────────────────────────────────────
def _run_mediation(df: pd.DataFrame) -> None:
    from analysis.heterogeneity import run_mediation_analysis

    st.markdown("### 中介效应分析（Bootstrap）")
    numeric_cols = df.select_dtypes(include="number").columns.tolist()

    col1, col2, col3 = st.columns(3)
    with col1:
        treatment = st.selectbox("处理/原因变量（X）", numeric_cols, key="med_x")
    with col2:
        mediator  = st.selectbox("中介变量（M）",
                                 [c for c in numeric_cols if c != treatment],
                                 key="med_m")
    with col3:
        dep_var   = st.selectbox("结果变量（Y）",
                                 [c for c in numeric_cols
                                  if c not in [treatment, mediator]],
                                 key="med_y")

    controls = st.multiselect("控制变量",
                              [c for c in numeric_cols
                               if c not in [treatment, mediator, dep_var]],
                              key="med_controls")
    n_boot   = st.slider("Bootstrap 次数", 200, 2000, 1000, 100, key="med_boot")

    if st.button("▶ 运行中介效应分析", type="primary"):
        with st.spinner(f"Bootstrap 中（{n_boot}次）..."):
            result, fig = run_mediation_analysis(
                df, dep_var, mediator, treatment, controls or None, n_boot
            )
            display_figure(fig, "中介效应路径图与Bootstrap分布", "mediation.png")
            col_a, col_b, col_c = st.columns(3)
            col_a.metric("间接效应（a×b）", str(result["indirect_effect"]))
            col_b.metric("直接效应（c'）", str(result["direct_effect"]))
            col_c.metric("中介比例", f"{result['pct_mediated']}%")
            st.info(result.get("conclusion", ""))


# ── 调节效应 ──────────────────────────────────────────────────────────────────
def _run_moderation(df: pd.DataFrame) -> None:
    from analysis.heterogeneity import run_moderation_analysis

    st.markdown("### 调节效应分析")
    numeric_cols = df.select_dtypes(include="number").columns.tolist()

    col1, col2, col3 = st.columns(3)
    with col1:
        treatment = st.selectbox("自变量（X）", numeric_cols, key="mod_x")
    with col2:
        moderator = st.selectbox("调节变量（M）",
                                 [c for c in numeric_cols if c != treatment],
                                 key="mod_m")
    with col3:
        dep_var   = st.selectbox("因变量（Y）",
                                 [c for c in numeric_cols
                                  if c not in [treatment, moderator]],
                                 key="mod_y")

    controls = st.multiselect("控制变量",
                              [c for c in numeric_cols
                               if c not in [treatment, moderator, dep_var]],
                              key="mod_controls")

    if st.button("▶ 运行调节效应分析", type="primary"):
        with st.spinner("分析中..."):
            result, fig = run_moderation_analysis(
                df, dep_var, treatment, moderator, controls or None
            )
            display_figure(fig, "调节效应简单斜率图", "moderation.png")
            col_a, col_b, col_c = st.columns(3)
            col_a.metric("交互项系数", f"{result['interaction_coef']}{result['stars']}")
            col_b.metric("标准误", str(result["interaction_se"]))
            col_c.metric("p 值", str(result["interaction_pval"]))
            st.info(result.get("conclusion", ""))


# ── 工具函数 ──────────────────────────────────────────────────────────────────
def _save_result(key: str, result: dict) -> None:
    """将分析结果保存到 session_state"""
    if "analysis_results" not in st.session_state:
        st.session_state["analysis_results"] = {}
    st.session_state["analysis_results"][key] = result
