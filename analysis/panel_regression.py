"""
面板回归模块
包含：OLS、个体FE、时间FE、双向FE（TWFE）、随机效应（RE）、
      Hausman检验、面板单位根检验、聚类/DK标准误
"""
from __future__ import annotations

import warnings
from typing import Optional

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import statsmodels.api as sm
import statsmodels.formula.api as smf
from statsmodels.stats.diagnostic import het_breuschpagan

warnings.filterwarnings("ignore")


# ── OLS 回归 ──────────────────────────────────────────────────────────────────
def run_ols(
    df: pd.DataFrame,
    dep_var: str,
    indep_vars: list[str],
    cov_type: str = "HC3",
) -> dict:
    """
    OLS 回归（含稳健标准误）

    Args:
        cov_type: "HC3"（稳健）/ "nonrobust"（普通）

    Returns: 结果字典含 model, summary_df, stats
    """
    subset = df[[dep_var] + indep_vars].dropna()
    X = sm.add_constant(subset[indep_vars], has_constant="add")
    y = subset[dep_var]
    model = sm.OLS(y, X).fit(cov_type=cov_type)

    return _extract_ols_results(model, "OLS")


def _extract_ols_results(model, name: str) -> dict:
    """从 statsmodels OLS/WLS 结果中提取标准输出"""
    params = model.params
    bse    = model.bse
    pvals  = model.pvalues
    conf   = model.conf_int()

    rows = []
    for var in params.index:
        if var == "const":
            continue
        coef = params[var]
        se   = bse[var]
        pv   = pvals[var]
        stars = "***" if pv < 0.01 else "**" if pv < 0.05 else "*" if pv < 0.1 else ""
        rows.append({
            "变量":   var,
            "系数":   round(float(coef), 4),
            "标准误": round(float(se), 4),
            "t值":    round(float(coef / se), 4),
            "p值":    round(float(pv), 4),
            "显著性": stars,
            "CI下界": round(float(conf.loc[var, 0]), 4),
            "CI上界": round(float(conf.loc[var, 1]), 4),
        })

    summary_df = pd.DataFrame(rows)

    return {
        "name":       name,
        "model":      model,
        "summary_df": summary_df,
        "stats": {
            "n_obs":    int(model.nobs),
            "r2":       round(float(model.rsquared), 4),
            "adj_r2":   round(float(model.rsquared_adj), 4),
            "f_stat":   round(float(model.fvalue), 4) if hasattr(model, "fvalue") else None,
            "f_pval":   round(float(model.f_pvalue), 4) if hasattr(model, "f_pvalue") else None,
            "aic":      round(float(model.aic), 4) if hasattr(model, "aic") else None,
            "bic":      round(float(model.bic), 4) if hasattr(model, "bic") else None,
        },
    }


# ── 面板 FE / RE / TWFE ───────────────────────────────────────────────────────
def run_panel_model(
    df: pd.DataFrame,
    dep_var: str,
    indep_vars: list[str],
    id_col: str,
    time_col: str,
    model_type: str = "fe",
    cov_type: str = "clustered",
) -> dict:
    """
    运行面板模型

    Args:
        model_type: "fe"（个体FE）/ "te"（时间FE）/ "twfe"（双向FE）/ "re"（随机效应）
        cov_type: "clustered"（聚类到id_col）/ "robust"（稳健）/ "unadjusted"

    Returns: 结果字典
    """
    from linearmodels import PanelOLS, RandomEffects

    subset = (df[[id_col, time_col, dep_var] + indep_vars]
              .dropna()
              .set_index([id_col, time_col]))

    formula = dep_var + " ~ " + " + ".join(indep_vars)

    if model_type == "fe":
        formula += " + EntityEffects"
        estimator = PanelOLS.from_formula(formula, data=subset, drop_absorbed=True)
    elif model_type == "te":
        formula += " + TimeEffects"
        estimator = PanelOLS.from_formula(formula, data=subset, drop_absorbed=True)
    elif model_type == "twfe":
        formula += " + EntityEffects + TimeEffects"
        estimator = PanelOLS.from_formula(formula, data=subset, drop_absorbed=True)
    elif model_type == "re":
        estimator = RandomEffects.from_formula(formula, data=subset)
    else:
        raise ValueError(f"未知模型类型：{model_type}")

    fit_kwargs: dict = {}
    if model_type != "re":
        if cov_type == "clustered":
            fit_kwargs = {"cov_type": "clustered", "cluster_entity": True}
        else:
            fit_kwargs = {"cov_type": "robust"}
    else:
        fit_kwargs = {"cov_type": "robust"}

    result = estimator.fit(**fit_kwargs)
    return _extract_panel_results(result, model_type.upper())


def _extract_panel_results(result, name: str) -> dict:
    """从 linearmodels 结果中提取标准输出"""
    params = result.params
    bse    = result.std_errors
    pvals  = result.pvalues
    conf   = result.conf_int()

    rows = []
    for var in params.index:
        coef = params[var]
        se   = bse[var]
        pv   = pvals[var]
        stars = "***" if pv < 0.01 else "**" if pv < 0.05 else "*" if pv < 0.1 else ""
        rows.append({
            "变量":   var,
            "系数":   round(float(coef), 4),
            "标准误": round(float(se), 4),
            "t值":    round(float(coef / se), 4),
            "p值":    round(float(pv), 4),
            "显著性": stars,
            "CI下界": round(float(conf["lower"].loc[var]), 4),
            "CI上界": round(float(conf["upper"].loc[var]), 4),
        })

    summary_df = pd.DataFrame(rows)

    return {
        "name":       name,
        "model":      result,
        "summary_df": summary_df,
        "stats": {
            "n_obs":      int(result.nobs),
            "r2_within":  round(float(result.rsquared), 4),
            "f_stat":     round(float(result.f_statistic.stat), 4)
                          if hasattr(result, "f_statistic") else None,
        },
    }


