"""
首页：数据上传与预览
步骤1 - 上传数据
"""
from __future__ import annotations

import io

import pandas as pd
import streamlit as st

from core.data_loader import (
    load_dataframe,
    detect_panel_structure,
    validate_panel_data,
    generate_sample_data,
)
from i18n import t


def render_home() -> None:
    """渲染首页（步骤1：上传数据）"""
    st.markdown(
        f"""
        <div style="text-align:center; padding:2rem 0 1rem 0;">
            <h1 style="color:#2C3E50; font-size:2.5rem; margin:0;">{t("home.title")}</h1>
            <p style="color:#7F8C8D; font-size:1.1rem; margin:0.5rem 0 0 0;">
                {t("home.subtitle")}
            </p>
        </div>
        """,
        unsafe_allow_html=True,
    )

    st.divider()

    # ── 功能亮点 ──────────────────────────────────────────────────────────────
    col1, col2, col3, col4 = st.columns(4)
    col1.markdown(t("home.feature.describe"))
    col2.markdown(t("home.feature.baseline"))
    col3.markdown(t("home.feature.causal"))
    col4.markdown(t("home.feature.mechanism"))

    st.divider()

    # ── 数据上传区 ────────────────────────────────────────────────────────────
    st.markdown(t("home.step1.title"))

    tab1, tab2 = st.tabs([t("home.tab.upload"), t("home.tab.sample")])

    with tab1:
        _render_upload_section()

    with tab2:
        _render_sample_data_section()

    # ── 数据预览 ──────────────────────────────────────────────────────────────
    if st.session_state.get("df") is not None:
        _render_data_preview()


def _render_upload_section() -> None:
    """文件上传区"""
    uploaded = st.file_uploader(
        t("home.upload.label"),
        type=["csv", "xlsx", "xls"],
        help=t("home.upload.help"),
    )

    if uploaded is not None:
        with st.spinner(t("home.upload.parsing")):
            try:
                df = load_dataframe(io.BytesIO(uploaded.read()), uploaded.name)
                st.session_state["df"] = df
                st.session_state["filename"] = uploaded.name
                st.session_state["analysis_results"] = {}
                st.success(t("home.upload.success", rows=len(df), cols=len(df.columns)))
                _auto_detect_panel(df)
            except Exception as e:
                st.error(t("home.upload.error", error=str(e)))


def _render_sample_data_section() -> None:
    """示例数据区"""
    st.info(t("home.sample.info"))
    st.markdown(
        """
        | 变量 | 说明 |
        |------|------|
        | `firm_id` | 企业 ID（个体变量） |
        | `year` | 年份（时间变量） |
        | `treat` | 处理组虚拟变量（1=处理组） |
        | `post` | 政策后虚拟变量（year≥2015） |
        | `did` | DID 交乘项（treat×post） |
        | `tfp` | 全要素生产率（被解释变量） |
        | `size` | 企业规模（控制变量） |
        | `lev` | 资产负债率（控制变量） |
        | `roa` | 资产收益率（控制变量） |
        | `score` | 运行变量（用于 RDD） |
        """
    )

    col1, col2 = st.columns([1, 3])
    with col1:
        if st.button(t("home.sample.btn.load"), type="primary"):
            with st.spinner(t("home.sample.generating")):
                df = generate_sample_data()
                st.session_state["df"] = df
                st.session_state["filename"] = "data_sample.csv"
                st.session_state["analysis_results"] = {}
                st.success(t("home.sample.success", rows=len(df), cols=len(df.columns)))
                _auto_detect_panel(df)

    with col2:
        # 提供样本数据下载
        sample_df = generate_sample_data()
        csv_bytes = sample_df.to_csv(index=False, encoding="utf-8-sig").encode("utf-8-sig")
        st.download_button(
            t("home.sample.btn.download"),
            data=csv_bytes,
            file_name="data_sample.csv",
            mime="text/csv",
        )


def _auto_detect_panel(df: pd.DataFrame) -> None:
    """自动检测面板结构并存入 session"""
    panel_info = detect_panel_structure(df)
    st.session_state["panel_info"] = panel_info

    id_col = panel_info.get("id_col")
    time_col = panel_info.get("time_col")

    if id_col and time_col:
        st.info(t(
            "home.detect.info",
            id_col=id_col,
            time_col=time_col,
            n_entities=panel_info["n_entities"],
            n_periods=panel_info["n_periods"],
        ))
        validation = validate_panel_data(df, id_col, time_col)
        st.session_state["validation"] = validation

        if validation["warnings"]:
            for w in validation["warnings"]:
                st.warning(f"⚠️ {w}")
    else:
        st.warning(t("home.detect.warning"))


def _render_data_preview() -> None:
    """数据预览区"""
    df = st.session_state["df"]

    st.divider()
    st.markdown(t("home.preview.title"))

    col1, col2, col3, col4 = st.columns(4)
    col1.metric(t("home.preview.rows"), f"{len(df):,}")
    col2.metric(t("home.preview.cols"), f"{len(df.columns)}")
    numeric_count = len(df.select_dtypes(include="number").columns)
    col3.metric(t("home.preview.numeric"), f"{numeric_count}")
    missing_pct = round(df.isnull().mean().mean() * 100, 2)
    col4.metric(t("home.preview.missing"), f"{missing_pct}%")

    # 数据前 20 行
    st.dataframe(df.head(20), use_container_width=True)

    # 列信息
    with st.expander(t("home.preview.col_details")):
        col_info = pd.DataFrame({
            t("home.preview.col.name"):    df.columns,
            t("home.preview.col.type"):    [str(df[c].dtype) for c in df.columns],
            t("home.preview.col.notnull"): [df[c].count() for c in df.columns],
            t("home.preview.col.missing"): [f"{df[c].isnull().mean()*100:.1f}%" for c in df.columns],
            t("home.preview.col.unique"):  [df[c].nunique() for c in df.columns],
        })
        st.dataframe(col_info, use_container_width=True)

    # 配置面板结构
    _render_panel_config(df)


def _render_panel_config(df: pd.DataFrame) -> None:
    """面板结构配置与确认按钮（跳转到步骤2）"""
    st.markdown(t("home.panel_config.title"))
    panel_info = st.session_state.get("panel_info", {})
    all_cols = list(df.columns)

    col_a, col_b = st.columns(2)
    with col_a:
        default_id = _find_idx(all_cols, panel_info.get("id_col"))
        id_col = st.selectbox(t("home.panel_config.id"), all_cols, index=default_id, key="home_id")
    with col_b:
        default_time = _find_idx(all_cols, panel_info.get("time_col"))
        time_col = st.selectbox(t("home.panel_config.time"), all_cols, index=default_time, key="home_time")

    st.markdown("")  # 间距

    # 主行动按钮：下一步：智能引导 →
    if st.button(t("home.panel_config.next"), type="primary", key="confirm_panel"):
        validation = validate_panel_data(df, id_col, time_col)
        st.session_state["panel_info"]["id_col"] = id_col
        st.session_state["panel_info"]["time_col"] = time_col

        if validation["valid"]:
            st.success(t("home.panel_config.success"))
            # 步骤跳转：步骤1 → 步骤2
            st.session_state["step"] = 2
            st.session_state["page"] = "🤖 智能引导"
            st.rerun()
        else:
            for issue in validation["issues"]:
                st.error(f"❌ {issue}")


def _find_idx(lst: list, target) -> int:
    """在列表中找目标元素的索引，未找到返回 0"""
    try:
        return lst.index(target) if target in lst else 0
    except Exception:
        return 0
