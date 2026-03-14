"""
侧边栏导航组件
"""
from __future__ import annotations

import streamlit as st


def render_sidebar() -> str:
    """
    渲染侧边栏导航

    Returns: 当前选中的页面名称
    """
    with st.sidebar:
        st.markdown(
            """
            <div style="text-align:center; padding:1rem 0;">
                <h2 style="color:#2C3E50; margin:0;">📊 EconKit</h2>
                <p style="color:#7F8C8D; font-size:0.85rem; margin:4px 0 0 0;">
                    计量经济学实证分析工具
                </p>
            </div>
            """,
            unsafe_allow_html=True,
        )
        st.divider()

        page = st.radio(
            "🧭 导航",
            options=["🏠 首页", "🤖 智能引导", "📈 实证分析", "📄 下载报告"],
            label_visibility="collapsed",
        )

        st.divider()

        # 数据状态提示
        if "df" in st.session_state and st.session_state["df"] is not None:
            df = st.session_state["df"]
            st.success(f"✅ 已加载数据\n{len(df)} 行 × {len(df.columns)} 列")
        else:
            st.info("💡 请先上传数据")

        st.divider()
        st.markdown(
            """
            <div style="color:#95A5A6; font-size:0.75rem; text-align:center;">
                <p>EconKit v1.0.0</p>
                <p>适用于经管类硕博研究</p>
            </div>
            """,
            unsafe_allow_html=True,
        )

    return page