# ── Hausman 检验 ──────────────────────────────────────────────────────────────
def run_hausman_test(
    df: pd.DataFrame,
    dep_var: str,
    indep_vars: list[str],
    id_col: str,
    time_col: str,
) -> dict:
    """
    Hausman 检验（FE vs RE）
    统计量：H = (b_fe - b_re)' * (Var_fe - Var_re)^{-1} * (b_fe - b_re)

    Returns: 检验结果字典
    """
    fe_res = run_panel_model(df, dep_var, indep_vars, id_col, time_col, "fe", "robust")
    re_res = run_panel_model(df, dep_var, indep_vars, id_col, time_col, "re")

    fe_model = fe_res["model"]
    re_model = re_res["model"]

    common_vars = list(set(fe_model.params.index) & set(re_model.params.index))
    if not common_vars:
        return {"error": "FE 和 RE 无公共变量，无法进行 Hausman 检验"}

    b_fe = fe_model.params[common_vars].values
    b_re = re_model.params[common_vars].values

    V_fe = fe_model.cov[common_vars].loc[common_vars].values
    V_re = re_model.cov[common_vars].loc[common_vars].values

    diff = b_fe - b_re
    try:
        V_diff = V_fe - V_re
        H = float(diff @ np.linalg.pinv(V_diff) @ diff)
        df_chi = len(common_vars)
        from scipy.stats import chi2
        p_val = 1 - chi2.cdf(H, df=df_chi)
        conclusion = "推荐固定效应（FE）" if p_val < 0.05 else "推荐随机效应（RE）"
    except Exception as e:
        return {"error": f"Hausman 检验计算失败：{str(e)}"}

    return {
        "H统计量":     round(H, 4),
        "自由度":      df_chi,
        "p值":         round(float(p_val), 4),
        "结论":        conclusion,
        "解释":        (
            "p<0.05：个体效应与解释变量相关，FE 一致，RE 不一致，选择 FE"
            if p_val < 0.05
            else "p≥0.05：RE 效率更高，选择 RE"
        ),
    }


# ── 面板单位根检验 ─────────────────────────────────────────────────────────────
def test_panel_unit_root(
    df: pd.DataFrame,
    col: str,
    id_col: str,
    time_col: str,
) -> dict:
    """
    简化版面板单位根检验（基于 ADF 检验的汇总）
    注：完整 LLC/IPS 需要 arch 包，这里用 statsmodels ADF 做截面汇总

    Returns: 检验结果字典
    """
    from statsmodels.tsa.stattools import adfuller

    ids = df[id_col].unique()
    adf_stats: list[float] = []
    adf_pvals: list[float] = []

    for uid in ids:
        sub = df[df[id_col] == uid].sort_values(time_col)[col].dropna()
        if len(sub) < 4:
            continue
        try:
            result = adfuller(sub, autolag="AIC")
            adf_stats.append(result[0])
            adf_pvals.append(result[1])
        except Exception:
            continue

    if not adf_pvals:
        return {"error": "无法计算单位根检验（数据量不足）"}

    # IPS W统计量近似：标准化 ADF 统计量
    n_tests = len(adf_stats)
    mean_adf = np.mean(adf_stats)
    reject_pct = np.mean([p < 0.05 for p in adf_pvals]) * 100

    return {
        "检验方法":     "ADF 面板汇总（简化版）",
        "截面数":       n_tests,
        "平均ADF统计量": round(float(mean_adf), 4),
        "拒绝单位根比例": f"{reject_pct:.1f}%",
        "结论":         "序列平稳" if reject_pct > 50 else "可能存在单位根",
        "建议":         "建议对变量取一阶差分" if reject_pct <= 50 else "序列平稳，可直接使用",
    }


# ── 多模型对比表 ──────────────────────────────────────────────────────────────
def build_regression_table(
    results: list[dict],
    key_vars: Optional[list[str]] = None,
) -> pd.DataFrame:
    """
    将多个回归结果合并为学术论文风格对比表

    Args:
        results: run_ols / run_panel_model 返回的结果列表
        key_vars: 只展示这些变量（None 则展示所有）

    Returns: 对比表 DataFrame
    """
    all_vars: list[str] = []
    for r in results:
        for var in r["summary_df"]["变量"].tolist():
            if var not in all_vars:
                if key_vars is None or var in key_vars:
                    all_vars.append(var)

    rows = []
    for var in all_vars:
        coef_row: dict = {"变量": var}
        se_row:   dict = {"变量": ""}
        for r in results:
            name = r["name"]
            df_r = r["summary_df"]
            match = df_r[df_r["变量"] == var]
            if not match.empty:
                coef = match.iloc[0]["系数"]
                se   = match.iloc[0]["标准误"]
                stars = match.iloc[0]["显著性"]
                coef_row[name] = f"{coef}{stars}"
                se_row[name]   = f"({se})"
            else:
                coef_row[name] = ""
                se_row[name]   = ""
        rows.append(coef_row)
        rows.append(se_row)

    # 底部统计量
    stat_rows = []
    for stat_name, key in [("N", "n_obs"), ("R²", "r2"), ("Adj.R²", "adj_r2")]:
        stat_row: dict = {"变量": stat_name}
        for r in results:
            val = r["stats"].get(key, r["stats"].get("r2_within"))
            stat_row[r["name"]] = str(val) if val is not None else ""
        stat_rows.append(stat_row)

    all_rows = rows + stat_rows
    cols = ["变量"] + [r["name"] for r in results]
    return pd.DataFrame(all_rows, columns=cols)
