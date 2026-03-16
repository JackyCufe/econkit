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


# ── 动态面板 GMM (Arellano-Bond / Blundell-Bond) ──────────────────────────────
def run_dynamic_panel_gmm(
    df: pd.DataFrame,
    dep_var: str,
    indep_vars: list[str],
    id_col: str,
    time_col: str,
    gmm_type: str = "difference",
    lags: int = 1,
    iv_lags_min: int = 2,
    iv_lags_max: int = 4,
    collapse: bool = False,
    timedumm: bool = False,
    fod: bool = False,
) -> dict:
    """
    动态面板 GMM，使用 pydynpd 实现真正的 Arellano-Bond / Blundell-Bond 估计。

    Args:
        gmm_type:    "difference"（差分GMM，Arellano-Bond）
                     "system"（系统GMM，Blundell-Bond）
        lags:        被解释变量滞后阶数（默认1阶）
        iv_lags_min: GMM工具变量滞后起始期（默认2）
        iv_lags_max: GMM工具变量滞后终止期（默认4）
        collapse:    是否折叠工具变量矩阵（避免instrument proliferation）
        timedumm:    是否加入时间虚拟变量
        fod:         是否使用前向正交偏差变换（代替一阶差分）

    Returns:
        结果字典，含 summary_df / stats / ar_tests / hansen / gmm_type
    """
    try:
        from pydynpd import regression as pydynpd_reg
    except ImportError:
        return {"error": "pydynpd 未安装，请运行 pip install pydynpd"}

    try:
        df = df.copy().sort_values([id_col, time_col]).reset_index(drop=True)

        # 构建 pydynpd 命令字符串
        lag_terms = f"L(1:{lags}).{dep_var}" if lags > 1 else f"L(1:1).{dep_var}"
        controls_str = " ".join(indep_vars)
        iv_str = f"gmm({dep_var}, {iv_lags_min}:{iv_lags_max})"
        exog_iv_str = f"iv({controls_str})" if indep_vars else ""

        options_parts = []
        if gmm_type == "difference":
            options_parts.append("nolevel")
        if collapse:
            options_parts.append("collapse")
        if timedumm:
            options_parts.append("timedumm")
        if fod:
            options_parts.append("fod")

        options_str = " ".join(options_parts)
        parts = [
            f"{dep_var} {lag_terms} {controls_str}",
            f"{iv_str} {exog_iv_str}".strip(),
        ]
        if options_str:
            parts.append(options_str)

        command_str = " | ".join(parts)
        method_name = (
            f"差分GMM（Arellano-Bond，L{lags}，工具变量L{iv_lags_min}:{iv_lags_max}）"
            if gmm_type == "difference"
            else f"系统GMM（Blundell-Bond，L{lags}，工具变量L{iv_lags_min}:{iv_lags_max}）"
        )

        result = pydynpd_reg.abond(command_str, df, [id_col, time_col])
        model = result.models[0]
        reg_table: pd.DataFrame = model.regression_table

        # 提取系数表
        rows = []
        for _, row in reg_table.iterrows():
            pv = float(row["p_value"])
            stars = "***" if pv < 0.01 else "**" if pv < 0.05 else "*" if pv < 0.1 else ""
            rows.append({
                "变量":   str(row["variable"]),
                "系数":   round(float(row["coefficient"]), 4),
                "标准误": round(float(row["std_err"]), 4),
                "z值":    round(float(row["z_value"]), 4),
                "p值":    round(pv, 4),
                "显著性": stars,
            })
        summary_df = pd.DataFrame(rows)

        # AR 检验
        ar_tests = []
        for ar in model.AR_list:
            ar_tests.append({
                "阶数": ar.lag,
                "z统计量": round(float(ar.AR), 4),
                "p值": round(float(ar.P_value), 4),
                "结论": (
                    "AR(1)显著（正常）" if ar.lag == 1 and ar.P_value < 0.05
                    else "AR(2)不显著（扰动项无序列相关，GMM有效）" if ar.lag == 2 and ar.P_value >= 0.1
                    else "AR(2)显著（扰动项可能存在序列相关，需检查模型）" if ar.lag == 2
                    else f"p={ar.P_value:.4f}"
                ),
            })

        # Hansen 检验
        h = model.hansen
        hansen_result = {
            "chi2统计量": round(float(h.test_value), 4),
            "自由度":     int(h.df),
            "p值":        round(float(h.p_value), 4),
            "结论": (
                "✅ Hansen检验通过（p≥0.1）：工具变量外生性不被拒绝"
                if h.p_value >= 0.1
                else "⚠️ Hansen检验未通过（p<0.1）：工具变量可能存在过度识别问题，考虑减少IV数量或使用collapse选项"
            ),
        }

        return {
            "name":         method_name,
            "gmm_type":     gmm_type,
            "command_str":  command_str,
            "summary_df":   summary_df,
            "stats": {
                "n_obs":          int(model.num_obs),
                "n_groups":       int(model.N),
                "n_instruments":  int(model.z_information.num_instr),
            },
            "ar_tests":     ar_tests,
            "hansen":       hansen_result,
            "ar_note": (
                "✅ 使用 pydynpd 实现真正的 Arellano-Bond / Blundell-Bond GMM，"
                "包含 Windmeijer(2005) 有限样本校正标准误、Hansen过度识别检验、AR(1)/AR(2)序列相关检验。"
            ),
        }

    except Exception as e:
        return {"error": f"GMM 估计失败：{str(e)}"}


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
