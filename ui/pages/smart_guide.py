"""
智能引导页：根据研究描述推荐分析方法
步骤2 - 智能引导
"""
from __future__ import annotations

import streamlit as st

from core.smart_recommender import recommend_methods, get_method_categories, MethodRecommendation
from i18n import t


# 分类颜色映射
CATEGORY_COLORS: dict[str, tuple[str, str]] = {
    "describe": ("#FDEBD0", "#784212"),
    "panel":    ("#D5EAF5", "#1A5276"),
    "causal":   ("#FADBD8", "#C0392B"),
    "robust":   ("#D5F5E3", "#1D8348"),
    "hetero":   ("#E8DAEF", "#6C3483"),
}

CATEGORY_LABEL_KEYS: dict[str, str] = {
    "describe": "guide.category.describe",
    "panel":    "guide.category.panel",
    "causal":   "guide.category.causal",
    "robust":   "guide.category.robust",
    "hetero":   "guide.category.hetero",
}

PRIORITY_LABEL_KEYS: dict[int, str] = {
    1: "guide.priority.1",
    2: "guide.priority.2",
    3: "guide.priority.3",
}


def render_smart_guide() -> None:
    """渲染智能引导页（步骤2）"""
    st.markdown(t("guide.title"))
    st.markdown(t("guide.subtitle"))

    st.divider()

    # ── 输入区 ────────────────────────────────────────────────────────────────
    col1, col2 = st.columns([2, 1])

    with col1:
        description = st.text_area(
            t("guide.input.label"),
            placeholder=t("guide.input.placeholder"),
            height=150,
            key="smart_description",
        )

    with col2:
        st.markdown(t("guide.keywords.title"))
        st.markdown(t("guide.keywords.content"))

    if st.button(t("guide.btn.recommend"), type="primary", disabled=not description.strip()):
        with st.spinner(t("guide.recommending")):
            recommendations = recommend_methods(description)
            st.session_state["recommendations"] = recommendations
            st.success(t("guide.recommend.success", n=len(recommendations)))

    st.divider()

    # ── 推荐结果 + 跳转按钮 ───────────────────────────────────────────────────
    recommendations = st.session_state.get("recommendations", [])
    if recommendations:
        _render_recommendations(recommendations)

        st.divider()
        # 主行动按钮：开始实证分析 →
        col_btn, col_tip = st.columns([1, 3])
        with col_btn:
            if st.button(t("guide.btn.start_analysis"), type="primary", key="goto_analysis"):
                st.session_state["recommended_methods"] = [
                    rec.method_name for rec in recommendations
                ]
                # 步骤跳转：步骤2 → 步骤3
                st.session_state["step"] = 3
                st.session_state["page"] = "📈 实证分析"
                st.rerun()
        with col_tip:
            st.info(t("guide.tip.methods_saved"))

    # ── 全部方法目录 ─────────────────────────────────────────────────────────
    st.divider()
    st.markdown(t("guide.catalog.title"))
    _render_method_catalog()


def _render_recommendations(recommendations: list[MethodRecommendation]) -> None:
    """渲染推荐结果卡片（每个方法一张卡，含优先级标签）"""
    st.markdown(t("guide.results.title"))
    st.markdown(t("guide.results.subtitle"))

    # 按优先级分组
    priority_groups: dict[int, list[MethodRecommendation]] = {1: [], 2: [], 3: []}
    for rec in recommendations:
        priority_groups.setdefault(rec.priority, []).append(rec)

    for priority in [1, 2, 3]:
        group = priority_groups.get(priority, [])
        if not group:
            continue

        label = t(PRIORITY_LABEL_KEYS.get(priority, f"guide.priority.{priority}"))
        st.markdown(f"#### {label}")

        for rec in group:
            _render_method_card(rec)


def _render_method_card(rec: MethodRecommendation) -> None:
    """渲染单个方法推荐卡片"""
    bg, text = CATEGORY_COLORS.get(rec.category, ("#F8F9FA", "#2C3E50"))
    cat_label = t(CATEGORY_LABEL_KEYS.get(rec.category, "guide.category.describe"))
    priority_badge = t(PRIORITY_LABEL_KEYS.get(rec.priority, "guide.priority.3"))

    with st.container():
        st.markdown(
            f"""
            <div style="
                background:{bg};
                border-left:4px solid {text};
                padding:1rem 1.2rem;
                border-radius:8px;
                margin-bottom:0.8rem;
                box-shadow:0 1px 3px rgba(0,0,0,0.06);
            ">
                <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:0.4rem;">
                    <strong style="color:{text}; font-size:1.05rem;">
                        {rec.method_name}
                    </strong>
                    <div style="display:flex; gap:6px;">
                        <span style="
                            background:{text}; color:white;
                            padding:2px 10px; border-radius:12px; font-size:0.78rem;
                        ">{cat_label}</span>
                        <span style="
                            background:rgba(0,0,0,0.08); color:{text};
                            padding:2px 10px; border-radius:12px; font-size:0.78rem;
                        ">{priority_badge}</span>
                    </div>
                </div>
                <p style="margin:0; color:#555; font-size:0.9rem; line-height:1.5;">
                    {rec.reason}
                </p>
            </div>
            """,
            unsafe_allow_html=True,
        )

        if rec.sub_steps:
            with st.expander(t("guide.sub_steps.expander")):
                for i, step in enumerate(rec.sub_steps, 1):
                    st.markdown(f"{i}. {step}")


def _render_method_catalog() -> None:
    """渲染全部方法目录"""
    catalog = get_method_categories()

    for category, methods in catalog.items():
        with st.expander(category, expanded=False):
            cols = st.columns(3)
            for i, method in enumerate(methods):
                cols[i % 3].markdown(f"• {method['name']}")
