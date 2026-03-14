"""
图表与结果展示组件
支持：学术三线表（matplotlib LaTeX渲染）、图表展示、回归摘要、检验结果
"""
from __future__ import annotations

import io
from typing import Optional

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.ticker as ticker
from matplotlib.patches import FancyBboxPatch
import numpy as np
import pandas as pd
import streamlit as st

# ── 学术主题颜色 ──────────────────────────────────────────────────────────────
COLOR_PRIMARY   = "#2C3E50"
COLOR_ACCENT    = "#E74C3C"
COLOR_SUCCESS   = "#27AE60"
COLOR_LIGHT     = "#ECF0F1"


# ── 三线表渲染（matplotlib，支持LaTeX公式） ───────────────────────────────────
def render_booktabs_table(
    df: pd.DataFrame,
    title: str = "",
    note: str = "注：括号内为标准误；*** p<0.01，** p<0.05，* p<0.1",
    col_width: float = 1.8,
    row_height: float = 0.45,
    font_size: float = 9.5,
    show_index: bool = True,
) -> plt.Figure:
    """
    渲染学术三线表（booktabs风格）

    Args:
        df:         数据框
        title:      表格标题
        note:       表格注释
        col_width:  每列宽度（英寸）
        row_height: 每行高度（英寸）
        font_size:  字体大小
        show_index: 是否显示行索引

    Returns:
        matplotlib Figure
    """
    if show_index:
        display_df = df.reset_index()
        display_df.rename(columns={"index": ""}, inplace=True)
    else:
        display_df = df.reset_index(drop=True)

    n_rows, n_cols = display_df.shape

    # 图表尺寸
    fig_w = max(6.0, n_cols * col_width + 0.5)
    fig_h = (n_rows + 3) * row_height + (0.6 if title else 0) + (0.4 if note else 0)

    fig, ax = plt.subplots(figsize=(fig_w, fig_h), dpi=150)
    ax.axis("off")

    # 标题
    y_offset = 1.0
    if title:
        ax.text(
            0.5, y_offset, title,
            transform=ax.transAxes,
            ha="center", va="top",
            fontsize=font_size + 1.5,
            fontweight="bold",
            color=COLOR_PRIMARY,
        )
        y_offset -= (0.55 / fig_h)

    # 表格数据
    cell_text = []
    for _, row in display_df.iterrows():
        cell_text.append([str(v) for v in row])

    col_labels = list(display_df.columns)

    table = ax.table(
        cellText=cell_text,
        colLabels=col_labels,
        loc="center",
        cellLoc="center",
    )
    table.auto_set_font_size(False)
    table.set_fontsize(font_size)
    table.scale(1.0, 1.4)

    # 三线表样式：只保留顶线、表头下线、底线
    for (row_idx, col_idx), cell in table.get_celld().items():
        cell.set_edgecolor("none")  # 默认去掉所有边框
        cell.set_linewidth(0)

        if row_idx == 0:
            # 表头行：上下粗线 + 浅灰背景
            cell.set_facecolor(COLOR_LIGHT)
            cell.set_text_props(fontweight="bold", color=COLOR_PRIMARY)
            # 表头顶线（top）和底线（bottom）
            cell.visible_edges = "TB"
            cell.set_linewidth(1.2)
            cell.set_edgecolor(COLOR_PRIMARY)
        elif row_idx == n_rows:
            # 最后一行：底线
            cell.visible_edges = "B"
            cell.set_linewidth(1.2)
            cell.set_edgecolor(COLOR_PRIMARY)
            cell.set_facecolor("white")
        else:
            # 数据行：无边框，交替背景
            cell.set_facecolor("white" if row_idx % 2 == 1 else "#FAFAFA")

    # 注释
    if note:
        ax.text(
            0.02, 0.01, note,
            transform=ax.transAxes,
            ha="left", va="bottom",
            fontsize=font_size - 1.5,
            color="#666666",
            style="italic",
        )

    plt.tight_layout(pad=0.3)
    return fig


def display_result_table(
    df: pd.DataFrame,
    title: str = "",
    note: str = "注：括号内为标准误；*** p<0.01，** p<0.05，* p<0.1",
    highlight_col: Optional[str] = None,
    show_index: bool = True,
) -> None:
    """
    展示结果表格（三线表风格，matplotlib渲染 + 可下载）

    Args:
        df:            结果 DataFrame
        title:         表格标题
        note:          表格注释
        highlight_col: 高亮列（暂留接口，三线表中用行色区分）
        show_index:    是否显示行索引
    """
    fig = render_booktabs_table(df, title=title, note=note, show_index=show_index)

    # 展示图表
    st.pyplot(fig, use_container_width=True)
    plt.close(fig)

    # 提供 PNG 和 CSV 双下载
    col1, col2 = st.columns(2)
    with col1:
        buf = io.BytesIO()
        render_booktabs_table(df, title=title, note=note, show_index=show_index).savefig(
            buf, format="png", dpi=300, bbox_inches="tight", facecolor="white"
        )
        st.download_button(
            label="⬇️ 下载表格 PNG",
            data=buf.getvalue(),
            file_name=f"{title or 'table'}.png",
            mime="image/png",
            key=f"dl_png_{title}_{id(df)}",
        )
    with col2:
        csv_bytes = df.to_csv(index=show_index, encoding="utf-8-sig").encode("utf-8-sig")
        st.download_button(
            label="⬇️ 下载表格 CSV",
            data=csv_bytes,
            file_name=f"{title or 'result'}.csv",
            mime="text/csv",
            key=f"dl_csv_{title}_{id(df)}",
        )


