"""
异质性与机制分析模块
包含：分组回归、分位数回归、中介效应（Bootstrap）、调节效应
"""
from __future__ import annotations

import warnings
from typing import Optional

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


# ── 中介效应（Bootstrap）────────────────────────────────────────────────────
def run_mediation_analysis(
    df: pd.DataFrame,
    dep_var: str,
    mediator: str,
    treatment: str,
    controls: Optional[list[str]] = None,
    n_bootstrap: int = 1000,
    ci_level: float = 0.95,
) -> tuple[dict, plt.Figure]:
    """
    Bootstrap 中介效应分析（Baron-Kenny 框架）

    Args:
        dep_var:   结果变量 (Y)
        mediator:  中介变量 (M)
        treatment: 处理变量 (X)

    Returns: (结果字典, 可视化图)
    """
    rng = np.random.default_rng(42)
    controls = controls or []
    all_cols = [dep_var, mediator, treatment] + controls
    subset = df[all_cols].dropna().reset_index(drop=True)

    # 路径估计
    path_a_coef, path_b_coef, path_c_coef, path_c_prime_coef = _estimate_paths(
        subset, dep_var, mediator, treatment, controls
    )
    indirect_effect = path_a_coef * path_b_coef

    # Bootstrap 间接效应
    indirect_boot: list[float] = []
    for _ in range(n_bootstrap):
        boot_df = subset.sample(n=len(subset), replace=True, random_state=None)
        a, b, c, c_p = _estimate_paths(boot_df, dep_var, mediator, treatment, controls)
        indirect_boot.append(a * b)

    boot_arr = np.array(indirect_boot)
    alpha = 1 - ci_level
    ci_lo = float(np.percentile(boot_arr, alpha / 2 * 100))
    ci_hi = float(np.percentile(boot_arr, (1 - alpha / 2) * 100))
    p_val_indirect = float(np.mean(
        np.abs(boot_arr - boot_arr.mean()) >= abs(indirect_effect)
    ))

    # 效应分解
    total = path_c_coef
    indirect = indirect_effect
    direct   = path_c_prime_coef
    pct_mediated = (indirect / (total + 1e-10)) * 100

    # 绘图
    fig, axes = plt.subplots(1, 2, figsize=(14, 6))

    # 图1：路径图
    ax = axes[0]
    ax.axis("off")
    _draw_mediation_path(ax, path_a_coef, path_b_coef,
                         path_c_coef, path_c_prime_coef,
                         treatment, mediator, dep_var)

    # 图2：Bootstrap 分布
    ax2 = axes[1]
    ax2.hist(boot_arr, bins=50, alpha=0.7, color="#2C3E50",
             edgecolor="white", linewidth=0.5)
    ax2.axvline(indirect_effect, color="#E74C3C", linewidth=2.5,
                label=f"间接效应 = {indirect_effect:.4f}")
    ax2.axvline(ci_lo, color="#3498DB", linewidth=1.5, linestyle="--",
                label=f"CI [{ci_lo:.4f}, {ci_hi:.4f}]")
    ax2.axvline(ci_hi, color="#3498DB", linewidth=1.5, linestyle="--")
    ax2.axvline(0, color="gray", linewidth=0.8, linestyle="-")
    ax2.axvspan(ci_lo, ci_hi, alpha=0.1, color="#3498DB")
    ax2.set_xlabel("间接效应（a×b）")
    ax2.set_ylabel("频次")
    ax2.set_title(f"Bootstrap 间接效应分布\n（{n_bootstrap}次）",
                  fontsize=12, fontweight="bold", color="#2C3E50")
    ax2.legend(fontsize=10)
    ax2.spines["top"].set_visible(False)
    ax2.spines["right"].set_visible(False)
    plt.tight_layout()

    return {
        "path_a":       round(path_a_coef, 4),
        "path_b":       round(path_b_coef, 4),
        "path_c":       round(path_c_coef, 4),
        "path_c_prime": round(path_c_prime_coef, 4),
        "indirect_effect": round(indirect_effect, 4),
        "direct_effect":   round(direct, 4),
        "total_effect":    round(total, 4),
        "pct_mediated":    round(pct_mediated, 1),
        "bootstrap_ci_lo": round(ci_lo, 4),
        "bootstrap_ci_hi": round(ci_hi, 4),
        "ci_level":        ci_level,
        "conclusion": (
            f"✅ 间接效应（中介效应）显著：{indirect_effect:.4f}，"
            f"{ci_level*100:.0f}% CI=[{ci_lo:.4f}, {ci_hi:.4f}]，不含0；"
            f"中介占比 {pct_mediated:.1f}%"
            if ci_lo * ci_hi > 0
            else f"⚠️ 间接效应不显著：{ci_level*100:.0f}% CI 包含0"
        ),
    }, fig


