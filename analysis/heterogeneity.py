"""
异质性与机制分析模块
包含：分组回归、分位数回归、中介效应（Bootstrap）、调节效应
"""
from __future__ import annotations

import warnings
from typing import Optional, Callable

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import statsmodels.api as sm
import statsmodels.formula.api as smf
from scipy import stats

warnings.filterwarnings("ignore")


# ── 分组回归 ──────────────────────────────────────────────────────────────────
def run_subgroup_regression(
    df: pd.DataFrame,
    dep_var: str,
    indep_vars: list[str],
    key_var: str,
    group_col: str,
    cov_type: str = "HC3",
) -> tuple[pd.DataFrame, plt.Figure]:
    """
    分组回归，估计各子样本中的处理效应

    Args:
        group_col: 分组变量列名

    Returns: (对比表 DataFrame, 系数比较图)
    """
    groups = df[group_col].unique()
    rows:  list[dict] = []
    coefs: list[float] = []
    cis_lo: list[float] = []
    cis_hi: list[float] = []
    labels: list[str] = []

    for grp in sorted(groups):
        sub_df = df[df[group_col] == grp]
        if len(sub_df) < 20:
            continue

        subset = sub_df[[dep_var] + indep_vars].dropna()
        X = sm.add_constant(subset[indep_vars], has_constant="add")
        y = subset[dep_var]
        model = sm.OLS(y, X).fit(cov_type=cov_type)

        coef  = float(model.params.get(key_var, np.nan))
        se    = float(model.bse.get(key_var, np.nan))
        pval  = float(model.pvalues.get(key_var, np.nan))
        ci    = model.conf_int().loc[key_var] if key_var in model.conf_int().index else pd.Series([np.nan, np.nan])
        stars = "***" if pval < 0.01 else "**" if pval < 0.05 else "*" if pval < 0.1 else ""

        rows.append({
            "子样本":   str(grp),
            "系数":     round(coef, 4),
            "标准误":   round(se, 4),
            "p值":      round(pval, 4),
            "显著性":   stars,
            "CI下界":   round(float(ci.iloc[0]), 4),
            "CI上界":   round(float(ci.iloc[1]), 4),
            "N":        int(model.nobs),
        })
        coefs.append(coef)
        cis_lo.append(float(ci.iloc[0]))
        cis_hi.append(float(ci.iloc[1]))
        labels.append(str(grp))

    result_df = pd.DataFrame(rows)

    # 绘图
    fig, ax = plt.subplots(figsize=(10, max(5, len(labels) * 0.8 + 2)))
    y_pos = np.arange(len(labels))
    colors_list = ["#2C3E50", "#E74C3C", "#3498DB", "#27AE60",
                   "#8E44AD", "#E67E22"] * (len(labels) // 6 + 1)

    for i, (coef, lo, hi, c) in enumerate(zip(coefs, cis_lo, cis_hi, colors_list)):
        ax.barh(i, coef, color=c, alpha=0.7, height=0.5)
        ax.errorbar(coef, i, xerr=[[coef - lo], [hi - coef]],
                    fmt="none", color="black", capsize=5, linewidth=1.5)
        ax.text(max(coef, hi) + 0.002, i,
                f"{coef:.4f}", va="center", ha="left", fontsize=10)

    ax.set_yticks(y_pos)
    ax.set_yticklabels(labels, fontsize=11)
    ax.axvline(0, color="gray", linestyle="--", linewidth=0.8)
    ax.set_xlabel(f"{key_var} 系数")
    ax.set_title(f"分组回归结果（按 {group_col} 分组）\n各子样本 {key_var} 的处理效应",
                 fontsize=12, fontweight="bold", color="#2C3E50")
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)
    plt.tight_layout()

    return result_df, fig


