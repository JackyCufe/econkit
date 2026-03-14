"""
图表展示组件
提供图表渲染、下载按钮等通用 UI 功能
"""
from __future__ import annotations

import io
from typing import Optional

import matplotlib.pyplot as plt
import pandas as pd
import streamlit as st


def display_figure(
    fig: plt.Figure,
    caption: str = "",
    download_name: str = "chart.png",
) -> None:
    """
    展示 matplotlib 图表，并提供 PNG 下载按钮

    Args:
        fig:           matplotlib Figure 对象
        caption:       图表说明
        download_name: 下载文件名
    """
    st.pyplot(fig, use_container_width=True)
    if caption:
        st.caption(caption)

    # 导出为 PNG
    buf = io.BytesIO()
    fig.savefig(buf, format="png", dpi=300, bbox_inches="tight",
                facecolor="white")
    buf.seek(0)

    st.download_button(
        label=f"⬇️ 下载图表 PNG",
        data=buf,
        file_name=download_name,
        mime="image/png",
        key=f"dl_{download_name}_{id(fig)}",
    )
    plt.close(fig)


def display_result_table(
    df: pd.DataFrame,
    title: str = "",
    note: str = "",
    highlight_col: Optional[str] = None,
) -> None:
    """
    展示结果表格（学术三线表风格）

    Args:
        df:            结果 DataFrame
        title:         表格标题
        note:          表格注释
        highlight_col: 高亮的列名（用于强调关键结果）
    """
    if title:
        st.markdown(f"**{title}**")

    # 表格样式
    styler = df.style.format(precision=4)

    if highlight_col and highlight_col in df.columns:
        styler = styler.highlight_max(
            subset=[highlight_col], color="#FADBD8"
        )

    st.dataframe(
        styler,
        use_container_width=True,
        hide_index=False,
    )

    if note:
        st.caption(f"注：{note}")

    # CSV 下载
    csv_bytes = df.to_csv(index=True, encoding="utf-8-sig").encode("utf-8-sig")
    st.download_button(
        label="⬇️ 下载表格 CSV",
        data=csv_bytes,
        file_name=f"{title or 'result'}.csv",
        mime="text/csv",
        key=f"dl_csv_{title}_{id(df)}",
    )


def display_regression_summary(result: dict) -> None:
    """
    展示标准回归结果摘要（系数表 + 统计量）

    Args:
        result: run_ols / run_panel_model 等函数的返回字典
    """
    name  = result.get("name", "回归结果")
    stats = result.get("stats", {})
    df_r  = result.get("summary_df", pd.DataFrame())

    st.markdown(f"### {name}")

    col1, col2, col3, col4 = st.columns(4)
    col1.metric("观测数 N",    stats.get("n_obs", "N/A"))
    col2.metric("R²",          stats.get("r2") or stats.get("r2_within", "N/A"))
    col3.metric("Adj. R²",     stats.get("adj_r2", "N/A"))
    col4.metric("F 统计量",    stats.get("f_stat", "N/A"))

    if not df_r.empty:
        display_result_table(
            df_r,
            title=f"{name} 系数表",
            note="括号内为标准误；*** p<0.01，** p<0.05，* p<0.1",
        )


def display_did_summary(did_result: dict, title: str = "DID 回归结果") -> None:
    """DID 结果摘要卡片展示"""
    st.markdown(f"### {title}")

    coef  = did_result.get("did_coef", "N/A")
    se    = did_result.get("did_se", "N/A")
    pval  = did_result.get("did_pval", "N/A")
    stars = did_result.get("did_stars", "")
    ci    = did_result.get("did_ci", [None, None])

    col1, col2, col3 = st.columns(3)
    col1.metric("DID 系数", f"{coef}{stars}")
    col2.metric("标准误",   str(se))
    col3.metric("p 值",     str(pval))

    if ci[0] is not None:
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
        result:        检验结果字典
        test_name:     检验名称
        conclusion_key: 结论字段的键名
    """
    st.markdown(f"**{test_name}**")
    if "error" in result:
        st.error(f"❌ {result['error']}")
        return

    conclusion = result.get(conclusion_key, "")
    display_dict = {k: v for k, v in result.items()
                    if k not in [conclusion_key, "model", "matched_df"]}

    # 展示为 metrics
    cols = st.columns(min(4, len(display_dict)))
    for i, (k, v) in enumerate(display_dict.items()):
        cols[i % len(cols)].metric(k, str(v))

    if conclusion:
        if "✅" in str(conclusion):
            st.success(conclusion)
        elif "⚠️" in str(conclusion):
            st.warning(conclusion)
        else:
            st.info(conclusion)
