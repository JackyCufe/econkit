"""
报告下载页面
生成和下载 PDF 分析报告
"""
from __future__ import annotations

import datetime
import traceback

import streamlit as st

from core.report_generator import generate_pdf_report
from i18n import t


def render_report() -> None:
    """渲染报告下载页面"""
    st.markdown(t("report_title"))
    st.markdown(t("report_subtitle"))

    st.divider()

    # ── 报告基本信息 ──────────────────────────────────────────────────────────
    col1, col2 = st.columns(2)
    with col1:
        report_title = st.text_input(
            t("report_input_title"),
            value=t("report_input_title_default"),
            key="report_title_input",
        )
        author = st.text_input(t("report_input_author"), value="", key="report_author")

    with col2:
        data_desc = st.text_area(
            t("report_input_data_desc"),
            value=_get_default_data_desc(),
            height=100,
            key="report_data_desc",
        )

    st.divider()

    # ── 选择包含的内容 ────────────────────────────────────────────────────────
    st.markdown(t("report_section_title"))
    available_results = _get_available_results()

    if not available_results:
        st.info(t("report_no_results"))
        _render_empty_report_option(report_title, author, data_desc)
        return

    include_sections = st.multiselect(
        t("report_section_select"),
        options=[name for name, _ in available_results],
        default=[name for name, _ in available_results],
        key="report_sections",
    )

    st.divider()

    # ── 生成按钮 ──────────────────────────────────────────────────────────────
    with st.container():
        if st.button(t("report_gen_btn"), type="primary", key="btn_gen_pdf"):
            with st.spinner(t("report_generating")):
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
                    st.session_state["pdf_bytes"]    = pdf_bytes
                    st.session_state["pdf_filename"] = f"{report_title}_{datetime.datetime.now().strftime('%Y%m%d')}.pdf"
                    st.success(t("report_success"))
                except Exception as e:
                    st.error(t("report_error", error=str(e)))
                    st.code(traceback.format_exc(), language="python")

    # ── 下载按钮（独立区域，明显间隔）────────────────────────────────────────
    pdf_bytes = st.session_state.get("pdf_bytes")
    if pdf_bytes:
        st.markdown("---")
        with st.container():
            st.download_button(
                label     = t("report_download_btn"),
                data      = pdf_bytes,
                file_name = st.session_state.get("pdf_filename", "report.pdf"),
                mime      = "application/pdf",
                key       = "dl_pdf_btn",
            )

    # ── 预览 ──────────────────────────────────────────────────────────────────
    if available_results:
        st.divider()
        st.markdown(t("report_preview_title"))
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
        "descriptive": t("report_result_descriptive"),
        "ols":         t("report_result_ols"),
        "panel_fe":    t("report_result_panel_fe"),
        "did":         t("report_result_did"),
        "psm":         t("report_result_psm"),
        "rdd":         t("report_result_rdd"),
        "iv":          t("report_result_iv"),
        "gmm":         t("method_gmm"),
        "bootstrap":   t("report_result_bootstrap"),
        "mediation":   t("report_result_mediation"),
        "moderation":  t("report_result_moderation"),
        "subgroup":    t("method_subgroup"),
        "quantile":    t("method_quantile"),
        "exclude":     t("method_exclude_samples"),
    }

    for key, result in analysis_results.items():
        name = name_map.get(key, key)
        summary = _build_result_summary(key, result)
        results.append((name, summary))

    return results


def _build_result_summary(key: str, result: dict) -> str:
    """将分析结果转为文字摘要"""
    if key in ("ols", "panel_fe"):
        stats = result.get("stats", {})
        df_r  = result.get("summary_df")
        lines = [
            f"{t('label_n_obs')}：{stats.get('n_obs', 'N/A')}",
            f"{t('label_r2')}：{stats.get('r2') or stats.get('r2_within', 'N/A')}",
        ]
        if df_r is not None and not df_r.empty:
            lines.append(f"{t('label_coef')}：")
            for _, row in df_r.head(5).iterrows():
                coef_col = row.get("系数", row.get("Coef.", "N/A"))
                var_col  = row.get("变量", row.get("Variable", str(row.index)))
                sig_col  = row.get("显著性", row.get("Stars", ""))
                se_col   = row.get("标准误", row.get("Std.Err.", "N/A"))
                p_col    = row.get("p值", row.get("P>|z|", "N/A"))
                lines.append(f"  {var_col}: {coef_col}{sig_col} (SE={se_col}, p={p_col})")
        return "\n".join(lines)

    elif key == "did":
        coef  = result.get("did_coef", "N/A")
        stars = result.get("did_stars", "")
        pval  = result.get("did_pval", "N/A")
        n     = result.get("n_obs", result.get("stats", {}).get("n_obs", "N/A"))
        return f"DID {t('label_coef')} = {coef}{stars}，p = {pval}，N = {n}"

    elif key == "descriptive":
        stats_df = result.get("stats_df")
        if stats_df is not None:
            return f"{t('label_n_obs')}：{len(stats_df)}"
        return t("report_result_descriptive")

    elif key == "psm":
        att  = result.get("att", "N/A")
        pval = result.get("pval", "N/A")
        return f"ATT = {att}，p = {pval}"

    elif key == "rdd":
        coef = result.get("coef", "N/A")
        pval = result.get("pval", "N/A")
        bw   = result.get("bandwidth", "N/A")
        return f"RDD {t('label_coef')} = {coef}，p = {pval}，bandwidth = {bw}"

    elif key == "iv":
        coef = result.get("coef", "N/A")
        pval = result.get("pval", "N/A")
        f1   = result.get("first_stage_f", "N/A")
        return f"IV {t('label_coef')} = {coef}，p = {pval}，First-stage F = {f1}"

    elif key == "mediation":
        indirect = result.get("indirect_effect", "N/A")
        pct      = result.get("pct_mediated", "N/A")
        return f"间接效应 = {indirect}，中介比例 = {pct}%"

    elif key == "moderation":
        coef = result.get("coef", "N/A")
        pval = result.get("pval", "N/A")
        return f"交互项系数 = {coef}，p = {pval}"

    else:
        coef_val = result.get("coef", result.get("att", "N/A"))
        return f"{key}：{t('label_coef')} = {coef_val}"