# ── 分位数回归 ────────────────────────────────────────────────────────────────
def run_quantile_regression(
    df: pd.DataFrame,
    dep_var: str,
    indep_vars: list[str],
    key_var: str,
    quantiles: Optional[list[float]] = None,
) -> tuple[pd.DataFrame, plt.Figure]:
    """
    分位数回归（Quantile Regression）

    Returns: (各分位点系数表, 分位点系数图)
    """
    if quantiles is None:
        quantiles = [0.1, 0.25, 0.5, 0.75, 0.9]

    subset  = df[[dep_var] + indep_vars].dropna()
    formula = dep_var + " ~ " + " + ".join(indep_vars)

    rows: list[dict] = []
    coefs: list[float] = []
    ci_lo: list[float] = []
    ci_hi: list[float] = []

    for q in quantiles:
        model = smf.quantreg(formula, data=subset).fit(q=q)
        if key_var in model.params:
            coef = float(model.params[key_var])
            se   = float(model.bse[key_var])
            pval = float(model.pvalues[key_var])
            lo   = float(model.conf_int().loc[key_var, 0])
            hi   = float(model.conf_int().loc[key_var, 1])
        else:
            coef, se, pval, lo, hi = np.nan, np.nan, np.nan, np.nan, np.nan

        stars = "***" if pval < 0.01 else "**" if pval < 0.05 else "*" if pval < 0.1 else ""
        rows.append({
            "分位数":   f"Q{q:.2f}",
            "系数":     round(coef, 4),
            "标准误":   round(se, 4),
            "p值":      round(pval, 4),
            "显著性":   stars,
            "CI下界":   round(lo, 4),
            "CI上界":   round(hi, 4),
        })
        coefs.append(coef)
        ci_lo.append(lo)
        ci_hi.append(hi)

    result_df = pd.DataFrame(rows)

    # OLS 基准
    ols = smf.ols(formula, data=subset).fit()
    ols_coef = float(ols.params.get(key_var, np.nan))
    ols_ci   = ols.conf_int().loc[key_var].tolist() if key_var in ols.conf_int().index else [np.nan, np.nan]

    # 绘图
    fig, ax = plt.subplots(figsize=(10, 6))
    ax.plot(quantiles, coefs, "o-", color="#2C3E50", linewidth=2, markersize=8,
            label="分位数回归系数")
    ax.fill_between(quantiles, ci_lo, ci_hi, alpha=0.2, color="#2C3E50",
                    label="95% 置信区间")
    ax.axhline(ols_coef, color="#E74C3C", linewidth=2, linestyle="--",
               label=f"OLS 系数 = {ols_coef:.4f}")
    ax.fill_between(quantiles,
                    [ols_ci[0]] * len(quantiles),
                    [ols_ci[1]] * len(quantiles),
                    alpha=0.1, color="#E74C3C")

    ax.set_xlabel("分位数")
    ax.set_ylabel(f"{key_var} 系数")
    ax.set_xticks(quantiles)
    ax.set_xticklabels([f"Q{q:.2f}" for q in quantiles])
    ax.set_title(f"分位数回归结果（{key_var}）\n效应在不同分布位置的异质性",
                 fontsize=12, fontweight="bold", color="#2C3E50")
    ax.legend(fontsize=10)
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)
    plt.tight_layout()

    return result_df, fig


# ── re-export 中介效应（已移至 mediation.py）──────────────────────────────────
from analysis.mediation import run_mediation_analysis  # noqa: F401,E402


# ── 调节效应 ──────────────────────────────────────────────────────────────────
def run_moderation_analysis(
    df: pd.DataFrame,
    dep_var: str,
    treatment: str,
    moderator: str,
    controls: Optional[list[str]] = None,
    n_levels: int = 3,
) -> tuple[dict, plt.Figure]:
    """
    调节效应分析（交互项回归 + 简单斜率图）

    Args:
        n_levels: 简单斜率图中调节变量的水平数（3=低/中/高）

    Returns: (结果字典, 简单斜率图)
    """
    controls = controls or []
    df = df.copy()

    # 中心化
    df["X_c"] = df[treatment] - df[treatment].mean()
    df["M_c"] = df[moderator] - df[moderator].mean()
    df["XM"]  = df["X_c"] * df["M_c"]

    indep_vars = ["X_c", "M_c", "XM"] + controls
    subset = df[[dep_var] + indep_vars].dropna()
    X = sm.add_constant(subset[indep_vars], has_constant="add")
    y = subset[dep_var]
    model = sm.OLS(y, X).fit(cov_type="HC3")

    xm_coef  = float(model.params.get("XM", np.nan))
    xm_se    = float(model.bse.get("XM", np.nan))
    xm_pval  = float(model.pvalues.get("XM", np.nan))
    stars = "***" if xm_pval < 0.01 else "**" if xm_pval < 0.05 else "*" if xm_pval < 0.1 else ""

    # 简单斜率图
    m_std = float(df[moderator].std())
    m_levels = {
        "低（-1SD）": -m_std,
        "均值（0）":   0.0,
        "高（+1SD）":  m_std,
    }

    x_range = np.linspace(float(df["X_c"].min()), float(df["X_c"].max()), 100)
    const_coef = float(model.params.get("const", 0))
    x_coef     = float(model.params.get("X_c", 0))
    m_coef     = float(model.params.get("M_c", 0))
    xm_c       = float(model.params.get("XM", 0))

    fig, ax = plt.subplots(figsize=(10, 6))
    colors_list = ["#2C3E50", "#E74C3C", "#3498DB"]
    for (label, m_val), color in zip(m_levels.items(), colors_list):
        y_pred = const_coef + x_coef * x_range + m_coef * m_val + xm_c * x_range * m_val
        ax.plot(x_range + df[treatment].mean(), y_pred,
                color=color, linewidth=2.5, label=f"{moderator}: {label}")

    ax.set_xlabel(treatment)
    ax.set_ylabel(dep_var)
    ax.set_title(f"调节效应简单斜率图\n交互项系数={xm_coef:.4f}{stars}（{moderator} 调节 {treatment} 的效应）",
                 fontsize=12, fontweight="bold", color="#2C3E50")
    ax.legend(fontsize=10)
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)
    plt.tight_layout()

    return {
        "interaction_coef": round(xm_coef, 4),
        "interaction_se":   round(xm_se, 4),
        "interaction_pval": round(xm_pval, 4),
        "stars":            stars,
        "n_obs":            int(model.nobs),
        "r2":               round(float(model.rsquared), 4),
        "conclusion": (
            f"✅ 调节效应显著（交互项系数={xm_coef:.4f}{stars}, p={xm_pval:.4f}）"
            if xm_pval < 0.1
            else f"调节效应不显著（p={xm_pval:.4f}）"
        ),
    }, fig
