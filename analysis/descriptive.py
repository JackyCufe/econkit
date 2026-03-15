"""
描述统计与诊断检验模块
包含：描述统计、相关矩阵、正态性检验、VIF、异方差检验、自相关检验
"""
from __future__ import annotations

import warnings
from typing import Optional

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from scipy import stats


warnings.filterwarnings("ignore")


# ── 描述统计 ──────────────────────────────────────────────────────────────────
def compute_descriptive_stats(
    df: pd.DataFrame,
    cols: Optional[list[str]] = None,
) -> pd.DataFrame:
    """
    计算描述统计表，含均值/标准差/分位数/偏度/峰度

    Returns: 描述统计 DataFrame，行为变量，列为统计量
    """
    if cols is None:
        cols = df.select_dtypes(include=np.number).columns.tolist()

    subset = df[cols].dropna()
    stats_dict: dict[str, list] = {
        "变量": cols,
        "观测数": [int(subset[c].count()) for c in cols],
        "均值":   [round(subset[c].mean(), 4) for c in cols],
        "标准差": [round(subset[c].std(), 4) for c in cols],
        "最小值": [round(subset[c].min(), 4) for c in cols],
        "P25":    [round(subset[c].quantile(0.25), 4) for c in cols],
        "中位数": [round(subset[c].median(), 4) for c in cols],
        "P75":    [round(subset[c].quantile(0.75), 4) for c in cols],
        "最大值": [round(subset[c].max(), 4) for c in cols],
        "偏度":   [round(float(subset[c].skew()), 4) for c in cols],
        "峰度":   [round(float(subset[c].kurt()), 4) for c in cols],
    }
    return pd.DataFrame(stats_dict).set_index("变量")


def plot_descriptive_stats(
    df: pd.DataFrame,
    cols: list[str],
) -> plt.Figure:
    """绘制变量分布直方图 + 核密度图"""
    n = len(cols)
    ncols = min(3, n)
    nrows = (n + ncols - 1) // ncols
    fig, axes = plt.subplots(nrows, ncols, figsize=(5 * ncols, 4 * nrows))
    if n == 1:
        axes = [axes]
    else:
        axes = np.array(axes).flatten()

    for i, col in enumerate(cols):
        ax = axes[i]
        data = df[col].dropna()
        ax.hist(data, bins=30, alpha=0.6, color="#2C3E50", density=True)
        data.plot.kde(ax=ax, color="#E74C3C", linewidth=2)
        ax.set_title(f"{col} 分布", fontsize=11, color="#2C3E50")
        ax.set_xlabel(col)
        ax.set_ylabel("密度")
        ax.spines["top"].set_visible(False)
        ax.spines["right"].set_visible(False)

    # 隐藏多余子图
    for j in range(i + 1, len(axes)):
        axes[j].set_visible(False)

    plt.suptitle("变量分布图", fontsize=13, fontweight="bold",
                 color="#2C3E50", y=1.01)
    plt.tight_layout()
    return fig


# ── 相关矩阵 ──────────────────────────────────────────────────────────────────
def compute_correlation_matrix(
    df: pd.DataFrame,
    cols: list[str],
    method: str = "pearson",
) -> tuple[pd.DataFrame, pd.DataFrame]:
    """
    计算相关矩阵及 p 值矩阵

    Returns: (corr_matrix, pvalue_matrix)
    """
    subset = df[cols].dropna()
    corr = subset.corr(method=method).round(4)

    n = len(subset)
    pvals = pd.DataFrame(index=cols, columns=cols, dtype=float)
    for c1 in cols:
        for c2 in cols:
            if c1 == c2:
                pvals.loc[c1, c2] = 0.0
            else:
                if method == "pearson":
                    _, p = stats.pearsonr(subset[c1], subset[c2])
                else:
                    _, p = stats.spearmanr(subset[c1], subset[c2])
                pvals.loc[c1, c2] = round(p, 4)

    return corr, pvals


def plot_correlation_matrix(
    corr: pd.DataFrame,
    pvals: pd.DataFrame,
) -> plt.Figure:
    """绘制带显著性标注的热力图"""
    fig, ax = plt.subplots(figsize=(10, 8))

    mask = np.triu(np.ones_like(corr, dtype=bool), k=1)
    sns.heatmap(
        corr, annot=True, fmt=".3f", cmap="RdYlBu_r",
        vmin=-1, vmax=1, center=0, ax=ax,
        mask=mask, square=True, linewidths=0.5,
        cbar_kws={"shrink": 0.8},
    )

    # 标注显著性星号
    for i, c1 in enumerate(corr.columns):
        for j, c2 in enumerate(corr.index):
            if i > j:  # 下三角
                p = pvals.loc[c2, c1]
                stars = "***" if p < 0.01 else "**" if p < 0.05 else "*" if p < 0.1 else ""
                if stars:
                    ax.text(i + 0.5, j + 0.85, stars,
                            ha="center", va="center",
                            fontsize=8, color="#E74C3C", fontweight="bold")

    ax.set_title("相关矩阵（下三角显著性：***p<0.01，**p<0.05，*p<0.1）",
                 fontsize=12, fontweight="bold", color="#2C3E50", pad=12)
    plt.tight_layout()
    return fig


