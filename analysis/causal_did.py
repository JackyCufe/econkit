"""
DID 双重差分分析模块
包含：基准DID、双向固定效应DID、平行趋势检验（事件研究法）、安慰剂检验
"""
from __future__ import annotations

import warnings
from typing import Optional

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import statsmodels.formula.api as smf
import statsmodels.api as sm

warnings.filterwarnings("ignore")


# ── 基准 DID ──────────────────────────────────────────────────────────────────
def run_basic_did(
    df: pd.DataFrame,
    dep_var: str,
    treat_col: str,
    post_col: str,
    did_col: str,
    controls: Optional[list[str]] = None,
    cov_type: str = "HC3",
) -> dict:
    """
    OLS 基准 DID 回归

    Args:
        dep_var:   被解释变量
        treat_col: 处理组虚拟变量（treat=1为处理组）
        post_col:  政策后虚拟变量（post=1为政策后）
        did_col:   交乘项（treat×post），也可由函数自动创建
        controls:  控制变量列表
        cov_type:  标准误类型

    Returns: 结果字典
    """
    df = df.copy()

    # 若 did_col 不存在，自动创建
    if did_col not in df.columns:
        df[did_col] = df[treat_col] * df[post_col]

    indep = [did_col, treat_col, post_col]
    if controls:
        indep += controls

    subset = df[[dep_var] + indep].dropna()
    X = sm.add_constant(subset[indep], has_constant="add")
    y = subset[dep_var]
    model = sm.OLS(y, X).fit(cov_type=cov_type)

    did_coef  = model.params.get(did_col, np.nan)
    did_se    = model.bse.get(did_col, np.nan)
    did_pval  = model.pvalues.get(did_col, np.nan)
    did_ci    = model.conf_int().loc[did_col] if did_col in model.conf_int().index else [np.nan, np.nan]

    stars = "***" if did_pval < 0.01 else "**" if did_pval < 0.05 else "*" if did_pval < 0.1 else ""

    return {
        "model":     model,
        "did_coef":  round(float(did_coef), 4),
        "did_se":    round(float(did_se), 4),
        "did_pval":  round(float(did_pval), 4),
        "did_stars": stars,
        "did_ci":    [round(float(did_ci[0]), 4), round(float(did_ci[1]), 4)],
        "n_obs":     int(model.nobs),
        "r2":        round(float(model.rsquared), 4),
        "adj_r2":    round(float(model.rsquared_adj), 4),
    }


# ── 双向固定效应 DID ──────────────────────────────────────────────────────────
def run_twfe_did(
    df: pd.DataFrame,
    dep_var: str,
    did_col: str,
    id_col: str,
    time_col: str,
    controls: Optional[list[str]] = None,
) -> dict:
    """
    双向固定效应 DID（个体+时间固定效应）

    Returns: 结果字典
    """
    from linearmodels import PanelOLS

    df = df.copy()
    indep_vars = [did_col] + (controls or [])
    subset = (df[[id_col, time_col, dep_var] + indep_vars]
              .dropna()
              .set_index([id_col, time_col]))

    formula = f"{dep_var} ~ {' + '.join(indep_vars)} + EntityEffects + TimeEffects"
    model = PanelOLS.from_formula(formula, data=subset, drop_absorbed=True)
    result = model.fit(cov_type="clustered", cluster_entity=True)

    did_coef = float(result.params.get(did_col, np.nan))
    did_se   = float(result.std_errors.get(did_col, np.nan))
    did_pval = float(result.pvalues.get(did_col, np.nan))

    stars = "***" if did_pval < 0.01 else "**" if did_pval < 0.05 else "*" if did_pval < 0.1 else ""

    return {
        "model":     result,
        "did_coef":  round(did_coef, 4),
        "did_se":    round(did_se, 4),
        "did_pval":  round(did_pval, 4),
        "did_stars": stars,
        "n_obs":     int(result.nobs),
        "r2_within": round(float(result.rsquared), 4),
    }


