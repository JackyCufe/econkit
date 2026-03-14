"""
顶部步骤进度条组件
Progressive Disclosure UX - 向导式步骤引导
"""
from __future__ import annotations

import streamlit as st

# 步骤定义：(步骤号, 图标, 名称)
STEPS: list[tuple[int, str, str]] = [
    (1, "📁", "上传数据"),
    (2, "🤖", "智能引导"),
    (3, "📈", "实证分析"),
    (4, "📄", "下载报告"),
]

# 步骤号 → 页面名映射
STEP_TO_PAGE: dict[int, str] = {
    1: "🏠 首页",
    2: "🤖 智能引导",
    3: "📈 实证分析",
    4: "📄 下载报告",
}

PAGE_TO_STEP: dict[str, int] = {v: k for k, v in STEP_TO_PAGE.items()}


def render_stepper(current_step: int) -> None:
    """
    渲染顶部步骤进度条

    Args:
        current_step: 当前步骤编号 (1-4)
    """
    st.markdown(
        _build_stepper_html(current_step),
        unsafe_allow_html=True,
    )


def _build_stepper_html(current_step: int) -> str:
    """构建步骤条 HTML"""
    items_html = ""
    for step_num, icon, name in STEPS:
        if step_num < current_step:
            # 已完成步骤 - 绿色
            style = (
                "background:#27AE60; color:white; border-radius:50%; "
                "width:32px; height:32px; display:inline-flex; "
                "align-items:center; justify-content:center; font-size:1rem;"
            )
            label_style = "color:#27AE60; font-weight:600; font-size:0.85rem;"
            circle = f'<div style="{style}">✅</div>'
        elif step_num == current_step:
            # 当前步骤 - 深蓝色高亮
            style = (
                "background:#2C3E50; color:white; border-radius:50%; "
                "width:32px; height:32px; display:inline-flex; "
                "align-items:center; justify-content:center; font-size:1rem; "
                "box-shadow:0 0 0 3px rgba(44,62,80,0.25);"
            )
            label_style = "color:#2C3E50; font-weight:700; font-size:0.85rem;"
            circle = f'<div style="{style}">{icon}</div>'
        else:
            # 未完成步骤 - 灰色
            style = (
                "background:#BDC3C7; color:white; border-radius:50%; "
                "width:32px; height:32px; display:inline-flex; "
                "align-items:center; justify-content:center; font-size:1rem;"
            )
            label_style = "color:#95A5A6; font-weight:400; font-size:0.85rem;"
            circle = f'<div style="{style}">{icon}</div>'

        items_html += f"""
        <div style="display:flex; flex-direction:column; align-items:center; gap:4px;">
            {circle}
            <span style="{label_style}">{name}</span>
        </div>
        """

        # 步骤间连接线（最后一步不加）
        if step_num < len(STEPS):
            line_color = "#27AE60" if step_num < current_step else "#E0E0E0"
            items_html += f"""
            <div style="flex:1; height:2px; background:{line_color};
                        margin-top:-20px; align-self:flex-start; margin-top:16px;">
            </div>
            """

    return f"""
    <div style="
        background:white;
        border-radius:12px;
        padding:1rem 1.5rem;
        margin-bottom:1rem;
        box-shadow:0 1px 4px rgba(0,0,0,0.08);
        display:flex;
        align-items:center;
        gap:8px;
    ">
        {items_html}
    </div>
    """
