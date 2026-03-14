"""
学术图表主题配置
仿学术期刊风格：Times New Roman / SimSun，三线表，深蓝主色
"""
from __future__ import annotations
import matplotlib
import matplotlib.pyplot as plt
import matplotlib.font_manager as fm
import platform
from typing import Optional


# ── 颜色常量 ─────────────────────────────────────────────────────────────────
COLOR_PRIMARY   = "#2C3E50"   # 深蓝（主色）
COLOR_SECONDARY = "#E74C3C"   # 红色（显著性标注）
COLOR_ACCENT    = "#3498DB"   # 浅蓝（辅助）
COLOR_GRAY      = "#95A5A6"   # 灰色（背景/次要）
COLOR_FILL      = "#EBF5FB"   # 浅蓝填充

# 显著性颜色映射
SIGNIFICANCE_COLORS = {
    "***": "#E74C3C",
    "**":  "#E67E22",
    "*":   "#F1C40F",
    "":    "#95A5A6",
}


def _get_chinese_font() -> Optional[str]:
    """检测系统中文字体，优先级：STSong > SimSun > PingFang > Heiti"""
    candidates = [
        "STSong", "SimSun", "Songti SC",
        "PingFang SC", "Heiti SC", "STHeiti",
        "Arial Unicode MS", "WenQuanYi Micro Hei"
    ]
    available = {f.name for f in fm.fontManager.ttflist}
    for name in candidates:
        if name in available:
            return name
    return None


def apply_academic_theme() -> None:
    """全局应用学术图表主题设置"""
    chinese_font = _get_chinese_font()
    sans_serif_list = ["Times New Roman", "DejaVu Sans"]
    if chinese_font:
        sans_serif_list.insert(0, chinese_font)

    matplotlib.rcParams.update({
        # 字体
        "font.family":          "sans-serif",
        "font.sans-serif":      sans_serif_list,
        "font.size":            11,
        "axes.titlesize":       12,
        "axes.labelsize":       11,
        "xtick.labelsize":      10,
        "ytick.labelsize":      10,
        "legend.fontsize":      10,
        # 线条
        "axes.linewidth":       1.0,
        "grid.linewidth":       0.5,
        "lines.linewidth":      1.8,
        # 网格
        "axes.grid":            True,
        "grid.alpha":           0.3,
        "grid.linestyle":       "--",
        # 其他
        "axes.unicode_minus":   False,
        "figure.dpi":           150,
        "savefig.dpi":          300,
        "savefig.bbox":         "tight",
        "figure.facecolor":     "white",
        "axes.facecolor":       "white",
        "axes.spines.top":      False,
        "axes.spines.right":    False,
    })


def make_figure(width: float = 10, height: float = 6) -> tuple:
    """创建学术风格图表，返回 (fig, ax)"""
    fig, ax = plt.subplots(figsize=(width, height))
    return fig, ax


def make_subplots(rows: int, cols: int,
                  width: float = 12, height: float = 8) -> tuple:
    """创建多子图学术风格图表，返回 (fig, axes)"""
    fig, axes = plt.subplots(rows, cols, figsize=(width, height))
    return fig, axes


def finalize_figure(fig: plt.Figure,
                    title: str = "",
                    note: str = "") -> None:
    """最终化图表：添加标题和注释"""
    if title:
        fig.suptitle(title, fontsize=13, fontweight="bold",
                     color=COLOR_PRIMARY, y=1.01)
    if note:
        fig.text(0.01, -0.02, f"注：{note}",
                 fontsize=9, color="#666666", style="italic")
    plt.tight_layout()


def add_significance_stars(ax: plt.Axes, x: float, y: float,
                            p_value: float, offset: float = 0.02) -> None:
    """在图表上标注显著性星号"""
    if p_value < 0.01:
        stars = "***"
    elif p_value < 0.05:
        stars = "**"
    elif p_value < 0.1:
        stars = "*"
    else:
        return
    color = SIGNIFICANCE_COLORS.get(stars, COLOR_SECONDARY)
    ax.text(x, y + offset, stars, ha="center", va="bottom",
            color=color, fontsize=11, fontweight="bold")


def style_three_line_table(ax: plt.Axes) -> None:
    """将 ax 设置为三线表风格（隐藏所有边框，由外部绘制横线）"""
    ax.axis("off")


# 初始化主题（导入即生效）
apply_academic_theme()
