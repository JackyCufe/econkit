"""
中介效应分析模块
包含：Bootstrap 中介效应（Baron-Kenny 框架）
（从 heterogeneity.py 拆分出，逻辑不变）
"""
from __future__ import annotations

from typing import Optional, Callable

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import statsmodels.api as sm

import warnings
warnings.filterwarnings("ignore")


def run_mediation_analysis(
    df: pd.DataFrame,
    dep_var: str,
    mediator: str,
    treatment: str,
    controls: Optional[list[str]] = None,
    n_bootstrap: int = 1000,
    ci_level: float = 0.95,
    progress_callback: Optional[Callable[[float], None]] = None,
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
    for i in range(n_bootstrap):
        boot_df = subset.sample(n=len(subset), replace=True, random_state=None)
        a, b, c, c_p = _estimate_paths(boot_df, dep_var, mediator, treatment, controls)
        indirect_boot.append(a * b)
        if progress_callback and (i + 1) % max(1, n_bootstrap // 50) == 0:
            progress_callback((i + 1) / n_bootstrap)

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
