"""
工具变量 IV / 2SLS 模块
包含：2SLS估计、弱工具变量检验、Wu-Hausman内生性检验、Sargan过度识别检验
"""
from __future__ import annotations

import warnings
from typing import Optional

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import statsmodels.api as sm
from scipy import stats

warnings.filterwarnings("ignore")


# ── 2SLS 主函数 ───────────────────────────────────────────────────────────────
def run_iv_2sls(
    df: pd.DataFrame,
    dep_var: str,
    endog_var: str,
    instruments: list[str],
    exog_controls: Optional[list[str]] = None,
    id_col: Optional[str] = None,
    time_col: Optional[str] = None,
    panel_effects: str = "none",
) -> dict:
    """
    IV / 2SLS 估计

    Args:
        dep_var:       被解释变量
        endog_var:     内生变量
        instruments:   工具变量列表
        exog_controls: 外生控制变量
        panel_effects: "none" / "entity" / "twfe"

    Returns: 结果字典（含第一阶段、第二阶段、检验统计量）
    """
    from linearmodels import IV2SLS

    controls = exog_controls or []
    all_cols = [dep_var, endog_var] + instruments + controls
    if id_col and time_col:
        all_cols = [id_col, time_col] + all_cols

    subset = df[all_cols].dropna()

    if id_col and time_col and panel_effects != "none":
        subset = subset.set_index([id_col, time_col])

    # 第一阶段（OLS，用于弱工具变量检验）
    X_first = sm.add_constant(subset[instruments + controls])
    y_first = subset[endog_var]
    first_stage = sm.OLS(y_first, X_first).fit()
    f_stat_first = _compute_first_stage_f(first_stage, instruments)

    # 2SLS 估计
    endog_df    = subset[[endog_var]]
    instrument_df = subset[instruments]
    exog_df     = sm.add_constant(subset[controls]) if controls else sm.add_constant(pd.Series(1, index=subset.index, name="const"))

    model = IV2SLS(
        dependent=subset[dep_var],
        exog=exog_df,
        endog=endog_df,
        instruments=instrument_df,
    )
    result = model.fit(cov_type="robust")

    # 提取系数
    coef   = float(result.params.get(endog_var, np.nan))
    se     = float(result.std_errors.get(endog_var, np.nan))
    pval   = float(result.pvalues.get(endog_var, np.nan))
    stars  = "***" if pval < 0.01 else "**" if pval < 0.05 else "*" if pval < 0.1 else ""

    # 内生性检验（Wu-Hausman）
    wu_hausman = _wu_hausman_test(subset, dep_var, endog_var, instruments, controls)

    # Sargan 过度识别检验（仅当工具变量数 > 内生变量数）
    sargan = _sargan_test(result) if len(instruments) > 1 else {"note": "恰好识别，无需Sargan检验"}

    return {
        "model":          result,
        "coef":           round(coef, 4),
        "se":             round(se, 4),
        "pval":           round(pval, 4),
        "stars":          stars,
        "n_obs":          int(result.nobs),
        "first_stage_f":  round(float(f_stat_first), 4),
        "weak_iv_pass":   f_stat_first > 10,
        "wu_hausman":     wu_hausman,
        "sargan":         sargan,
        "first_stage_r2": round(float(first_stage.rsquared), 4),
    }


def _compute_first_stage_f(
    first_stage_model,
    instruments: list[str],
) -> float:
    """计算第一阶段 F 统计量（仅对工具变量联合检验）"""
    try:
        f_test = first_stage_model.f_test(
            [f"({inst} = 0)" for inst in instruments]
        )
        return float(f_test.fvalue)
    except Exception:
        return float(first_stage_model.fvalue) if hasattr(first_stage_model, "fvalue") else 0.0


def _wu_hausman_test(
    df: pd.DataFrame,
    dep_var: str,
    endog_var: str,
    instruments: list[str],
    controls: list[str],
) -> dict:
    """
    Wu-Hausman 内生性检验
    原理：第一阶段残差作为附加控制变量，检验其显著性
    """
    X_first = sm.add_constant(df[instruments + controls])
    first   = sm.OLS(df[endog_var], X_first).fit()
    resid_first = first.resid

    df_aug = df.copy()
    df_aug["resid_first"] = resid_first.values

    X_aug = sm.add_constant(df_aug[[endog_var] + controls + ["resid_first"]])
    aug   = sm.OLS(df_aug[dep_var], X_aug).fit(cov_type="HC3")

    pval = float(aug.pvalues.get("resid_first", np.nan))
    fval = float(aug.tvalues.get("resid_first", np.nan)) ** 2

    return {
        "F统计量": round(fval, 4),
        "p值":     round(pval, 4),
        "结论": (
            "存在内生性（p<0.05），OLS 估计有偏，IV 估计一致"
            if pval < 0.05
            else "内生性不显著（p≥0.05），OLS 与 IV 估计均可"
        ),
    }