# ── 平行趋势检验（事件研究法）─────────────────────────────────────────────────
def run_parallel_trend_test(
    df: pd.DataFrame,
    dep_var: str,
    treat_col: str,
    time_col: str,
    treat_year: int,
    id_col: str,
    controls: Optional[list[str]] = None,
) -> tuple[dict, plt.Figure]:
    """
    事件研究法平行趋势检验

    Args:
        treat_year: 政策实施年份（基准期为 treat_year-1）

    Returns: (结果字典, matplotlib Figure)
    """
    df = df.copy()
    df["rel_year"] = df[time_col] - treat_year

    # 创建安全列名（负数用 m 前缀）
    unique_rel_years = sorted(df["rel_year"].unique())
    # 基准期：t-1（即 rel_year = -1）
    base_period = -1

    event_vars = [y for y in unique_rel_years if y != base_period]

    def safe_col(y: int) -> str:
        return f"tm{abs(y)}" if y < 0 else f"tp{y}"

    # 创建虚拟变量和交互项
    for y in event_vars:
        col = safe_col(y)
        df[col] = (df["rel_year"] == y).astype(float)
        df[f"inter_{col}"] = df[treat_col] * df[col]

    interact_terms = [f"inter_{safe_col(y)}" for y in event_vars]
    controls_part  = " + ".join(controls) if controls else ""
    fe_part        = f"+ C({id_col}) + C({time_col})"

    indep_str = " + ".join(interact_terms)
    if controls_part:
        indep_str += " + " + controls_part
    formula = f"{dep_var} ~ {indep_str} {fe_part}"

    try:
        ev_model = smf.ols(formula, data=df).fit(cov_type="HC3")
    except Exception as e:
        return {"error": str(e)}, plt.figure()

    # 提取系数
    coefs:  list[float] = []
    ci_lo:  list[float] = []
    ci_hi:  list[float] = []
    labels: list[str]   = []
    pvals:  list[float] = []

    for y in sorted(event_vars):
        term = f"inter_{safe_col(y)}"
        if term in ev_model.params:
            c  = float(ev_model.params[term])
            lo = float(ev_model.conf_int().loc[term, 0])
            hi = float(ev_model.conf_int().loc[term, 1])
            pv = float(ev_model.pvalues[term])
            coefs.append(c)
            ci_lo.append(lo)
            ci_hi.append(hi)
            pvals.append(pv)
            labels.append(f"t{y:+d}" if y != 0 else "t0")

    # 在基准期插入 0
    base_idx = sum(1 for y in sorted(event_vars) if y < base_period + 1)
    coefs.insert(base_idx, 0.0)
    ci_lo.insert(base_idx, 0.0)
    ci_hi.insert(base_idx, 0.0)
    pvals.insert(base_idx, 1.0)
    labels.insert(base_idx, f"t{base_period:+d}（基准）")

    # 绘图
    fig, ax = plt.subplots(figsize=(10, 6))
    x = range(len(labels))
    pivot = base_idx

    ax.axhline(0, color="gray", linestyle="--", linewidth=0.8, alpha=0.7)
    ax.axvline(pivot, color="#E74C3C", linestyle=":", linewidth=1.5,
               label="基准期（t-1）", alpha=0.7)

    # 政策实施后背景色
    policy_start = sum(1 for l in labels if l.startswith("t-") or l == "t-1（基准）")
    ax.axvspan(policy_start - 0.5, len(labels) - 0.5,
               alpha=0.05, color="#E74C3C", label="政策实施后")

    ax.errorbar(x, coefs,
                yerr=[np.array(coefs) - np.array(ci_lo),
                      np.array(ci_hi) - np.array(coefs)],
                fmt="o-", color="#2C3E50", capsize=4,
                ecolor="#3498DB", linewidth=2, markersize=6,
                label="处理效应估计")

    # 标注显著性
    for i, (c, p) in enumerate(zip(coefs, pvals)):
        if p < 0.1 and i != base_idx:
            stars = "***" if p < 0.01 else "**" if p < 0.05 else "*"
            offset = max(np.array(ci_hi)) * 0.05
            ax.text(i, c + offset, stars, ha="center", va="bottom",
                    color="#E74C3C", fontsize=10, fontweight="bold")

    ax.set_xticks(list(x))
    ax.set_xticklabels(labels, rotation=30, ha="right", fontsize=9)
    ax.set_xlabel("相对政策实施年份", fontsize=11)
    ax.set_ylabel(f"{dep_var} 变化量", fontsize=11)
    ax.set_title("平行趋势检验（事件研究法）\n政策前系数应围绕0波动且不显著",
                 fontsize=12, fontweight="bold", color="#2C3E50")
    ax.legend(fontsize=10)
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)
    plt.tight_layout()

    # 平行趋势是否通过（政策前系数联合检验）
    pre_terms = [f"inter_{safe_col(y)}" for y in event_vars
                 if y < 0 and f"inter_{safe_col(y)}" in ev_model.params]
    pre_test = _joint_significance_test(ev_model, pre_terms)

    return {
        "coefs":     coefs,
        "labels":    labels,
        "ci_lo":     ci_lo,
        "ci_hi":     ci_hi,
        "pvals":     pvals,
        "pre_test":  pre_test,
        "conclusion": (
            "✅ 平行趋势假设成立（政策前系数联合不显著）"
            if (pre_test.get("p_value") is not None and pre_test.get("p_value", 0) > 0.1)
            else "⚠️ 平行趋势假设可能不满足（政策前系数联合显著或无法检验）"
        ),
    }, fig


