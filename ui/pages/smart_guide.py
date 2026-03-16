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

# 分类标签 key 映射（动态获取）
CATEGORY_KEY_MAP: dict[str, str] = {
    "describe": "guide_category_describe",
    "panel":    "guide_category_panel",
    "causal":   "guide_category_causal",
    "robust":   "guide_category_robust",
    "hetero":   "guide_category_hetero",
}

# 优先级 key 映射（动态获取）
PRIORITY_KEY_MAP: dict[int, str] = {
    1: "guide_priority_must",
    2: "guide_priority_suggest",
    3: "guide_priority_optional",
}


def render_smart_guide() -> None:
    """渲染智能引导页（步骤2）"""
    st.markdown(t("guide_title"))
    st.markdown(t("guide_subtitle"))

    st.divider()

    # ── 输入区 ────────────────────────────────────────────────────────────────
    col1, col2 = st.columns([2, 1])

    with col1:
        description = st.text_area(
            t("guide_input_label"),
            placeholder=t("guide_input_placeholder"),
            height=150,
            key="smart_description",
        )

    with col2:
        st.markdown(t("guide_keywords_title"))
        st.markdown(t("guide_keywords_content"))

    if st.button(t("guide_btn_recommend"), type="primary", disabled=not description.strip()):
        with st.spinner(t("guide_recommending")):
            recommendations = recommend_methods(description)
            st.session_state["recommendations"] = recommendations
            st.success(t("guide_recommend_success", n=len(recommendations)))

    st.divider()

    # ── 推荐结果 ─────────────────────────────────────────────────────────────
    recommendations = st.session_state.get("recommendations", [])
    if recommendations:
        _render_recommendations(recommendations)
        st.divider()

    # ── 手动选择分析方法 ──────────────────────────────────────────────────────
    _render_manual_selection(recommendations)

    # ── 全部方法目录 ─────────────────────────────────────────────────────────
    st.divider()
    st.markdown(t("guide_catalog_title"))
    _render_method_catalog()


def _render_recommendations(recommendations: list[MethodRecommendation]) -> None:
    """渲染推荐结果卡片（每个方法一张卡，含优先级标签）"""
    st.markdown(t("guide_result_title"))
    st.markdown(t("guide_result_subtitle"))

    # 按优先级分组
    priority_groups: dict[int, list[MethodRecommendation]] = {1: [], 2: [], 3: []}
    for rec in recommendations:
        priority_groups.setdefault(rec.priority, []).append(rec)

    for priority in [1, 2, 3]:
        group = priority_groups.get(priority, [])
        if not group:
            continue

        label = t(PRIORITY_KEY_MAP.get(priority, f"guide_priority_{priority}"))
        st.markdown(f"#### {label}")

        for rec in group:
            _render_method_card(rec)


def _render_method_card(rec: MethodRecommendation) -> None:
    """渲染单个方法推荐卡片"""
    bg, text = CATEGORY_COLORS.get(rec.category, ("#F8F9FA", "#2C3E50"))
    cat_key = CATEGORY_KEY_MAP.get(rec.category)
    cat_label = t(cat_key) if cat_key else rec.category
    priority_key = PRIORITY_KEY_MAP.get(rec.priority)
    priority_badge = t(priority_key) if priority_key else ""

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
            with st.expander(t("guide_sub_steps_expander")):
                for i, step in enumerate(rec.sub_steps, 1):
                    st.markdown(f"{i}. {step}")


def _render_manual_selection(auto_recommendations: list) -> None:
    """手动选择分析方法区域"""
    st.markdown("#### 🔧 " + ("手动选择分析方法" if st.session_state.get("lang","zh") == "zh" else "Manually Select Methods"))
    st.caption("在智能推荐基础上，你也可以自行勾选需要的分析方法" if st.session_state.get("lang","zh") == "zh"
               else "You can also manually add methods on top of the AI recommendations.")

    # 所有可选方法（分组展示）
    ALL_METHODS: dict[str, list[str]] = {
        "🔵 描述与诊断": ["描述统计", "相关矩阵", "正态性检验", "VIF 多重共线性", "异方差检验", "自相关检验"],
        "🟡 基准回归":   ["OLS 回归", "面板固定效应（FE/RE/TWFE）", "Hausman 检验", "面板单位根检验"],
        "🔴 因果推断":   ["DID 双重差分", "PSM 倾向得分匹配", "RDD 断点回归", "IV / 2SLS", "动态面板 GMM"],
        "🟢 稳健性检验": ["Bootstrap 置信区间", "剔除特殊样本"],
        "🟣 异质性与机制": ["分组回归", "分位数回归", "中介效应", "调节效应"],
    } if st.session_state.get("lang","zh") == "zh" else {
        "🔵 Diagnostics": ["Descriptive Stats", "Correlation Matrix", "Normality Test", "VIF", "Heteroskedasticity", "Autocorrelation"],
        "🟡 Regression":  ["OLS", "Panel FE/RE/TWFE", "Hausman Test", "Panel Unit Root"],
        "🔴 Causal":      ["DID", "PSM", "RDD", "IV/2SLS", "Dynamic Panel GMM"],
        "🟢 Robustness":  ["Bootstrap CI", "Sample Exclusion"],
        "🟣 Heterogeneity": ["Subgroup Regression", "Quantile Regression", "Mediation", "Moderation"],
    }

    # 已选方法（来自智能推荐或上次手动选择）
    auto_names = [rec.method_name for rec in auto_recommendations]
    default_manual = st.session_state.get("manual_methods", auto_names)

    # 将所有方法名展平为列表（用于 multiselect）
    all_method_names = [m for methods in ALL_METHODS.values() for m in methods]

    # 过滤 default：只保留 all_method_names 里有的
    valid_defaults = [m for m in default_manual if m in all_method_names]

    selected = st.multiselect(
        "选择要在第三步分析的方法：" if st.session_state.get("lang","zh") == "zh" else "Select methods for Step 3 analysis:",
        options=all_method_names,
        default=valid_defaults,
        key="manual_method_select",
    )

    # 显示分组视图
    with st.expander("📋 " + ("按分类查看" if st.session_state.get("lang","zh") == "zh" else "Browse by Category"), expanded=False):
        for group, methods in ALL_METHODS.items():
            st.markdown(f"**{group}**")
            cols = st.columns(3)
            for i, m in enumerate(methods):
                tag = "✅" if m in selected else "○"
                cols[i % 3].markdown(f"{tag} {m}")

    # 跳转按钮
    col_btn, col_tip = st.columns([1, 3])
    with col_btn:
        if st.button(t("guide_btn_start_analysis"), type="primary", key="goto_analysis_manual"):
            st.session_state["manual_methods"]       = selected
            st.session_state["recommended_methods"]  = selected  # analysis.py 用这个
            st.session_state["step"] = 3
            st.session_state["page"] = "📈 实证分析"
            st.rerun()
    with col_tip:
        if selected:
            st.info(f"{'已选' if st.session_state.get('lang','zh')=='zh' else 'Selected'} {len(selected)} {'个方法' if st.session_state.get('lang','zh')=='zh' else 'methods'}：{', '.join(selected[:4])}{'...' if len(selected)>4 else ''}")


def _render_method_catalog() -> None:
    """渲染全部方法目录"""
    catalog = get_method_categories()

    for category, methods in catalog.items():
        with st.expander(category, expanded=False):
            cols = st.columns(3)
            for i, method in enumerate(methods):
                cols[i % 3].markdown(f"• {method['name']}")
