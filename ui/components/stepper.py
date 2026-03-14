"""
顶部步骤进度条组件（纯 Streamlit 原生实现，避免 CSP 问题）
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
    渲染顶部步骤进度条（纯原生 Streamlit，无 HTML 注入）

    Args:
        current_step: 当前步骤编号 (1-4)
    """
    cols = st.columns(len(STEPS))

    for i, (step_num, icon, name) in enumerate(STEPS):
        with cols[i]:
            if step_num < current_step:
                # 已完成 - 绿色打勾
                st.success(f"✅ {name}")
            elif step_num == current_step:
                # 当前步骤 - info 蓝色高亮
                st.info(f"**{icon} 步骤{step_num}：{name}**")
            else:
                # 未完成 - 灰色
                st.caption(f"○ {icon} {name}")

    # 进度条
    progress = (current_step - 1) / (len(STEPS) - 1)
    st.progress(progress)
    st.caption(f"当前进度：步骤 {current_step} / {len(STEPS)} — {STEP_TO_PAGE[current_step]}")
    st.divider()