def _build_sections(
    available_results: list[tuple[str, str]],
    include_sections: list[str],
) -> list[dict]:
    """构建 PDF 报告章节"""
    sections = []
    analysis_results = st.session_state.get("analysis_results", {})
    analysis_figures = st.session_state.get("analysis_figures", {})

    # 数据概况（始终放第一章）
    if st.session_state.get("df") is not None:
        df = st.session_state["df"]
        panel_info = st.session_state.get("panel_info", {})
        sections.append({
            "title": t("report_section_data"),
            "content": (
                f"{t('pdf_data_rows_cols', rows=len(df), cols=len(df.columns))}\n"
                f"{t('pdf_data_id', col=panel_info.get('id_col', 'N/A'))}\n"
                f"{t('pdf_data_time', col=panel_info.get('time_col', 'N/A'))}\n"
                f"{t('pdf_data_entities', n=panel_info.get('n_entities', 'N/A'))}\n"
                f"{t('pdf_data_periods', n=panel_info.get('n_periods', 'N/A'))}\n"
                f"{t('pdf_data_numeric', cols=', '.join(df.select_dtypes(include='number').columns.tolist()))}"
            ),
        })

    # 内部 key 映射（显示名 → 存储 key）
    key_map = {
        t("report_result_descriptive"): "descriptive",
        t("report_result_ols"):         "ols",
        t("report_result_panel_fe"):    "panel_fe",
        t("report_result_did"):         "did",
        t("report_result_psm"):         "psm",
        t("report_result_rdd"):         "rdd",
        t("report_result_iv"):          "iv",
        t("method_gmm"):                "gmm",
        t("report_result_bootstrap"):   "bootstrap",
        t("report_result_mediation"):   "mediation",
        t("report_result_moderation"):  "moderation",
        t("method_subgroup"):           "subgroup",
        t("method_quantile"):           "quantile",
        t("method_exclude_samples"):    "exclude",
    }

    for name, content in available_results:
        if name not in include_sections:
            continue

        section: dict = {"title": name, "content": content}
        key = key_map.get(name)

        # 提取表格
        if key and key in analysis_results:
            res  = analysis_results[key]
            df_r = res.get("summary_df")
            if df_r is None:
                df_r = res.get("stats_df")
            if df_r is not None and not df_r.empty:
                section["table_headers"] = list(df_r.columns)
                section["table_rows"] = [
                    [str(v) for v in row]
                    for row in df_r.values.tolist()[:15]
                ]

        # 嵌入图表
        if key and key in analysis_figures:
            section["figure"] = analysis_figures[key]

        sections.append(section)

    return sections


def _get_default_data_desc() -> str:
    """获取默认数据说明"""
    if st.session_state.get("df") is None:
        return ""
    df = st.session_state["df"]
    panel_info = st.session_state.get("panel_info", {})
    return t(
        "pdf_default_data_desc",
        rows=len(df),
        cols=len(df.columns),
        id=panel_info.get("id_col", "N/A"),
        time=panel_info.get("time_col", "N/A"),
    )


def _render_empty_report_option(
    title: str, author: str, data_desc: str
) -> None:
    """无分析结果时，提供生成空报告的选项"""
    st.divider()
    st.markdown(t("report_empty_title"))
    if st.button(t("report_empty_btn"), key="btn_empty_pdf"):
        sections = [
            {
                "title": "说明" if st.session_state.get("lang", "zh") == "zh" else "Note",
                "content": t("report_empty_content"),
            }
        ]
        try:
            pdf_bytes = generate_pdf_report(
                title, sections, {"author": author, "data_desc": data_desc}
            )
            st.session_state["pdf_bytes"]    = pdf_bytes
            st.session_state["pdf_filename"] = f"{title}_template.pdf"
            st.success(t("report_success"))
        except Exception as e:
            st.error(t("report_error", error=str(e)))

    pdf_bytes = st.session_state.get("pdf_bytes")
    if pdf_bytes:
        st.download_button(
            t("report_empty_download"),
            data      = pdf_bytes,
            file_name = st.session_state.get("pdf_filename", "template.pdf"),
            mime      = "application/pdf",
            key       = "dl_empty_pdf_btn",
        )