def display_figure(
    fig: plt.Figure,
    title: str = "",
    caption: str = "",
) -> None:
    """
    展示 matplotlib 图表，提供 PNG 下载

    Args:
        fig:     matplotlib Figure 对象
        title:   图表标题（显示在图表上方）
        caption: 图表说明（显示在图表下方）
    """
    if title:
        st.markdown(f"**{title}**")

    st.pyplot(fig, use_container_width=True)
    plt.close(fig)

    if caption:
        st.caption(caption)

    # PNG 下载
    buf = io.BytesIO()
    fig.savefig(buf, format="png", dpi=300, bbox_inches="tight", facecolor="white")
    st.download_button(
        label="⬇️ 下载图表 PNG (300DPI)",
        data=buf.getvalue(),
        file_name=f"{title or 'figure'}.png",
        mime="image/png",
        key=f"dl_fig_{title}_{id(fig)}",
    )


def display_regression_summary(result: dict) -> None:
    """
    展示标准回归结果摘要（三线表 + 统计量 metrics）

    Args:
        result: run_ols / run_panel_model 等函数的返回字典
    """
    name  = result.get("name", "回归结果")
    stats = result.get("stats", {})
    df_r  = result.get("summary_df", pd.DataFrame())

    st.markdown(f"### {name}")

    # 统计量 metrics 卡片
    col1, col2, col3, col4 = st.columns(4)
    col1.metric("观测数 N",  stats.get("n_obs", "N/A"))
    col2.metric("R²",        stats.get("r2") or stats.get("r2_within", "N/A"))
    col3.metric("Adj. R²",   stats.get("adj_r2", "N/A"))
    col4.metric("F 统计量",  stats.get("f_stat", "N/A"))

    if not df_r.empty:
        display_result_table(
            df_r,
            title=f"{name} 系数表",
            note="注：括号内为稳健标准误；*** p<0.01，** p<0.05，* p<0.1",
        )


def display_did_summary(did_result: dict, title: str = "DID 回归结果") -> None:
    """DID 结果摘要卡片展示"""
    st.markdown(f"### {title}")

    coef  = did_result.get("did_coef", "N/A")
    se    = did_result.get("did_se",   "N/A")
    pval  = did_result.get("did_pval", "N/A")
    stars = did_result.get("did_stars", "")
    ci    = did_result.get("did_ci", [None, None])

    col1, col2, col3 = st.columns(3)
    col1.metric("DID 系数", f"{coef}{stars}")
    col2.metric("标准误",   str(se))
    col3.metric("p 值",     str(pval))

    if ci and ci[0] is not None:
        st.info(f"📐 95% 置信区间：[{ci[0]:.4f}, {ci[1]:.4f}]")

    if isinstance(pval, float):
        if pval < 0.01:
            st.success("✅ DID 估计在 1% 显著性水平显著")
        elif pval < 0.05:
            st.success("✅ DID 估计在 5% 显著性水平显著")
        elif pval < 0.1:
            st.warning("⚡ DID 估计在 10% 显著性水平显著")
        else:
            st.error("❌ DID 估计不显著（p ≥ 0.1）")


def display_test_result(
    result: dict,
    test_name: str,
    conclusion_key: str = "结论",
) -> None:
    """
    展示统计检验结果

    Args:
        result:         检验结果字典
        test_name:      检验名称
        conclusion_key: 结论字段的键名
    """
    st.markdown(f"**{test_name}**")

    if "error" in result:
        st.error(f"❌ {result['error']}")
        return

    conclusion = result.get(conclusion_key, "")
    display_dict = {
        k: v for k, v in result.items()
        if k not in [conclusion_key, "model", "matched_df"]
    }

    # 展示为 metrics
    if display_dict:
        cols = st.columns(min(4, max(1, len(display_dict))))
        for i, (k, v) in enumerate(display_dict.items()):
            cols[i % len(cols)].metric(k, str(v))

    if conclusion:
        if "✅" in str(conclusion):
            st.success(conclusion)
        elif "⚠️" in str(conclusion):
            st.warning(conclusion)
        else:
            st.info(conclusion)
