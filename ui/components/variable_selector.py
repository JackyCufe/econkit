"""
变量选择器组件
"""
from __future__ import annotations

from typing import Optional

import pandas as pd
import streamlit as st

from i18n import t


def select_variables(
    df: pd.DataFrame,
    key_prefix: str = "var",
    show_id_time: bool = True,
) -> dict:
    """
    通用变量选择器

    Args:
        df:          当前数据
        key_prefix:  组件 key 前缀（避免冲突）
        show_id_time: 是否展示个体/时间变量选择

    Returns: 变量选择字典
    """
    all_cols    = list(df.columns)
    numeric_cols = df.select_dtypes(include="number").columns.tolist()

    result: dict = {}

    if show_id_time:
        col1, col2 = st.columns(2)
        with col1:
            result["id_col"] = st.selectbox(
                t("var.id.label"),
                options=all_cols,
                index=_guess_index(all_cols, ["firm_id", "id", "entity", "code"]),
                key=f"{key_prefix}_id",
            )
        with col2:
            result["time_col"] = st.selectbox(
                t("var.time.label"),
                options=all_cols,
                index=_guess_index(all_cols, ["year", "time", "date", "period"]),
                key=f"{key_prefix}_time",
            )

    result["dep_var"] = st.selectbox(
        t("var.dep.label"),
        options=numeric_cols,
        index=_guess_index(numeric_cols, ["tfp", "y", "outcome", "dep"]),
        key=f"{key_prefix}_dep",
    )

    result["indep_vars"] = st.multiselect(
        t("var.indep.label"),
        options=[c for c in numeric_cols if c != result.get("dep_var")],
        default=[],
        key=f"{key_prefix}_indep",
    )

    return result


def select_did_variables(
    df: pd.DataFrame,
    key_prefix: str = "did",
) -> dict:
    """DID 专用变量选择器"""
    all_cols     = list(df.columns)
    numeric_cols = df.select_dtypes(include="number").columns.tolist()

    st.markdown(t("did.config.title"))
    col1, col2 = st.columns(2)

    with col1:
        dep_var = st.selectbox(
            t("did.dep.label"),
            numeric_cols,
            index=_guess_index(numeric_cols, ["tfp", "y", "outcome"]),
            key=f"{key_prefix}_dep",
        )
        treat_col = st.selectbox(
            t("did.treat.label"),
            all_cols,
            index=_guess_index(all_cols, ["treat", "treated", "group"]),
            key=f"{key_prefix}_treat",
        )

    with col2:
        post_col = st.selectbox(
            t("did.post.label"),
            all_cols,
            index=_guess_index(all_cols, ["post", "after", "policy"]),
            key=f"{key_prefix}_post",
        )
        did_col = st.selectbox(
            t("did.did.label"),
            all_cols,
            index=_guess_index(all_cols, ["did", "treat_post", "interaction"]),
            key=f"{key_prefix}_did",
        )

    id_col = st.selectbox(
        t("did.id.label"),
        all_cols,
        index=_guess_index(all_cols, ["firm_id", "id", "entity"]),
        key=f"{key_prefix}_id",
    )
    time_col = st.selectbox(
        t("did.time.label"),
        all_cols,
        index=_guess_index(all_cols, ["year", "time", "date"]),
        key=f"{key_prefix}_time",
    )

    treat_year = st.number_input(
        t("did.treat_year.label"),
        value=int(df[time_col].median()) if time_col in df.columns else 2015,
        step=1,
        key=f"{key_prefix}_treat_year",
    )

    controls = st.multiselect(
        t("did.controls.label"),
        [c for c in numeric_cols
         if c not in [dep_var, treat_col, post_col, did_col]],
        key=f"{key_prefix}_controls",
    )

    return {
        "dep_var":    dep_var,
        "treat_col":  treat_col,
        "post_col":   post_col,
        "did_col":    did_col,
        "id_col":     id_col,
        "time_col":   time_col,
        "treat_year": int(treat_year),
        "controls":   controls,
    }


def select_panel_variables(df: pd.DataFrame, key_prefix: str = "panel") -> dict:
    """面板回归专用变量选择器"""
    all_cols     = list(df.columns)
    numeric_cols = df.select_dtypes(include="number").columns.tolist()

    col1, col2 = st.columns(2)
    with col1:
        id_col = st.selectbox(t("panel_var.id.label"), all_cols,
                              index=_guess_index(all_cols, ["firm_id", "id"]),
                              key=f"{key_prefix}_id")
        dep_var = st.selectbox(t("panel_var.dep.label"), numeric_cols,
                               index=_guess_index(numeric_cols, ["tfp", "y"]),
                               key=f"{key_prefix}_dep")
    with col2:
        time_col = st.selectbox(t("panel_var.time.label"), all_cols,
                                index=_guess_index(all_cols, ["year", "time"]),
                                key=f"{key_prefix}_time")
        model_type = st.selectbox(
            t("panel_var.model.label"),
            ["fe（个体固定效应）", "te（时间固定效应）",
             "twfe（双向固定效应）", "re（随机效应）"],
            key=f"{key_prefix}_model",
        )

    indep_vars = st.multiselect(
        t("panel_var.indep.label"),
        [c for c in numeric_cols if c != dep_var],
        key=f"{key_prefix}_indep",
    )

    return {
        "id_col":     id_col,
        "time_col":   time_col,
        "dep_var":    dep_var,
        "indep_vars": indep_vars,
        "model_type": model_type.split("（")[0],
    }


def _guess_index(cols: list[str], candidates: list[str]) -> int:
    """猜测列名在候选列表中的最佳索引"""
    cols_lower = [c.lower() for c in cols]
    for cand in candidates:
        if cand in cols_lower:
            return cols_lower.index(cand)
    return 0
