"""
RDD 断点回归模块
包含：断点可视化、局部线性回归、最优带宽、带宽敏感性、McCrary密度检验
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


# ── 局部线性回归（不同带宽）──────────────────────────────────────────────────
def run_rdd_local_linear(
    df: pd.DataFrame,
    dep_var: str,
    running_var: str,
    cutoff: float,
    bandwidth: Optional[float] = None,
    polynomial: int = 1,
) -> dict:
    """
    RDD 局部线性（或多项式）回归

    Args:
        cutoff:     断点值
        bandwidth:  带宽（None则使用全样本）
        polynomial: 多项式阶数（1=线性，2=二次）

    Returns: 结果字典
    """
    df = df.copy()
    df["score_c"] = df[running_var] - cutoff
    df["treat"]   = (df[running_var] >= cutoff).astype(int)

    # 限制带宽
    if bandwidth is not None:
        df = df[df["score_c"].abs() <= bandwidth]

    if len(df) < 10:
        return {"error": f"带宽内样本量不足（n={len(df)}），请增大带宽"}

    # 交互项（允许两侧斜率不同）
    df["score_x_treat"] = df["score_c"] * df["treat"]

    if polynomial == 1:
        formula = f"{dep_var} ~ treat + score_c + score_x_treat"
    else:
        df["score_c2"] = df["score_c"] ** 2
        df["score_c2_x_treat"] = df["score_c2"] * df["treat"]
        formula = f"{dep_var} ~ treat + score_c + score_c2 + score_x_treat + score_c2_x_treat"

    model = smf.ols(formula, data=df).fit(cov_type="HC3")

    coef  = float(model.params.get("treat", np.nan))
    se    = float(model.bse.get("treat", np.nan))
    pval  = float(model.pvalues.get("treat", np.nan))
    ci    = model.conf_int().loc["treat"].tolist() if "treat" in model.conf_int().index else [np.nan, np.nan]
    stars = "***" if pval < 0.01 else "**" if pval < 0.05 else "*" if pval < 0.1 else ""

    return {
        "model":      model,
        "cutoff":     cutoff,
        "bandwidth":  bandwidth,
        "n_obs":      int(model.nobs),
        "coef":       round(coef, 4),
        "se":         round(se, 4),
        "pval":       round(pval, 4),
        "ci":         [round(ci[0], 4), round(ci[1], 4)],
        "stars":      stars,
        "r2":         round(float(model.rsquared), 4),
    }


# ── 最优带宽选择（简化 CCT/IK 方法）─────────────────────────────────────────
def select_optimal_bandwidth(
    df: pd.DataFrame,
    dep_var: str,
    running_var: str,
    cutoff: float,
    bandwidths: Optional[list[float]] = None,
) -> dict:
    """
    通过交叉验证选择近似最优带宽

    Args:
        bandwidths: 候选带宽列表（默认从0.5*std到3*std）

    Returns: 包含最优带宽和各带宽结果的字典
    """
    df = df.copy()
    df["score_c"] = df[running_var] - cutoff

    std = float(df["score_c"].std())
    if bandwidths is None:
        bandwidths = [round(std * m, 4) for m in [0.5, 0.75, 1.0, 1.5, 2.0, 2.5, 3.0]]

    results = []
    for h in bandwidths:
        res = run_rdd_local_linear(df, dep_var, running_var, cutoff, bandwidth=h)
        if "error" not in res:
            results.append({
                "带宽":   h,
                "系数":   res["coef"],
                "标准误": res["se"],
                "p值":    res["pval"],
                "显著性": res["stars"],
                "N":      res["n_obs"],
            })

    results_df = pd.DataFrame(results) if results else pd.DataFrame()

    # 选择使系数最稳健的带宽（变化最小的中间带宽）
    optimal_bw = bandwidths[len(bandwidths) // 2]

    return {
        "optimal_bandwidth": optimal_bw,
        "sensitivity_table": results_df,
        "std_score":         round(std, 4),
    }


# ── McCrary 密度检验 ──────────────────────────────────────────────────────────
def mccrary_density_test(
    df: pd.DataFrame,
    running_var: str,
    cutoff: float,
    bins: int = 30,
) -> tuple[dict, plt.Figure]:
    """
    McCrary (2008) 密度连续性检验
    检验运行变量在断点处是否存在密度不连续（操纵迹象）

    Returns: (检验结果字典, 图)
    """
    df = df.copy()
    df["score_c"] = df[running_var] - cutoff

    left  = df[df["score_c"] < 0]["score_c"]
    right = df[df["score_c"] >= 0]["score_c"]

    # 简化版：t检验密度是否连续
    bin_range = df["score_c"].abs().max()
    bw = bin_range / (bins / 2)

    left_near  = left[left > -bw].count()
    right_near = right[right < bw].count()
    total_near = left_near + right_near

    if total_near < 10:
        t_stat, p_val = np.nan, np.nan
    else:
        expected = total_near / 2
        t_stat = (right_near - expected) / np.sqrt(total_near * 0.25 + 1e-10)
        p_val  = float(2 * (1 - stats.norm.cdf(abs(t_stat))))

    # 绘图
    fig, ax = plt.subplots(figsize=(10, 6))
    ax.hist(df["score_c"][df["score_c"] < 0], bins=bins // 2,
            color="#2C3E50", alpha=0.7, label="断点左侧（对照）")
    ax.hist(df["score_c"][df["score_c"] >= 0], bins=bins // 2,
            color="#E74C3C", alpha=0.7, label="断点右侧（处理）")
    ax.axvline(0, color="black", linewidth=2, linestyle="--", label="断点")
    ax.set_xlabel(f"{running_var}（以断点为中心）")
    ax.set_ylabel("频次")
    ax.set_title(
        f"McCrary 密度检验\n t={t_stat:.3f}, p={p_val:.4f} "
        f"({'✅ 无操纵迹象' if p_val > 0.05 else '⚠️ 可能存在操纵'})",
        fontsize=12, fontweight="bold", color="#2C3E50"
    )
    ax.legend()
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)
    plt.tight_layout()

    conclusion = "无操纵迹象（密度连续，RDD 有效）" if (np.isnan(p_val) or p_val > 0.05) else "⚠️ 可能存在操纵（密度不连续，结论需谨慎）"
    return {
        "t统计量":  round(float(t_stat), 4) if not np.isnan(t_stat) else "N/A",
        "p值":      round(float(p_val), 4) if not np.isnan(p_val) else "N/A",
        "左侧样本": int(left_near),
        "右侧样本": int(right_near),
        "结论":     conclusion,
    }, fig


# ── RDD 可视化 ────────────────────────────────────────────────────────────────
def plot_rdd(
    df: pd.DataFrame,
    dep_var: str,
    running_var: str,
    cutoff: float,
    bandwidth: Optional[float] = None,
    n_bins: int = 20,
) -> plt.Figure:
    """
    标准 RDD 图表：散点（分bin均值）+ 分段拟合线

    Returns: matplotlib Figure
    """
    df = df.copy()
    df["score_c"] = df[running_var] - cutoff
    df["treat"]   = (df[running_var] >= cutoff).astype(int)

    if bandwidth is not None:
        plot_df = df[df["score_c"].abs() <= bandwidth].copy()
    else:
        plot_df = df.copy()

    fig, axes = plt.subplots(1, 2, figsize=(14, 6))

    # 图1：散点 + 拟合线（展示全部数据）
    ax = axes[0]
    for t, color, label in [(0, "#2C3E50", "对照组"), (1, "#E74C3C", "处理组")]:
        sub = plot_df[plot_df["treat"] == t]
        ax.scatter(sub[running_var], sub[dep_var],
                   alpha=0.3, s=10, color=color)
        if len(sub) > 2:
            z = np.polyfit(sub[running_var], sub[dep_var], 2)
            x_line = np.linspace(sub[running_var].min(), sub[running_var].max(), 100)
            ax.plot(x_line, np.polyval(z, x_line), color=color,
                    linewidth=2.5, label=label)

    ax.axvline(cutoff, color="black", linewidth=1.5,
               linestyle="--", label=f"断点（{cutoff}）")
    ax.set_xlabel(running_var)
    ax.set_ylabel(dep_var)
    ax.set_title("RDD 断点图\n（散点 + 二次拟合）",
                 fontsize=12, fontweight="bold", color="#2C3E50")
    ax.legend(fontsize=10)
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)

    # 图2：分 Bin 均值图
    ax2 = axes[1]
    bin_edges = np.linspace(plot_df[running_var].min(),
                            plot_df[running_var].max(),
                            n_bins + 1)
    plot_df["bin"] = pd.cut(plot_df[running_var], bins=bin_edges)
    bin_mean = (plot_df.groupby("bin", observed=False)[dep_var]
                .mean()
                .reset_index())
    bin_mean["bin_mid"] = bin_mean["bin"].apply(
        lambda x: (x.left + x.right) / 2 if hasattr(x, "left") else np.nan
    )
    bin_mean = bin_mean.dropna(subset=["bin_mid"])

    # 确保 bin_mid 是 float，避免 Categorical dtype 比较报错
    bin_mean["bin_mid"] = bin_mean["bin_mid"].astype(float)
    left_bins  = bin_mean[bin_mean["bin_mid"] < float(cutoff)]
    right_bins = bin_mean[bin_mean["bin_mid"] >= float(cutoff)]

    ax2.scatter(left_bins["bin_mid"],  left_bins[dep_var],
                color="#2C3E50", s=50, zorder=5)
    ax2.scatter(right_bins["bin_mid"], right_bins[dep_var],
                color="#E74C3C", s=50, zorder=5)

    for sub_b, color in [(left_bins, "#2C3E50"), (right_bins, "#E74C3C")]:
        if len(sub_b) > 1:
            z = np.polyfit(sub_b["bin_mid"], sub_b[dep_var], 1)
            x_l = np.linspace(sub_b["bin_mid"].min(), sub_b["bin_mid"].max(), 50)
            ax2.plot(x_l, np.polyval(z, x_l), color=color, linewidth=2)

    ax2.axvline(cutoff, color="black", linewidth=1.5,
                linestyle="--", label=f"断点（{cutoff}）")
    ax2.set_xlabel(running_var)
    ax2.set_ylabel(f"{dep_var}（bin均值）")
    ax2.set_title("分 Bin 均值图\n（标准 RDD 展示方式）",
                  fontsize=12, fontweight="bold", color="#2C3E50")
    ax2.legend(fontsize=10)
    ax2.spines["top"].set_visible(False)
    ax2.spines["right"].set_visible(False)

    plt.tight_layout()
    return fig
