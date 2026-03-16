"""
侧边栏导航组件（辅助导航，主导航为顶部步骤条）
"""
from __future__ import annotations

import streamlit as st
from i18n import t


def render_sidebar() -> str:
    """
    渲染侧边栏导航

    Returns: 当前选中的页面名称
    """
    with st.sidebar:
        st.markdown(
            f"""
            <div style="text-align:center; padding:1rem 0;">
                <h2 style="color:#2C3E50; margin:0;">📊 EconKit</h2>
                <p style="color:#7F8C8D; font-size:0.85rem; margin:4px 0 0 0;">
                    {t("sidebar.subtitle")}
                </p>
            </div>
            """,
            unsafe_allow_html=True,
        )
        st.divider()

        # 步骤进度提示
        current_step = st.session_state.get("step", 1)
        step_labels = {
            1: t("sidebar.step_label.1"),
            2: t("sidebar.step_label.2"),
            3: t("sidebar.step_label.3"),
            4: t("sidebar.step_label.4"),
        }
        st.caption(t("sidebar.current_step", label=step_labels.get(current_step, t("sidebar.step_label.1"))))

        _options = ["🏠 首页", "🤖 智能引导", "📈 实证分析", "📄 下载报告"]
        _current = st.session_state.get("page", "🏠 首页")
        _index = _options.index(_current) if _current in _options else 0

        page = st.radio(
            t("sidebar.nav_label"),
            options=_options,
            index=_index,
            label_visibility="collapsed",
        )

        st.divider()

        # 数据状态提示
        if "df" in st.session_state and st.session_state["df"] is not None:
            df = st.session_state["df"]
            st.success(t("sidebar.data_loaded", rows=len(df), cols=len(df.columns)))
        else:
            st.info(t("sidebar.no_data"))

        # 分析进度提示
        analysis_results = st.session_state.get("analysis_results", {})
        if analysis_results:
            st.caption(t("sidebar.analysis_done", n=len(analysis_results)))

        st.divider()
        st.markdown(
            f"""
            <div style="color:#95A5A6; font-size:0.75rem; text-align:center;">
                <p>{t("sidebar.version")}</p>
                <p>{t("sidebar.desc")}</p>
            </div>
            """,
            unsafe_allow_html=True,
        )

    return page
