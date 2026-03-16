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

from i18n import t

# ── 学术主题颜色 ──────────────────────────────────────────────────────────────
COLOR_PRIMARY   = "#2C3E50"
COLOR_ACCENT    = "#E74C3C"
COLOR_SUCCESS   = "#27AE60"
COLOR_LIGHT     = "#ECF0F1"


# ── 三线表渲染（matplotlib，支持LaTeX公式） ───────────────────────────────────
def render_booktabs_table(
    df: pd.DataFrame,
    title: str = "",
    note: str = "",
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
    if not note:
        note = t("chart.note.default")

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
    note: str = "",
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
    if not note:
        note = t("chart.note.default")

    fig = render_booktabs_table(df, title=title, note=note, show_index=show_index)

    # 先把图保存到 bytes，再展示，再关闭（避免 close 后 savefig 拿不到数据）
    buf_png = io.BytesIO()
    fig.savefig(buf_png, format="png", dpi=200, bbox_inches="tight", facecolor="white")
    buf_png.seek(0)
    png_bytes = buf_png.getvalue()

    st.pyplot(fig, use_container_width=True)
    plt.close(fig)

    # CSV 数据
    csv_bytes = df.to_csv(index=show_index, encoding="utf-8-sig").encode("utf-8-sig")

    # 稳定的 key（用 title hash，不用 id(df)，避免 rerun 时 key 变化触发抖动）
    import hashlib
    _key_suffix = hashlib.md5((title + str(len(df))).encode()).hexdigest()[:8]

    # 提供 PNG 和 CSV 双下载（inline，不用 columns 避免布局抖动）
    col1, col2 = st.columns(2)
    with col1:
        st.download_button(
            label=t("chart.download.table.png"),
            data=png_bytes,
            file_name=f"{title or 'table'}.png",
            mime="image/png",
            key=f"dl_tpng_{_key_suffix}",
        )
    with col2:
        st.download_button(
            label=t("chart.download.csv"),
            data=csv_bytes,
            file_name=f"{title or 'result'}.csv",
            mime="text/csv",
            key=f"dl_csv_{_key_suffix}",
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

    # 先 savefig 到 bytes，再 pyplot 展示，再 close
    # 顺序很关键：close 之后再 savefig 会得到空图；pyplot 之后 close 不影响已渲染的显示
    import hashlib
    buf = io.BytesIO()
    try:
        fig.savefig(buf, format="png", dpi=150, bbox_inches="tight", facecolor="white")
        buf.seek(0)
        png_bytes = buf.getvalue()
    except Exception:
        png_bytes = b""

    st.pyplot(fig, use_container_width=True)
    # 不 close figure，让 session_state 里的 figure 对象保持可用（用于 PDF 生成）
    # 内存由 matplotlib 的 figure manager 管理，Streamlit rerun 时会复用

    if caption:
        st.caption(caption)

    # 稳定 key（用 title + caption hash，rerun 时不变）
    _key_suffix = hashlib.md5((title + caption).encode()).hexdigest()[:8]

    if png_bytes:
        st.download_button(
            label=t("chart.download.png"),
            data=png_bytes,
            file_name=f"{title or 'figure'}.png",
            mime="image/png",
            key=f"dl_fig_{_key_suffix}",
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
    col1.metric(t("reg.n_obs"),   stats.get("n_obs", "N/A"))
    col2.metric(t("reg.r2"),      stats.get("r2") or stats.get("r2_within", "N/A"))
    col3.metric(t("reg.adj_r2"),  stats.get("adj_r2", "N/A"))
    col4.metric(t("reg.f_stat"),  stats.get("f_stat", "N/A"))

    if not df_r.empty:
        display_result_table(
            df_r,
            title=t("reg.coef_table", name=name),
            note=t("chart.note.robust"),
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
    col1.metric(t("did.display.coef"), f"{coef}{stars}")
    col2.metric(t("did.display.se"),   str(se))
    col3.metric(t("did.display.pval"), str(pval))

    if ci and ci[0] is not None:
        st.info(t("did.display.ci", lower=ci[0], upper=ci[1]))

    if isinstance(pval, float):
        if pval < 0.01:
            st.success(t("did.display.sig1"))
        elif pval < 0.05:
            st.success(t("did.display.sig5"))
        elif pval < 0.1:
            st.warning(t("did.display.sig10"))
        else:
            st.error(t("did.display.insig"))


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
