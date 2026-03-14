"""
智能引导页：根据研究描述推荐分析方法
"""
from __future__ import annotations

import streamlit as st

from core.smart_recommender import recommend_methods, get_method_categories, MethodRecommendation


# 分类颜色映射
CATEGORY_COLORS = {
    "describe": ("#FDEBD0", "#784212"),
    "panel":    ("#D5EAF5", "#1A5276"),
    "causal":   ("#FADBD8", "#C0392B"),
    "robust":   ("#D5F5E3", "#1D8348"),
    "hetero":   ("#E8DAEF", "#6C3483"),
}

CATEGORY_LABELS = {
    "describe": "🔵 描述诊断",
    "panel":    "🟡 面板回归",
    "causal":   "🔴 因果推断",
    "robust":   "🟢 稳健性",
    "hetero":   "🟣 异质性机制",
}

PRIORITY_LABELS = {1: "🔴 必须", 2: "🟡 推荐", 3: "🟢 可选"}


def render_smart_guide() -> None:
    """渲染智能引导页"""
    st.markdown("## 🤖 智能方法推荐引擎")
    st.markdown(
        "描述您的研究背景，系统将自动推荐最合适的计量分析路径。"
    )

    st.divider()

    # ── 输入区 ────────────────────────────────────────────────────────────────
    col1, col2 = st.columns([2, 1])

    with col1:
        description = st.text_area(
            "📝 研究背景描述（中英文均可）",
            placeholder=(
                "示例：本文研究某省2015年出台的环保政策对企业全要素生产率的影响，"
                "使用2010-2020年企业面板数据，处理组与对照组在政策实施前应满足平行趋势。"
                "同时担心内生性问题，需要检验政策效果的传导机制。"
            ),
            height=150,
            key="smart_description",
        )

    with col2:
        st.markdown("**💡 关键词触发规则**")
        st.markdown(
            """
            - 政策/冲击/自然实验 → **DID**
            - 内生性/双向因果 → **IV/GMM**
            - 面板数据 → **FE/RE**
            - 断点/资格线 → **RDD**
            - 机制/路径 → **中介效应**
            - 不同群体 → **异质性**
            """
        )

    if st.button("🔍 智能推荐", type="primary", disabled=not description.strip()):
        with st.spinner("分析中..."):
            recommendations = recommend_methods(description)
            st.session_state["recommendations"] = recommendations
            st.success(f"✅ 推荐 {len(recommendations)} 种分析方法")

    st.divider()

    # ── 推荐结果展示 ─────────────────────────────────────────────────────────
    if "recommendations" in st.session_state:
        _render_recommendations(st.session_state["recommendations"])

        # 跳转按钮提到顶层，确保 rerun 生效
        st.divider()
        st.markdown("**⚡ 快速跳转到分析页面**")
        if st.button("🚀 前往实证分析", type="primary", key="goto_analysis_top"):
            st.session_state["recommended_methods"] = [
                rec.method_name for rec in st.session_state.get("recommendations", [])
            ]
            st.session_state["page"] = "📈 实证分析"
            st.rerun()

    # ── 全部方法目录 ─────────────────────────────────────────────────────────
    st.divider()
    st.markdown("## 📚 全部分析方法目录")
    _render_method_catalog()


def _render_recommendations(recommendations: list[MethodRecommendation]) -> None:
    """渲染推荐结果卡片"""
    st.markdown("### 🎯 推荐分析路径")
    st.markdown("按以下顺序执行可获得最完整的实证结果：")

    # 按优先级分组
    priority_groups: dict[int, list] = {1: [], 2: [], 3: []}
    for rec in recommendations:
        priority_groups.setdefault(rec.priority, []).append(rec)

    for priority in [1, 2, 3]:
        group = priority_groups.get(priority, [])
        if not group:
            continue

        label = PRIORITY_LABELS.get(priority, f"优先级{priority}")
        st.markdown(f"#### {label}")

        for rec in group:
            bg, text = CATEGORY_COLORS.get(rec.category, ("#F8F9FA", "#2C3E50"))
            cat_label = CATEGORY_LABELS.get(rec.category, rec.category)

            with st.container():
                st.markdown(
                    f"""
                    <div style="background:{bg}; border-left:4px solid {text};
                                padding:0.8rem 1rem; border-radius:4px; margin-bottom:0.5rem;">
                        <div style="display:flex; justify-content:space-between; align-items:center;">
                            <strong style="color:{text}; font-size:1rem;">
                                {rec.method_name}
                            </strong>
                            <span style="background:{text}; color:white;
                                         padding:2px 8px; border-radius:10px; font-size:0.8rem;">
                                {cat_label}
                            </span>
                        </div>
                        <p style="margin:0.3rem 0 0 0; color:#555; font-size:0.9rem;">
                            {rec.reason}
                        </p>
                    </div>
                    """,
                    unsafe_allow_html=True,
                )

                if rec.sub_steps:
                    with st.expander("📋 具体步骤"):
                        for i, step in enumerate(rec.sub_steps, 1):
                            st.markdown(f"{i}. {step}")

    # 跳转按钮已移到顶层渲染，此处不再重复


def _render_method_catalog() -> None:
    """渲染全部方法目录"""
    catalog = get_method_categories()

    for category, methods in catalog.items():
        with st.expander(category, expanded=False):
            cols = st.columns(3)
            for i, method in enumerate(methods):
                cols[i % 3].markdown(f"• {method['name']}")
