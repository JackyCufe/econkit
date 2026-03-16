"""
动态面板 GMM 模块
包含：Arellano-Bond / Blundell-Bond 差分GMM、系统GMM
（从 panel_regression.py 拆分出，逻辑不变）
"""
from __future__ import annotations

import pandas as pd


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

        command_str = " ".join(parts)
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
