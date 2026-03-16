"""
顶部步骤进度条组件
用法：CSS 注入（<style> 标签）+ class-based HTML，避开 HF Spaces inline-style CSP 限制
"""
from __future__ import annotations

import streamlit as st
from i18n import t

# 步骤定义（icon 固定，label 通过 t() 动态获取）
STEP_ICONS: list[tuple[int, str]] = [
    (1, "📁"),
    (2, "🤖"),
    (3, "📈"),
    (4, "📄"),
]

STEP_TO_PAGE: dict[int, str] = {
    1: "🏠 首页",
    2: "🤖 智能引导",
    3: "📈 实证分析",
    4: "📄 下载报告",
}

PAGE_TO_STEP: dict[str, int] = {v: k for k, v in STEP_TO_PAGE.items()}

# ── CSS（只注入一次）──────────────────────────────────────────────────────────
_STEPPER_CSS = """
<style>
.ek-stepper {
    display: flex;
    align-items: center;
    background: #fff;
    border-radius: 14px;
    padding: 18px 28px;
    margin-bottom: 18px;
    box-shadow: 0 2px 12px rgba(44,62,80,0.08);
    border: 1px solid #eef0f3;
}
.ek-step {
    display: flex;
    flex-direction: column;
    align-items: center;
    gap: 6px;
    flex: 0 0 auto;
    min-width: 90px;
}
.ek-step-circle {
    width: 40px;
    height: 40px;
    border-radius: 50%;
    display: flex;
    align-items: center;
    justify-content: center;
    font-size: 1.1rem;
    font-weight: 700;
    transition: all 0.3s;
}
.ek-step-circle.done {
    background: #27AE60;
    color: #fff;
}
.ek-step-circle.active {
    background: #2C3E50;
    color: #fff;
    box-shadow: 0 0 0 4px rgba(44,62,80,0.18);
}
.ek-step-circle.todo {
    background: #f0f2f5;
    color: #aab0bb;
    border: 2px solid #dde1e7;
}
.ek-step-label {
    font-size: 0.78rem;
    font-weight: 600;
    white-space: nowrap;
}
.ek-step-label.done  { color: #27AE60; }
.ek-step-label.active { color: #2C3E50; }
.ek-step-label.todo  { color: #aab0bb; }
.ek-connector {
    flex: 1;
    height: 3px;
    border-radius: 2px;
    margin: 0 6px;
    margin-bottom: 22px;
}
.ek-connector.done { background: #27AE60; }
.ek-connector.todo { background: #e5e8ed; }
</style>
"""


def render_stepper(current_step: int) -> None:
    """
    渲染顶部步骤进度条

    Args:
        current_step: 当前步骤编号 (1-4)
    """
    # 动态获取步骤标签（支持 i18n）
    step_labels = [
        t("step1_label"),
        t("step2_label"),
        t("step3_label"),
        t("step4_label"),
    ]

    STEPS = [
        (step_num, icon, step_labels[i])
        for i, (step_num, icon) in enumerate(STEP_ICONS)
    ]

    # 注入 CSS
    st.markdown(_STEPPER_CSS, unsafe_allow_html=True)

    # 构建步骤条 HTML（只用 class，无 inline style）
    items = ""
    for i, (step_num, icon, name) in enumerate(STEPS):
        if step_num < current_step:
            state = "done"
            display = "✓"
        elif step_num == current_step:
            state = "active"
            display = icon
        else:
            state = "todo"
            display = str(step_num)

        items += f"""
        <div class="ek-step">
            <div class="ek-step-circle {state}">{display}</div>
            <span class="ek-step-label {state}">{name}</span>
        </div>
        """

        # 连接线（最后一步不加）
        if i < len(STEPS) - 1:
            connector_state = "done" if step_num < current_step else "todo"
            items += f'<div class="ek-connector {connector_state}"></div>'

    st.markdown(
        f'<div class="ek-stepper">{items}</div>',
        unsafe_allow_html=True,
    )
