"""
稳健性检验模块
包含：Winsorize 缩尾、替换变量、安慰剂检验、Bootstrap、剔除特殊样本
"""
from __future__ import annotations

import warnings
from typing import Optional, Callable

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import statsmodels.api as sm

warnings.filterwarnings("ignore")


# ── Winsorize 缩尾处理 ───────────────────────────────────────────────────────
def winsorize_variables(
    df: pd.DataFrame,
    cols: list[str],
    pct: float = 0.01,
) -> pd.DataFrame:
    """
    对指定列进行 Winsorize 缩尾处理

    Args:
        pct: 双侧缩尾比例（0.01 = 1%~99%）

    Returns: 缩尾后的 DataFrame
    """
    if not 0 < pct < 0.5:
        raise ValueError(f"缩尾比例应在 (0, 0.5) 范围内，当前：{pct}")

    df = df.copy()
    for col in cols:
        if col in df.columns and pd.api.types.is_numeric_dtype(df[col]):
            lo = df[col].quantile(pct)
            hi = df[col].quantile(1 - pct)
            df[col] = df[col].clip(lo, hi)
    return df


# ── 替换核心变量稳健性 ────────────────────────────────────────────────────────
def replace_key_variable(
    df: pd.DataFrame,
    dep_var: str,
    alt_dep_var: str,
    indep_vars: list[str],
    base_coef_col: str,
    cov_type: str = "HC3",
) -> dict:
    """
    用替换的被解释变量重新回归，检验稳健性

    Returns: 包含替换回归结果的字典
    """
    subset = df[[alt_dep_var] + indep_vars].dropna()
    X = sm.add_constant(subset[indep_vars], has_constant="add")
    y = subset[alt_dep_var]
    model = sm.OLS(y, X).fit(cov_type=cov_type)

    if base_coef_col in model.params:
        coef  = round(float(model.params[base_coef_col]), 4)
        se    = round(float(model.bse[base_coef_col]), 4)
        pval  = round(float(model.pvalues[base_coef_col]), 4)
        stars = "***" if pval < 0.01 else "**" if pval < 0.05 else "*" if pval < 0.1 else ""
    else:
        coef, se, pval, stars = None, None, None, ""

    return {
        "alt_dep_var":  alt_dep_var,
        "coef":         coef,
        "se":           se,
        "pval":         pval,
        "stars":        stars,
        "n_obs":        int(model.nobs),
        "r2":           round(float(model.rsquared), 4),
        "model":        model,
    }


# ── Bootstrap 自助法 ─────────────────────────────────────────────────────────
def bootstrap_confidence_interval(
    df: pd.DataFrame,
    dep_var: str,
    indep_vars: list[str],
    key_var: str,
    n_bootstrap: int = 1000,
    ci_level: float = 0.95,
    id_col: Optional[str] = None,
    cluster_bootstrap: bool = False,
) -> tuple[dict, plt.Figure]:
    """
    Bootstrap 自助法置信区间

    Args:
        key_var:            关注的核心变量
        cluster_bootstrap:  是否按个体（id_col）聚类 Bootstrap

    Returns: (结果字典, 分布图)
    """
    rng = np.random.default_rng(42)
    subset = df[[dep_var] + indep_vars + ([id_col] if id_col else [])].dropna()

    boot_coefs: list[float] = []

    for _ in range(n_bootstrap):
        if cluster_bootstrap and id_col:
            ids = subset[id_col].unique()
            sampled_ids = rng.choice(ids, size=len(ids), replace=True)
            boot_df = pd.concat(
                [subset[subset[id_col] == uid] for uid in sampled_ids],
                ignore_index=True,
            )
        else:
            boot_df = subset.sample(n=len(subset), replace=True, random_state=None)

        X = sm.add_constant(boot_df[indep_vars], has_constant="add")
        y = boot_df[dep_var]
        try:
            coef = sm.OLS(y, X).fit().params.get(key_var, np.nan)
            boot_coefs.append(float(coef))
        except Exception:
            continue

    boot_arr = np.array([c for c in boot_coefs if not np.isnan(c)])

    alpha = 1 - ci_level
    ci_lo = float(np.percentile(boot_arr, alpha / 2 * 100))
    ci_hi = float(np.percentile(boot_arr, (1 - alpha / 2) * 100))
    mean  = float(boot_arr.mean())
    se    = float(boot_arr.std())

    # 绘图
    fig, ax = plt.subplots(figsize=(10, 6))
    ax.hist(boot_arr, bins=50, alpha=0.7, color="#2C3E50",
            edgecolor="white", linewidth=0.5, label="Bootstrap 分布")
    ax.axvline(mean, color="#E74C3C", linewidth=2,
               label=f"均值 = {mean:.4f}")
    ax.axvline(ci_lo, color="#3498DB", linewidth=1.5, linestyle="--",
               label=f"{ci_level*100:.0f}% CI 下界 = {ci_lo:.4f}")
    ax.axvline(ci_hi, color="#3498DB", linewidth=1.5, linestyle="--",
               label=f"{ci_level*100:.0f}% CI 上界 = {ci_hi:.4f}")
    ax.axvspan(ci_lo, ci_hi, alpha=0.1, color="#3498DB")

    ax.set_xlabel(f"{key_var} 系数")
    ax.set_ylabel("频次")
    ax.set_title(f"Bootstrap 置信区间（{n_bootstrap}次，{ci_level*100:.0f}% CI）",
                 fontsize=12, fontweight="bold", color="#2C3E50")
    ax.legend(fontsize=10)
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)
    plt.tight_layout()

    return {
        "n_bootstrap": n_bootstrap,
        "mean":        round(mean, 4),
        "se":          round(se, 4),
        "ci_lo":       round(ci_lo, 4),
        "ci_hi":       round(ci_hi, 4),
        "ci_level":    ci_level,
        "conclusion":  (
            f"✅ {key_var} 系数的 {ci_level*100:.0f}% Bootstrap CI 为 [{ci_lo:.4f}, {ci_hi:.4f}]，"
            + ("不含 0，效应显著" if ci_lo * ci_hi > 0 else "包含 0，效应不显著")
        ),
    }, fig


