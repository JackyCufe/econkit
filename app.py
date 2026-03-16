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

from ui.components.stepper import render_stepper, STEP_TO_PAGE, PAGE_TO_STEP
from ui.pages.home import render_home
from ui.pages.smart_guide import render_smart_guide
from ui.pages.analysis import render_analysis
from ui.pages.report import render_report
from i18n import t


# ── 页面配置 ──────────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="EconKit - 计量经济学分析工具",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="collapsed",
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
    """初始化 session state 默认值，确保所有关键字段存在"""
    defaults: dict = {
        # 语言设置
        "lang":             "zh",
        # 步骤状态（驱动向导式导航）
        "step":             1,
        "page":             "🏠 首页",
        # 数据状态
        "df":               None,
        "filename":         None,
        "panel_info":       {},
        "validation":       {},
        # 分析状态
        "analysis_results": {},
        "recommendations":  [],
        "recommended_methods": [],
        # 报告状态
        "pdf_bytes":        None,
    }
    for key, val in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = val


_init_session()

# ── 语言切换按钮（顶部右上角）──────────────────────────────────────────────────
_lc1, _lc2 = st.columns([20, 1])
with _lc2:
    btn_label = "🌐 EN" if st.session_state["lang"] == "zh" else "🌐 中文"
    if st.button(btn_label, key="lang_toggle", help="Switch Language / 切换语言"):
        st.session_state["lang"] = "en" if st.session_state["lang"] == "zh" else "zh"
        st.rerun()

current_page = st.session_state["page"]
current_step = st.session_state["step"]


# ── 顶部步骤进度条（所有页面内容之上） ────────────────────────────────────────
render_stepper(current_step)


# ── 页面路由 ──────────────────────────────────────────────────────────────────
page_router = {
    "🏠 首页":     render_home,
    "🏠 Home":     render_home,
    "🤖 智能引导": render_smart_guide,
    "🤖 Smart Guide": render_smart_guide,
    "📈 实证分析": render_analysis,
    "📈 Analysis": render_analysis,
    "📄 下载报告": render_report,
    "📄 Download Report": render_report,
}

handler = page_router.get(current_page)
if handler:
    handler()
else:
    render_home()
