"""
EconKit - 计量经济学在线分析工具
Streamlit 主入口

运行方式：
    cd /Users/jacky/.openclaw/workspace/econkit
    streamlit run app.py
"""
from __future__ import annotations

import sys
import os

# 将项目根目录添加到 Python 路径
sys.path.insert(0, os.path.dirname(__file__))

import streamlit as st

# 初始化学术图表主题（必须在 streamlit 组件之前）
from assets.academic_theme import apply_academic_theme
apply_academic_theme()

from ui.components.sidebar import render_sidebar
from ui.pages.home import render_home
from ui.pages.smart_guide import render_smart_guide
from ui.pages.analysis import render_analysis
from ui.pages.report import render_report


# ── 页面配置 ──────────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="EconKit - 计量经济学分析工具",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded",
)


# ── 加载自定义 CSS ─────────────────────────────────────────────────────────────
def _load_css() -> None:
    css_path = os.path.join(os.path.dirname(__file__), "assets", "style.css")
    if os.path.exists(css_path):
        with open(css_path, encoding="utf-8") as f:
            st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)


_load_css()


# ── Session 状态初始化 ────────────────────────────────────────────────────────
def _init_session() -> None:
    """初始化 session state 默认值"""
    defaults = {
        "df":               None,
        "filename":         None,
        "panel_info":       {},
        "validation":       {},
        "analysis_results": {},
        "recommendations":  [],
        "pdf_bytes":        None,
        "page":             "🏠 首页",
    }
    for key, val in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = val


_init_session()


# ── 侧边栏导航 ────────────────────────────────────────────────────────────────
page = render_sidebar()

# 侧边栏选择优先，更新 session_state
st.session_state["page"] = page


# ── 页面路由 ──────────────────────────────────────────────────────────────────
page_router = {
    "🏠 首页":     render_home,
    "🤖 智能引导": render_smart_guide,
    "📈 实证分析": render_analysis,
    "📄 下载报告": render_report,
}

handler = page_router.get(page)
if handler:
    handler()
else:
    render_home()