# ── 剔除特殊样本稳健性 ────────────────────────────────────────────────────────
def exclude_special_samples(
    df: pd.DataFrame,
    dep_var: str,
    indep_vars: list[str],
    key_var: str,
    exclude_conditions: list[dict],
    cov_type: str = "HC3",
) -> pd.DataFrame:
    """
    依次剔除特殊样本，检验结果稳健性

    Args:
        exclude_conditions: 剔除条件列表，每个元素为：
            {"label": str, "query": str}  # pandas query 表达式

    Returns: 稳健性对比表 DataFrame
    """
    rows = []

    # 基准回归（完整样本）
    base = _run_simple_ols(df, dep_var, indep_vars, key_var, cov_type)
    base["剔除条件"] = "基准（全样本）"
    rows.append(base)

    for cond in exclude_conditions:
        label = cond.get("label", "未命名")
        query = cond.get("query", "")
        try:
            sub_df = df.query(f"not ({query})")
            res = _run_simple_ols(sub_df, dep_var, indep_vars, key_var, cov_type)
            res["剔除条件"] = label
            rows.append(res)
        except Exception as e:
            rows.append({
                "剔除条件": label,
                "系数": "错误", "标准误": "", "p值": "", "显著性": "", "N": "",
            })

    return pd.DataFrame(rows)[["剔除条件", "系数", "标准误", "p值", "显著性", "N"]]


def _run_simple_ols(
    df: pd.DataFrame,
    dep_var: str,
    indep_vars: list[str],
    key_var: str,
    cov_type: str = "HC3",
) -> dict:
    """内部辅助：运行简单 OLS 并提取关键系数"""
    subset = df[[dep_var] + indep_vars].dropna()
    X = sm.add_constant(subset[indep_vars], has_constant="add")
    y = subset[dep_var]
    model = sm.OLS(y, X).fit(cov_type=cov_type)

    coef  = model.params.get(key_var, np.nan)
    se    = model.bse.get(key_var, np.nan)
    pval  = model.pvalues.get(key_var, np.nan)
    stars = "***" if pval < 0.01 else "**" if pval < 0.05 else "*" if pval < 0.1 else ""

    return {
        "系数":   round(float(coef), 4) if not np.isnan(coef) else "N/A",
        "标准误": round(float(se), 4) if not np.isnan(se) else "N/A",
        "p值":    round(float(pval), 4) if not np.isnan(pval) else "N/A",
        "显著性": stars,
        "N":      int(model.nobs),
    }
