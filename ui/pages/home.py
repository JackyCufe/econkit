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
    # 注入 CSS：数据预览区预留最小高度，防止加载后大块内容突然跳出（减少 CLS）
    st.markdown(
        """
        <style>
        .ek-data-preview { min-height: 300px; }
        </style>
        """,
        unsafe_allow_html=True,
    )

    st.markdown(
        f"""
        <div style="text-align:center; padding:2rem 0 1rem 0;">
            <h1 style="color:#2C3E50; font-size:2.5rem; margin:0;">{t("home_title")}</h1>
            <p style="color:#7F8C8D; font-size:1.1rem; margin:0.5rem 0 0 0;">
                {t("home_subtitle")}
            </p>
        </div>
        """,
        unsafe_allow_html=True,
    )

    st.divider()

    # ── 功能亮点 ──────────────────────────────────────────────────────────────
    col1, col2, col3, col4 = st.columns(4)
    col1.markdown(t("home_feature_desc"))
    col2.markdown(t("home_feature_panel"))
    col3.markdown(t("home_feature_causal"))
    col4.markdown(t("home_feature_hetero"))

    st.divider()

    # ── 数据上传区 ────────────────────────────────────────────────────────────
    st.markdown(t("home_step1_title"))

    tab1, tab2 = st.tabs([t("home_tab_upload"), t("home_tab_sample")])

    with tab1:
        _render_upload_section()

    with tab2:
        _render_sample_data_section()

    # ── 数据预览：divider + metric 行始终渲染，防止从无到有的高度跳变 ──────────
    st.divider()
    df = st.session_state.get("df")
    col1, col2, col3, col4 = st.columns(4)
    if df is not None:
        numeric_count = len(df.select_dtypes(include="number").columns)
        missing_pct = round(df.isnull().mean().mean() * 100, 2)
        col1.metric(t("home_preview_rows"),    f"{len(df):,}")
        col2.metric(t("home_preview_cols"),    f"{len(df.columns)}")
        col3.metric(t("home_preview_numeric"), f"{numeric_count}")
        col4.metric(t("home_preview_missing"), f"{missing_pct}%")
        _render_data_preview_detail(df)
    else:
        col1.metric(t("home_preview_rows"),    "—")
        col2.metric(t("home_preview_cols"),    "—")
        col3.metric(t("home_preview_numeric"), "—")
        col4.metric(t("home_preview_missing"), "—")


# @st.fragment  # disabled: requires streamlit>=1.37
def _render_upload_section() -> None:
    """文件上传区（fragment：上传后局部刷新，不触发全页 reflow → 减少 CLS）"""
    uploaded = st.file_uploader(
        t("home_upload_label"),
        type=["csv", "xlsx", "xls"],
        help=t("home_upload_help"),
    )

    if uploaded is not None:
        with st.spinner(t("home_upload_parsing")):
            try:
                df = load_dataframe(io.BytesIO(uploaded.read()), uploaded.name)
                st.session_state["df"] = df
                st.session_state["filename"] = uploaded.name
                st.session_state["analysis_results"] = {}
                st.success(t("home_upload_success", rows=len(df), cols=len(df.columns)))
                _auto_detect_panel(df)
                # scope="app" 让外层感知到 df 已更新
                st.rerun()  # was scope="app"
            except Exception as e:
                st.error(t("home_upload_error", error=str(e)))


# @st.fragment  # disabled: requires streamlit>=1.37
def _render_sample_data_section() -> None:
    """示例数据区（fragment：加载时只重渲染本区域，不触发整页 reflow → 减少 CLS）"""
    st.info(t("home_sample_info"))
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
        if st.button(t("home_sample_btn_load"), type="primary"):
            with st.spinner(t("home_sample_generating")):
                df = generate_sample_data()
                st.session_state["df"] = df
                st.session_state["filename"] = "data_sample.csv"
                st.session_state["analysis_results"] = {}
                _auto_detect_panel(df)
            # scope="app" 从 fragment 内触发全页刷新，让外层 _render_data_preview 感知到 df
            st.rerun()  # was scope="app"

    with col2:
        # 提供样本数据下载
        sample_df = generate_sample_data()
        csv_bytes = sample_df.to_csv(index=False, encoding="utf-8-sig").encode("utf-8-sig")
        st.download_button(
            t("home_sample_btn_download"),
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
        st.info(
            t(
                "home_detect_info",
                id_col=id_col,
                time_col=time_col,
                n_entities=panel_info["n_entities"],
                n_periods=panel_info["n_periods"],
            )
        )
        validation = validate_panel_data(df, id_col, time_col)
        st.session_state["validation"] = validation

        if validation["warnings"]:
            for w in validation["warnings"]:
                st.warning(f"⚠️ {w}")
    else:
        st.warning(t("home_detect_warning"))


def _render_data_preview() -> None:
    """数据预览区（兼容旧调用，内部调用 detail）"""
    df = st.session_state["df"]
    st.divider()
    col1, col2, col3, col4 = st.columns(4)
    numeric_count = len(df.select_dtypes(include="number").columns)
    missing_pct = round(df.isnull().mean().mean() * 100, 2)
    col1.metric(t("home_preview_rows"), f"{len(df):,}")
    col2.metric(t("home_preview_cols"), f"{len(df.columns)}")
    col3.metric(t("home_preview_numeric"), f"{numeric_count}")
    col4.metric(t("home_preview_missing"), f"{missing_pct}%")
    _render_data_preview_detail(df)


def _render_data_preview_detail(df) -> None:
    """数据预览详情（divider + metric 已在外层渲染）"""
    st.markdown(t("home_data_preview_title"))

    # 数据前 20 行
    st.dataframe(df.head(20), use_container_width=True)

    # 列信息
    with st.expander(t("home_preview_col_details")):
        col_info = pd.DataFrame({
            t("home_preview_col_name"):    df.columns,
            t("home_preview_col_type"):    [str(df[c].dtype) for c in df.columns],
            t("home_preview_col_notnull"): [df[c].count() for c in df.columns],
            t("home_preview_col_missing"): [f"{df[c].isnull().mean()*100:.1f}%" for c in df.columns],
            t("home_preview_col_unique"):  [df[c].nunique() for c in df.columns],
        })
        st.dataframe(col_info, use_container_width=True)

    # 配置面板结构
    _render_panel_config(df)


def _render_panel_config(df: pd.DataFrame) -> None:
    """面板结构配置与确认按钮（跳转到步骤2）"""
    st.markdown(t("home_panel_config_title"))
    panel_info = st.session_state.get("panel_info", {})
    all_cols = list(df.columns)

    col_a, col_b = st.columns(2)
    with col_a:
        default_id = _find_idx(all_cols, panel_info.get("id_col"))
        id_col = st.selectbox(t("home_panel_config_id"), all_cols, index=default_id, key="home_id")
    with col_b:
        default_time = _find_idx(all_cols, panel_info.get("time_col"))
        time_col = st.selectbox(t("home_panel_config_time"), all_cols, index=default_time, key="home_time")

    st.markdown("")  # 间距

    # 主行动按钮：下一步：智能引导 →
    if st.button(t("home_panel_config_next"), type="primary", key="confirm_panel"):
        validation = validate_panel_data(df, id_col, time_col)
        st.session_state["panel_info"]["id_col"] = id_col
        st.session_state["panel_info"]["time_col"] = time_col

        if validation["valid"]:
            st.success(t("home_panel_config_success"))
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