# ── 正态性检验 ────────────────────────────────────────────────────────────────
def test_normality(
    df: pd.DataFrame,
    cols: list[str],
) -> pd.DataFrame:
    """
    Shapiro-Wilk 和 Jarque-Bera 正态性检验

    Returns: 检验结果 DataFrame
    """
    results = []
    for col in cols:
        data = df[col].dropna().values
        if len(data) < 3:
            continue

        # Shapiro-Wilk（适合小样本 n<5000）
        if len(data) <= 5000:
            sw_stat, sw_p = stats.shapiro(data)
        else:
            sw_stat, sw_p = np.nan, np.nan

        # Jarque-Bera（适合大样本）
        jb_stat, jb_p = stats.jarque_bera(data)

        results.append({
            "变量":       col,
            "SW统计量":   round(float(sw_stat), 4) if not np.isnan(sw_stat) else "N/A",
            "SW p值":     round(float(sw_p), 4) if not np.isnan(sw_p) else "N/A",
            "SW结论":     "正态" if (not np.isnan(sw_p) and sw_p > 0.05) else "非正态",
            "JB统计量":   round(float(jb_stat), 4),
            "JB p值":     round(float(jb_p), 4),
            "JB结论":     "正态" if jb_p > 0.05 else "非正态",
        })

    return pd.DataFrame(results)


# ── VIF 多重共线性 ─────────────────────────────────────────────────────────────
def compute_vif(
    df: pd.DataFrame,
    cols: list[str],
) -> pd.DataFrame:
    """
    计算方差膨胀因子 (VIF)

    Returns: VIF 结果 DataFrame
    """
    from statsmodels.stats.outliers_influence import variance_inflation_factor
    import statsmodels.api as sm

    subset = df[cols].dropna()
    X = sm.add_constant(subset)

    vif_results = []
    for i, col in enumerate(subset.columns):
        vif_val = variance_inflation_factor(X.values, i + 1)
        conclusion = ("极高" if vif_val > 10
                      else "较高" if vif_val > 5
                      else "正常")
        vif_results.append({
            "变量":    col,
            "VIF":     round(float(vif_val), 4),
            "结论":    conclusion,
        })

    return pd.DataFrame(vif_results)


# ── 异方差检验 ────────────────────────────────────────────────────────────────
def test_heteroskedasticity(
    df: pd.DataFrame,
    dep_var: str,
    indep_vars: list[str],
) -> dict:
    """
    Breusch-Pagan 和 White 异方差检验

    Returns: 检验结果字典
    """
    import statsmodels.api as sm
    from statsmodels.stats.diagnostic import het_breuschpagan, het_white

    subset = df[[dep_var] + indep_vars].dropna()
    X = sm.add_constant(subset[indep_vars])
    y = subset[dep_var]
    model = sm.OLS(y, X).fit()
    resid = model.resid

    # Breusch-Pagan
    bp_lm, bp_p, bp_f, bp_fp = het_breuschpagan(resid, X)

    # White
    try:
        wh_lm, wh_p, wh_f, wh_fp = het_white(resid, X)
        white_result = {
            "LM统计量": round(float(wh_lm), 4),
            "p值":      round(float(wh_p), 4),
            "结论":     "存在异方差" if wh_p < 0.05 else "无显著异方差",
        }
    except Exception:
        white_result = {"LM统计量": "N/A", "p值": "N/A", "结论": "无法计算"}

    return {
        "breusch_pagan": {
            "LM统计量": round(float(bp_lm), 4),
            "p值":      round(float(bp_p), 4),
            "结论":     "存在异方差" if bp_p < 0.05 else "无显著异方差",
        },
        "white": white_result,
        "recommendation": (
            "建议使用稳健标准误（HC3）或 GLS 估计" if bp_p < 0.05
            else "同方差假设成立，OLS 标准误可靠"
        ),
    }


# ── 自相关检验 ────────────────────────────────────────────────────────────────
def test_autocorrelation(
    df: pd.DataFrame,
    dep_var: str,
    indep_vars: list[str],
    id_col: Optional[str] = None,
    time_col: Optional[str] = None,
) -> dict:
    """
    Durbin-Watson 自相关检验（时序/面板）

    Returns: 检验结果字典
    """
    import statsmodels.api as sm
    from statsmodels.stats.stattools import durbin_watson

    subset = df[[dep_var] + indep_vars].dropna()
    X = sm.add_constant(subset[indep_vars])
    y = subset[dep_var]
    model = sm.OLS(y, X).fit()
    resid = model.resid

    dw = durbin_watson(resid)
    if dw < 1.5:
        conclusion = "正自相关（DW < 1.5）"
    elif dw > 2.5:
        conclusion = "负自相关（DW > 2.5）"
    else:
        conclusion = "无显著自相关（1.5 < DW < 2.5）"

    return {
        "durbin_watson": {
            "统计量": round(float(dw), 4),
            "结论":   conclusion,
        },
        "recommendation": (
            "建议使用 Newey-West HAC 标准误或 Driscoll-Kraay 标准误"
            if dw < 1.5 or dw > 2.5
            else "自相关不显著，OLS 标准误可靠"
        ),
    }
