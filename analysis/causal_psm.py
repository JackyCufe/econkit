"""
PSM 倾向得分匹配模块
包含：Logit 倾向得分估计、KNN / 核匹配 / 半径匹配、平衡性检验、ATT 估计
"""
from __future__ import annotations

import warnings
from typing import Optional

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from sklearn.linear_model import LogisticRegression
from sklearn.preprocessing import StandardScaler
from sklearn.neighbors import NearestNeighbors

warnings.filterwarnings("ignore")


# ── 倾向得分估计 ──────────────────────────────────────────────────────────────
def estimate_propensity_score(
    df: pd.DataFrame,
    treat_col: str,
    covariate_cols: list[str],
) -> pd.DataFrame:
    """
    使用 Logistic 回归估计倾向得分

    Returns: 含 pscore 列的 DataFrame
    """
    subset = df[[treat_col] + covariate_cols].dropna().copy()
    X = subset[covariate_cols]
    y = subset[treat_col]

    scaler = StandardScaler()
    X_scaled = scaler.fit_transform(X)

    logit = LogisticRegression(max_iter=500, random_state=42)
    logit.fit(X_scaled, y)

    subset["pscore"] = logit.predict_proba(X_scaled)[:, 1]
    subset["pscore_logit"] = np.log(subset["pscore"] / (1 - subset["pscore"] + 1e-10))

    return subset


# ── KNN 最近邻匹配 ────────────────────────────────────────────────────────────
def knn_matching(
    df_pscore: pd.DataFrame,
    dep_var_series: pd.Series,
    treat_col: str,
    k: int = 1,
    with_replacement: bool = True,
    caliper: Optional[float] = None,
) -> dict:
    """
    K 近邻匹配，估计 ATT

    Args:
        k:               最近邻数量
        with_replacement: 是否有放回匹配
        caliper:         卡尺（倾向得分允许最大差距，None表示无限制）

    Returns: 结果字典
    """
    df = df_pscore.copy()
    df["outcome"] = dep_var_series.values

    treated   = df[df[treat_col] == 1].copy()
    control   = df[df[treat_col] == 0].copy()

    ps_treated = treated["pscore"].values.reshape(-1, 1)
    ps_control = control["pscore"].values.reshape(-1, 1)

    nn = NearestNeighbors(n_neighbors=k, metric="euclidean")
    nn.fit(ps_control)
    distances, indices = nn.kneighbors(ps_treated)

    # 应用卡尺
    matched_control_outcomes: list[float] = []
    n_matched = 0
    for i, (dists, idxs) in enumerate(zip(distances, indices)):
        if caliper is not None:
            valid_idxs = [idx for idx, d in zip(idxs, dists) if d <= caliper]
        else:
            valid_idxs = list(idxs)

        if valid_idxs:
            matched_outcomes = control.iloc[valid_idxs]["outcome"].mean()
            matched_control_outcomes.append(matched_outcomes)
            n_matched += 1
        else:
            matched_control_outcomes.append(np.nan)

    treated["matched_outcome"] = matched_control_outcomes
    treated_clean = treated.dropna(subset=["matched_outcome"])

    att = float((treated_clean["outcome"] - treated_clean["matched_outcome"]).mean())
    att_se = float((treated_clean["outcome"] - treated_clean["matched_outcome"]).std()
                   / np.sqrt(len(treated_clean)))
    t_stat = att / (att_se + 1e-10)
    from scipy import stats
    p_val = 2 * (1 - stats.t.cdf(abs(t_stat), df=len(treated_clean) - 1))

    return {
        "method":      "KNN 匹配",
        "k":           k,
        "att":         round(att, 4),
        "att_se":      round(att_se, 4),
        "t_stat":      round(t_stat, 4),
        "p_value":     round(float(p_val), 4),
        "n_treated":   len(treated),
        "n_matched":   n_matched,
        "stars":       "***" if p_val < 0.01 else "**" if p_val < 0.05 else "*" if p_val < 0.1 else "",
        "matched_df":  treated_clean,
    }


# ── 核匹配 ───────────────────────────────────────────────────────────────────
def kernel_matching(
    df_pscore: pd.DataFrame,
    dep_var_series: pd.Series,
    treat_col: str,
    bandwidth: float = 0.06,
) -> dict:
    """
    高斯核匹配，估计 ATT

    Args:
        bandwidth: 核函数带宽

    Returns: 结果字典
    """
    df = df_pscore.copy()
    df["outcome"] = dep_var_series.values

    treated = df[df[treat_col] == 1].copy()
    control = df[df[treat_col] == 0].copy()

    att_contributions: list[float] = []
    for _, row in treated.iterrows():
        ps_diff = control["pscore"] - row["pscore"]
        # 高斯核权重
        weights = np.exp(-0.5 * (ps_diff / bandwidth) ** 2)
        weights /= weights.sum() + 1e-10
        counterfactual = (weights * control["outcome"]).sum()
        att_contributions.append(float(row["outcome"]) - counterfactual)

    att_arr = np.array(att_contributions)
    att    = float(att_arr.mean())
    att_se = float(att_arr.std() / np.sqrt(len(att_arr)))
    t_stat = att / (att_se + 1e-10)
    from scipy import stats
    p_val  = 2 * (1 - stats.t.cdf(abs(t_stat), df=len(att_arr) - 1))

    return {
        "method":    "核匹配",
        "bandwidth": bandwidth,
        "att":       round(att, 4),
        "att_se":    round(att_se, 4),
        "t_stat":    round(t_stat, 4),
        "p_value":   round(float(p_val), 4),
        "n_treated": len(treated),
        "stars":     "***" if p_val < 0.01 else "**" if p_val < 0.05 else "*" if p_val < 0.1 else "",
    }


