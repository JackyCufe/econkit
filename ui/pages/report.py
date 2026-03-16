"""
报告下载页面
生成和下载 PDF 分析报告
"""
from __future__ import annotations

import datetime

import streamlit as st

from core.report_generator import generate_pdf_report
from i18n import t


def render_report() -> None:
    """渲染报告下载页面"""
    st.markdown(t("report.title"))
    st.markdown(t("report.subtitle"))

    st.divider()

    # ── 报告基本信息 ──────────────────────────────────────────────────────────
    col1, col2 = st.columns(2)
    with col1:
        report_title = st.text_input(
            t("report.input.title"),
            value=t("report.input.title.default"),
            key="report_title",
        )
        author = st.text_input(t("report.input.author"), value="", key="report_author")

    with col2:
        data_desc = st.text_area(
            t("report.input.data_desc"),
            value=_get_default_data_desc(),
            height=100,
            key="report_data_desc",
        )

    st.divider()

    # ── 选择包含的内容 ────────────────────────────────────────────────────────
    st.markdown(t("report.section.title"))
    available_results = _get_available_results()

    if not available_results:
        st.info(t("report.no_results"))
        _render_empty_report_option(report_title, author, data_desc)
        return

    include_sections = st.multiselect(
        t("report.section.select"),
        options=[name for name, _ in available_results],
        default=[name for name, _ in available_results],
        key="report_sections",
    )

    # ── 生成报告 ──────────────────────────────────────────────────────────────
    st.divider()
    col_a, col_b = st.columns([1, 3])

    with col_a:
        if st.button(t("report.btn.generate"), type="primary"):
            with st.spinner(t("report.generating")):
                sections = _build_sections(available_results, include_sections)
                metadata = {
                    "author":    author,
                    "date":      datetime.datetime.now().strftime("%Y年%m月%d日"),
                    "data_desc": data_desc,
                }
                try:
                    pdf_bytes = generate_pdf_report(
                        title    = report_title,
                        sections = sections,
                        metadata = metadata,
                    )
                    st.session_state["pdf_bytes"] = pdf_bytes
                    st.success(t("report.success"))
                except Exception as e:
                    st.error(t("report.error", error=str(e)))

    with col_b:
        if "pdf_bytes" in st.session_state and st.session_state["pdf_bytes"]:
            st.download_button(
                label=t("report.btn.download"),
                data=st.session_state["pdf_bytes"],
                file_name=f"{report_title}_{datetime.datetime.now().strftime('%Y%m%d')}.pdf",
                mime="application/pdf",
                key="dl_pdf",
            )

    # ── 预览 ──────────────────────────────────────────────────────────────────
    if available_results:
        st.divider()
        st.markdown(t("report.preview.title"))
        for name, content in available_results:
            if name in (include_sections if include_sections else [n for n, _ in available_results]):
                with st.expander(f"📌 {name}"):
                    st.write(content)


def _get_available_results() -> list[tuple[str, str]]:
    """
    从 session_state 中获取已完成的分析结果摘要

    Returns: [(分析名称, 结果摘要文本)]
    """
    results = []
    analysis_results = st.session_state.get("analysis_results", {})

    name_map = {
        "descriptive": t("report.result.descriptive"),
        "ols":         t("report.result.ols"),
        "panel_fe":    t("report.result.panel_fe"),
        "did":         t("report.result.did"),
        "psm":         t("report.result.psm"),
        "rdd":         t("report.result.rdd"),
        "iv":          t("report.result.iv"),
        "bootstrap":   t("report.result.bootstrap"),
        "mediation":   t("report.result.mediation"),
        "moderation":  t("report.result.moderation"),
    }

    for key, result in analysis_results.items():
        name = name_map.get(key, key)
        summary = _build_result_summary(key, result)
        results.append((name, summary))

    return results