def _estimate_paths(
    df: pd.DataFrame,
    dep_var: str,
    mediator: str,
    treatment: str,
    controls: list[str],
) -> tuple[float, float, float, float]:
    """估计中介路径系数：a, b, c（总效应）, c'（直接效应）"""
    ctrl = controls or []

    # 路径 a: X → M
    X_a = sm.add_constant(df[[treatment] + ctrl])
    a = float(sm.OLS(df[mediator], X_a).fit().params.get(treatment, np.nan))

    # 路径 b 和 c'：X + M → Y
    X_bc = sm.add_constant(df[[treatment, mediator] + ctrl])
    bc_model = sm.OLS(df[dep_var], X_bc).fit()
    b  = float(bc_model.params.get(mediator, np.nan))
    c_prime = float(bc_model.params.get(treatment, np.nan))

    # 路径 c：总效应 X → Y
    X_c = sm.add_constant(df[[treatment] + ctrl])
    c = float(sm.OLS(df[dep_var], X_c).fit().params.get(treatment, np.nan))

    return a, b, c, c_prime


def _draw_mediation_path(
    ax, path_a: float, path_b: float, path_c: float, path_c_prime: float,
    x_name: str, m_name: str, y_name: str,
) -> None:
    """在 ax 上绘制中介路径示意图"""
    ax.set_xlim(0, 10)
    ax.set_ylim(0, 8)
    ax.axis("off")

    # 节点位置
    x_pos = (1.5, 3.5)   # X
    m_pos = (5,   6.5)   # M
    y_pos = (8.5, 3.5)   # Y

    def draw_box(pos, label, color):
        from matplotlib.patches import FancyBboxPatch
        box = FancyBboxPatch((pos[0]-1.2, pos[1]-0.6), 2.4, 1.2,
                              boxstyle="round,pad=0.1",
                              linewidth=1.5, edgecolor=color,
                              facecolor="white", zorder=5)
        ax.add_patch(box)
        ax.text(pos[0], pos[1], label, ha="center", va="center",
                fontsize=11, fontweight="bold", color=color, zorder=6)

    draw_box(x_pos, x_name[:6], "#2C3E50")
    draw_box(m_pos, m_name[:6], "#3498DB")
    draw_box(y_pos, y_name[:6], "#E74C3C")

    # 路径 a: X → M
    ax.annotate("", xy=(m_pos[0]-1.3, m_pos[1]-0.3),
                xytext=(x_pos[0]+1.2, x_pos[1]+0.3),
                arrowprops=dict(arrowstyle="->", color="#3498DB", lw=2))
    ax.text((x_pos[0]+m_pos[0])/2-0.5, (x_pos[1]+m_pos[1])/2+0.3,
            f"a={path_a:.3f}", fontsize=10, color="#3498DB", fontweight="bold")

    # 路径 b: M → Y
    ax.annotate("", xy=(y_pos[0]-1.2, y_pos[1]+0.3),
                xytext=(m_pos[0]+1.2, m_pos[1]-0.3),
                arrowprops=dict(arrowstyle="->", color="#3498DB", lw=2))
    ax.text((m_pos[0]+y_pos[0])/2+0.3, (m_pos[1]+y_pos[1])/2+0.3,
            f"b={path_b:.3f}", fontsize=10, color="#3498DB", fontweight="bold")

    # 路径 c'（直接）: X → Y
    ax.annotate("", xy=(y_pos[0]-1.2, y_pos[1]),
                xytext=(x_pos[0]+1.2, x_pos[1]),
                arrowprops=dict(arrowstyle="->", color="#E74C3C", lw=2))
    ax.text(5, 2.8, f"c'={path_c_prime:.3f}（直接效应）",
            ha="center", fontsize=10, color="#E74C3C", fontweight="bold")

    ax.set_title(f"中介路径图\n总效应 c={path_c:.3f}，间接效应 a×b={path_a*path_b:.4f}",
                 fontsize=11, fontweight="bold", color="#2C3E50", pad=8)


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