# ── 平衡性检验 ────────────────────────────────────────────────────────────────
def check_covariate_balance(
    df_before: pd.DataFrame,
    df_after_treated: pd.DataFrame,
    df_after_control: pd.DataFrame,
    treat_col: str,
    covariate_cols: list[str],
) -> tuple[pd.DataFrame, plt.Figure]:
    """
    匹配前后协变量平衡性检验（标准化偏差 SMD）

    Returns: (平衡性检验表, 图)
    """
    def smd(g1: pd.Series, g2: pd.Series) -> float:
        """标准化均值差（SMD）"""
        mu1, mu2 = g1.mean(), g2.mean()
        s1, s2   = g1.std(), g2.std()
        pooled   = np.sqrt((s1**2 + s2**2) / 2 + 1e-10)
        return float((mu1 - mu2) / pooled * 100)  # 百分比

    treated_before = df_before[df_before[treat_col] == 1]
    control_before = df_before[df_before[treat_col] == 0]

    rows = []
    smd_before_list: list[float] = []
    smd_after_list:  list[float] = []

    for cov in covariate_cols:
        sb = smd(treated_before[cov], control_before[cov])
        sa = smd(df_after_treated[cov], df_after_control[cov])
        smd_before_list.append(sb)
        smd_after_list.append(sa)
        rows.append({
            "协变量": cov,
            "匹配前SMD(%)": round(sb, 2),
            "匹配后SMD(%)": round(sa, 2),
            "平衡性改善": "✅" if abs(sa) < 10 else "⚠️",
        })

    balance_df = pd.DataFrame(rows)

    # 绘制 Love 图
    fig, ax = plt.subplots(figsize=(10, max(6, len(covariate_cols) * 0.5 + 2)))
    y_pos = np.arange(len(covariate_cols))

    ax.scatter(smd_before_list, y_pos, color="#E74C3C", s=80,
               zorder=5, label="匹配前", marker="o")
    ax.scatter(smd_after_list,  y_pos, color="#2C3E50", s=80,
               zorder=5, label="匹配后", marker="s")

    for i, (sb, sa) in enumerate(zip(smd_before_list, smd_after_list)):
        ax.plot([sb, sa], [i, i], color="gray", alpha=0.4, linewidth=1)

    ax.axvline(10,  color="#E74C3C", linestyle=":", linewidth=1.2,
               alpha=0.7, label="10% 阈值")
    ax.axvline(-10, color="#E74C3C", linestyle=":", linewidth=1.2, alpha=0.7)
    ax.axvline(0,   color="gray", linestyle="--", linewidth=0.8)

    ax.set_yticks(y_pos)
    ax.set_yticklabels(covariate_cols, fontsize=10)
    ax.set_xlabel("标准化均值差（SMD %）")
    ax.set_title("协变量平衡性检验（Love 图）\nSMD<10% 为满足平衡",
                 fontsize=12, fontweight="bold", color="#2C3E50")
    ax.legend(fontsize=10)
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)
    plt.tight_layout()

    return balance_df, fig


# ── PSM 分布图 ────────────────────────────────────────────────────────────────
def plot_psm_distributions(
    df_pscore: pd.DataFrame,
    treat_col: str,
) -> plt.Figure:
    """绘制匹配前倾向得分分布图"""
    fig, axes = plt.subplots(1, 2, figsize=(12, 5))

    treated = df_pscore[df_pscore[treat_col] == 1]["pscore"]
    control = df_pscore[df_pscore[treat_col] == 0]["pscore"]

    # 直方图
    ax = axes[0]
    ax.hist(control.values, bins=40, alpha=0.6, color="#2C3E50",
            density=True, label="对照组", edgecolor="white")
    ax.hist(treated.values, bins=40, alpha=0.6, color="#E74C3C",
            density=True, label="处理组", edgecolor="white")
    ax.set_xlabel("倾向得分")
    ax.set_ylabel("密度")
    ax.set_title("倾向得分分布", fontsize=12, fontweight="bold", color="#2C3E50")
    ax.legend()
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)

    # 箱线图
    ax2 = axes[1]
    ax2.boxplot([control.values, treated.values],
                labels=["对照组", "处理组"],
                patch_artist=True,
                boxprops=dict(facecolor="#EBF5FB", color="#2C3E50"),
                medianprops=dict(color="#E74C3C", linewidth=2))
    ax2.set_ylabel("倾向得分")
    ax2.set_title("倾向得分箱线图", fontsize=12, fontweight="bold", color="#2C3E50")
    ax2.spines["top"].set_visible(False)
    ax2.spines["right"].set_visible(False)

    plt.suptitle("PSM 倾向得分诊断", fontsize=13, fontweight="bold",
                 color="#2C3E50", y=1.01)
    plt.tight_layout()
    return fig