def _build_result_summary(key: str, result: dict) -> str:
    """将分析结果转为文字摘要"""
    if key == "ols" or key == "panel_fe":
        stats = result.get("stats", {})
        df_r  = result.get("summary_df")
        lines = [
            t("report.summary.model", name=result.get("name", "回归")),
            t("report.summary.n_obs", n=stats.get("n_obs", "N/A")),
            t("report.summary.r2", r2=stats.get("r2") or stats.get("r2_within", "N/A")),
        ]
        if df_r is not None and not df_r.empty:
            lines.append(t("report.summary.coefs"))
            for _, row in df_r.head(5).iterrows():
                lines.append(f"  {row['变量']}: {row['系数']}{row['显著性']}"
                             f" (SE={row['标准误']}, p={row['p值']})")
        return "\n".join(lines)

    elif key == "did":
        coef  = result.get("did_coef", "N/A")
        stars = result.get("did_stars", "")
        pval  = result.get("did_pval", "N/A")
        n     = result.get("n_obs", "N/A")
        return t("report.summary.did", coef=coef, stars=stars, pval=pval, n=n)

    elif key == "descriptive":
        stats_df = result.get("stats_df")
        if stats_df is not None:
            return t("report.summary.vars", n=len(stats_df))
        return t("report.result.descriptive") + " 已完成"

    else:
        coef = result.get("coef", result.get("att", "N/A"))
        return t("report.summary.done", key=key, coef=coef)


def _build_sections(
    available_results: list[tuple[str, str]],
    include_sections: list[str],
) -> list[dict]:
    """构建 PDF 报告章节"""
    sections = []
    analysis_results = st.session_state.get("analysis_results", {})
    unknown = t("pdf.data.unknown")
    na = t("pdf.data.na")

    # 数据概况
    if "df" in st.session_state and st.session_state["df"] is not None:
        df = st.session_state["df"]
        panel_info = st.session_state.get("panel_info", {})
        numeric_cols = ", ".join(df.select_dtypes(include="number").columns.tolist())
        sections.append({
            "title": t("report.section.data"),
            "content": "\n".join([
                t("pdf.data.rows_cols", rows=len(df), cols=len(df.columns)),
                t("pdf.data.id", col=panel_info.get("id_col", unknown)),
                t("pdf.data.time", col=panel_info.get("time_col", unknown)),
                t("pdf.data.entities", n=panel_info.get("n_entities", na)),
                t("pdf.data.periods", n=panel_info.get("n_periods", na)),
                t("pdf.data.numeric", cols=numeric_cols),
            ]),
        })

    # 各分析结果
    analysis_figures = st.session_state.get("analysis_figures", {})
    result_name_to_key = {
        t("report.result.ols"):       "ols",
        t("report.result.panel_fe"):  "panel_fe",
        t("report.result.descriptive"): "descriptive",
        t("report.result.did"):       "did",
        t("report.result.bootstrap"): "bootstrap",
        t("report.result.mediation"): "mediation",
        t("report.result.moderation"): "moderation",
        "GMM":                        "gmm",
    }

    for name, content in available_results:
        if name in include_sections:
            section: dict = {"title": name, "content": content}
            key = result_name_to_key.get(name)

            # 提取表格（不能用 or，DataFrame 的布尔值会抛 ValueError）
            if key and key in analysis_results:
                res = analysis_results[key]
                df_r = res.get("summary_df")
                if df_r is None:
                    df_r = res.get("stats_df")
                if df_r is not None and not df_r.empty:
                    section["table_headers"] = list(df_r.columns)
                    section["table_rows"] = [
                        [str(v) for v in row]
                        for row in df_r.values.tolist()[:10]
                    ]

            # 嵌入图表
            if key and key in analysis_figures:
                section["figure"] = analysis_figures[key]

            sections.append(section)

    return sections


def _get_default_data_desc() -> str:
    """获取默认数据说明"""
    if "df" not in st.session_state or st.session_state["df"] is None:
        return ""
    df = st.session_state["df"]
    panel_info = st.session_state.get("panel_info", {})
    unknown = t("pdf.data.unknown")
    return t(
        "pdf.default_data_desc",
        rows=len(df),
        cols=len(df.columns),
        id=panel_info.get("id_col", unknown),
        time=panel_info.get("time_col", unknown),
    )


def _render_empty_report_option(
    title: str, author: str, data_desc: str
) -> None:
    """无分析结果时，提供生成空报告的选项"""
    st.divider()
    st.markdown(t("report.empty.title"))
    if st.button(t("report.empty.btn")):
        sections = [
            {
                "title": "Analysis Notes",
                "content": t("report.empty.content"),
            }
        ]
        pdf_bytes = generate_pdf_report(title, sections,
                                         {"author": author, "data_desc": data_desc})
        st.download_button(
            t("report.empty.download"),
            data=pdf_bytes,
            file_name=f"{title}_template.pdf",
            mime="application/pdf",
        )