def _joint_significance_test(model, terms: list[str]) -> dict:
    """对多个系数进行联合显著性检验（F检验）"""
    if not terms:
        return {"f_stat": None, "p_value": None}
    try:
        hypotheses = [(f"{t} = 0") for t in terms]
        f_test = model.f_test(" | ".join(hypotheses))
        return {
            "f_stat":  round(float(f_test.statistic), 4),
            "p_value": round(float(f_test.pvalue), 4),
        }
    except Exception:
        return {"f_stat": None, "p_value": None}


# ── 安慰剂检验（置换处理组）──────────────────────────────────────────────────
def run_placebo_test(
    df: pd.DataFrame,
    dep_var: str,
    treat_col: str,
    post_col: str,
    controls: Optional[list[str]] = None,
    n_sim: int = 1000,
    real_coef: Optional[float] = None,
) -> tuple[dict, plt.Figure]:
    """
    安慰剂检验：随机置换处理组标签，1000次模拟

    Returns: (结果字典, matplotlib Figure)
    """
    rng = np.random.default_rng(42)
    indep = [treat_col, post_col] + (controls or [])
    subset = df[[dep_var] + indep].dropna().reset_index(drop=True)

    placebo_coefs: list[float] = []
    for _ in range(n_sim):
        sim = subset.copy()
        sim["treat_fake"] = rng.permutation(sim[treat_col].values)
        sim["did_fake"]   = sim["treat_fake"] * sim[post_col]

        indep_sim = ["did_fake", "treat_fake", post_col] + (controls or [])
        available = [c for c in indep_sim if c in sim.columns]
        X = sm.add_constant(sim[available], has_constant="add")
        y = sim[dep_var]
        coef = sm.OLS(y, X).fit().params.get("did_fake", np.nan)
        placebo_coefs.append(float(coef))

    placebo_arr = np.array(placebo_coefs)

    if real_coef is None:
        real_coef = 0.0

    p_val = float(np.mean(np.abs(placebo_arr) >= np.abs(real_coef)))

    # 绘图
    fig, ax = plt.subplots(figsize=(10, 6))
    ax.hist(placebo_arr, bins=50, alpha=0.7,
            color="#2C3E50", edgecolor="white", linewidth=0.5,
            label="安慰剂系数分布")
    ax.axvline(real_coef, color="#E74C3C", linewidth=2.5,
               label=f"真实系数 = {real_coef:.4f}")
    ax.axvline(-real_coef, color="#E74C3C", linewidth=1.5,
               linestyle="--", alpha=0.6, label=f"对称值 = {-real_coef:.4f}")

    # 核密度曲线
    from scipy.stats import gaussian_kde
    kde = gaussian_kde(placebo_arr)
    x_range = np.linspace(placebo_arr.min(), placebo_arr.max(), 200)
    ax2 = ax.twinx()
    ax2.plot(x_range, kde(x_range), color="#3498DB", linewidth=1.5,
             label="核密度")
    ax2.set_ylabel("密度", color="#3498DB")
    ax2.tick_params(axis="y", colors="#3498DB")
    ax2.set_ylim(0, ax2.get_ylim()[1] * 1.5)

    ax.set_xlabel("安慰剂 DID 系数")
    ax.set_ylabel("频次")
    ax.set_title(f"安慰剂检验（{n_sim}次随机置换）\n真实系数在尾部证明效应真实存在",
                 fontsize=12, fontweight="bold", color="#2C3E50")
    ax.legend(fontsize=10)
    ax.spines["top"].set_visible(False)
    plt.tight_layout()

    return {
        "n_sim":         n_sim,
        "placebo_mean":  round(float(placebo_arr.mean()), 4),
        "placebo_std":   round(float(placebo_arr.std()), 4),
        "real_coef":     round(float(real_coef), 4),
        "p_value":       round(p_val, 4),
        "conclusion": (
            "✅ 安慰剂检验通过：真实效应显著，非随机偶然"
            if p_val < 0.1
            else "⚠️ 安慰剂检验未通过：真实系数未超过随机分布"
        ),
    }, fig