def _sargan_test(result) -> dict:
    """
    Sargan 过度识别检验
    从 linearmodels IV2SLS 结果中提取
    """
    try:
        j_stat = result.j_stat
        return {
            "J统计量": round(float(j_stat.stat), 4),
            "p值":     round(float(j_stat.pval), 4),
            "结论": (
                "过度识别检验通过（p≥0.05），工具变量有效"
                if j_stat.pval >= 0.05
                else "⚠️ 过度识别检验失败（p<0.05），工具变量可能无效"
            ),
        }
    except Exception:
        return {"note": "无法计算 Sargan 检验"}


# ── 动态面板 GMM（已移除，请使用 panel_regression.run_dynamic_panel_gmm）──────
# run_gmm_panel 原实现存在逻辑错误（将 diff_dep 同时作为 dependent 和 endog 传入），
# 且功能与 panel_regression.run_dynamic_panel_gmm 重复，故删除。
# UI 层统一调用 panel_regression.run_dynamic_panel_gmm。


# ── IV 结果可视化 ─────────────────────────────────────────────────────────────
def plot_iv_diagnostics(
    result_ols: dict,
    result_iv: dict,
    var_name: str,
) -> plt.Figure:
    """对比 OLS 与 IV 估计结果，可视化内生性偏误"""
    fig, axes = plt.subplots(1, 2, figsize=(12, 5))

    # 系数对比
    ax = axes[0]
    methods = ["OLS", "IV/2SLS"]
    coefs   = [result_ols.get("did_coef", 0), result_iv.get("coef", 0)]
    cis_lo  = [result_ols.get("did_ci", [0, 0])[0] if "did_ci" in result_ols
                else coefs[0] - 0.05,
                coefs[1] - result_iv.get("se", 0.05) * 1.96]
    cis_hi  = [result_ols.get("did_ci", [0, 0])[1] if "did_ci" in result_ols
                else coefs[0] + 0.05,
                coefs[1] + result_iv.get("se", 0.05) * 1.96]

    colors = ["#2C3E50", "#E74C3C"]
    for i, (method, coef, lo, hi, c) in enumerate(zip(methods, coefs, cis_lo, cis_hi, colors)):
        ax.barh(i, coef, color=c, alpha=0.7, height=0.5)
        ax.errorbar(coef, i, xerr=[[coef - lo], [hi - coef]],
                    fmt="none", color="black", capsize=6, linewidth=2)
        ax.text(max(coef, hi) + 0.005, i,
                f"{coef:.4f}", va="center", ha="left", fontsize=10)

    ax.set_yticks(range(len(methods)))
    ax.set_yticklabels(methods, fontsize=11)
    ax.axvline(0, color="gray", linestyle="--", linewidth=0.8)
    ax.set_title(f"OLS vs IV 系数对比\n（{var_name}）",
                 fontsize=12, fontweight="bold", color="#2C3E50")
    ax.set_xlabel("估计系数")
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)

    # 诊断统计量
    ax2 = axes[1]
    ax2.axis("off")
    iv = result_iv
    diag_text = [
        ["检验项目", "统计量", "结论"],
        ["第一阶段 F", f"{iv.get('first_stage_f', 'N/A'):.4f}",
         "✅ 强工具" if iv.get("weak_iv_pass") else "⚠️ 弱工具"],
        ["Wu-Hausman", f"p={iv.get('wu_hausman', {}).get('p值', 'N/A')}",
         iv.get("wu_hausman", {}).get("结论", "N/A")[:15] + "..."],
        ["Sargan", f"p={iv.get('sargan', {}).get('p值', 'N/A')}",
         iv.get("sargan", {}).get("结论", "N/A")[:15] + "..."],
    ]

    from matplotlib.patches import FancyBboxPatch
    y_pos = 0.9
    for row_i, row in enumerate(diag_text):
        x_positions = [0.05, 0.4, 0.65]
        for col_j, (cell, x) in enumerate(zip(row, x_positions)):
            weight = "bold" if row_i == 0 else "normal"
            color  = "#2C3E50" if row_i == 0 else "#333333"
            ax2.text(x, y_pos, str(cell), transform=ax2.transAxes,
                     fontsize=9, fontweight=weight, color=color, va="top")
        y_pos -= 0.18

    ax2.set_title("IV 诊断检验汇总", fontsize=12, fontweight="bold",
                  color="#2C3E50", pad=12)

    plt.tight_layout()
    return fig
