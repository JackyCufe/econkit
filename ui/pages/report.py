"""
报告下载页面
生成和下载 PDF 分析报告
"""
from __future__ import annotations

import datetime

import streamlit as st

from core.report_generator import generate_pdf_report


def render_report() -> None:
    """渲染报告下载页面"""
    st.markdown("## 📄 下载分析报告")
    st.markdown("将本次分析结果汇总为 PDF 报告，可用于论文附录或汇报展示。")

    st.divider()

    # ── 报告基本信息 ──────────────────────────────────────────────────────────
    col1, col2 = st.columns(2)
    with col1:
        report_title = st.text_input(
            "报告标题",
            value="计量经济学实证分析报告",
            key="report_title",
        )
        author = st.text_input("作者/单位", value="", key="report_author")

    with col2:
        data_desc = st.text_area(
            "数据说明",
            value=_get_default_data_desc(),
            height=100,
            key="report_data_desc",
        )

    st.divider()

    # ── 选择包含的内容 ────────────────────────────────────────────────────────
    st.markdown("### 📋 选择报告内容")
    available_results = _get_available_results()

    if not available_results:
        st.info("💡 当前没有分析结果，请先在「实证分析」页面运行分析")
        _render_empty_report_option(report_title, author, data_desc)
        return

    include_sections = st.multiselect(
        "选择包含的分析结果",
        options=[name for name, _ in available_results],
        default=[name for name, _ in available_results],
        key="report_sections",
    )

    # ── 生成报告 ──────────────────────────────────────────────────────────────
    st.divider()
    col_a, col_b = st.columns([1, 3])

    with col_a:
        if st.button("📄 生成 PDF 报告", type="primary"):
            with st.spinner("正在生成报告..."):
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
                    st.success("✅ PDF 报告生成成功！")
                except Exception as e:
                    st.error(f"❌ 报告生成失败：{str(e)}")

    with col_b:
        if "pdf_bytes" in st.session_state and st.session_state["pdf_bytes"]:
            st.download_button(
                label="⬇️ 下载 PDF 报告",
                data=st.session_state["pdf_bytes"],
                file_name=f"{report_title}_{datetime.datetime.now().strftime('%Y%m%d')}.pdf",
                mime="application/pdf",
                key="dl_pdf",
            )

    # ── 预览 ──────────────────────────────────────────────────────────────────
    if available_results:
        st.divider()
        st.markdown("### 📊 分析结果预览")
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
        "descriptive": "描述统计",
        "ols":         "OLS 回归",
        "panel_fe":    "面板固定效应回归",
        "did":         "DID 双重差分",
        "psm":         "PSM 倾向得分匹配",
        "rdd":         "RDD 断点回归",
        "iv":          "IV/2SLS 工具变量",
        "bootstrap":   "Bootstrap 置信区间",
        "mediation":   "中介效应",
        "moderation":  "调节效应",
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
            f"模型：{result.get('name', '回归')}",
            f"观测数：{stats.get('n_obs', 'N/A')}",
            f"R²：{stats.get('r2') or stats.get('r2_within', 'N/A')}",
        ]
        if df_r is not None and not df_r.empty:
            lines.append("主要系数：")
            for _, row in df_r.head(5).iterrows():
                lines.append(f"  {row['变量']}: {row['系数']}{row['显著性']}"
                             f" (SE={row['标准误']}, p={row['p值']})")
        return "\n".join(lines)

    elif key == "did":
        coef  = result.get("did_coef", "N/A")
        stars = result.get("did_stars", "")
        pval  = result.get("did_pval", "N/A")
        n     = result.get("n_obs", "N/A")
        return (f"DID 系数 = {coef}{stars}，p = {pval}，N = {n}")

    elif key == "descriptive":
        stats_df = result.get("stats_df")
        if stats_df is not None:
            return f"变量数：{len(stats_df)}，描述统计已完成"
        return "描述统计已完成"

    else:
        return f"{key} 分析已完成，系数 = {result.get('coef', result.get('att', 'N/A'))}"


def _build_sections(
    available_results: list[tuple[str, str]],
    include_sections: list[str],
) -> list[dict]:
    """构建 PDF 报告章节"""
    sections = []
    analysis_results = st.session_state.get("analysis_results", {})

    # 数据概况
    if "df" in st.session_state and st.session_state["df"] is not None:
        df = st.session_state["df"]
        panel_info = st.session_state.get("panel_info", {})
        sections.append({
            "title": "数据基本情况",
            "content": (
                f"数据规模：{len(df)} 行 × {len(df.columns)} 列\n"
                f"个体变量：{panel_info.get('id_col', '未知')}\n"
                f"时间变量：{panel_info.get('time_col', '未知')}\n"
                f"个体数：{panel_info.get('n_entities', 'N/A')}\n"
                f"时期数：{panel_info.get('n_periods', 'N/A')}\n"
                f"数值变量：{', '.join(df.select_dtypes(include='number').columns.tolist())}"
            ),
        })

    # 各分析结果
    for name, content in available_results:
        if name in include_sections:
            section: dict = {"title": name, "content": content}

            # 尝试提取表格
            key_map = {"OLS 回归": "ols", "面板固定效应回归": "panel_fe",
                       "描述统计": "descriptive"}
            key = key_map.get(name)
            if key and key in analysis_results:
                res = analysis_results[key]
                df_r = res.get("summary_df") or res.get("stats_df")
                if df_r is not None and not df_r.empty:
                    section["table_headers"] = list(df_r.columns)
                    section["table_rows"] = [
                        [str(v) for v in row]
                        for row in df_r.values.tolist()[:10]
                    ]

            sections.append(section)

    return sections


def _get_default_data_desc() -> str:
    """获取默认数据说明"""
    if "df" not in st.session_state or st.session_state["df"] is None:
        return ""
    df = st.session_state["df"]
    panel_info = st.session_state.get("panel_info", {})
    return (
        f"{len(df)} 行 × {len(df.columns)} 列面板数据，"
        f"个体：{panel_info.get('id_col', '未知')}，"
        f"时间：{panel_info.get('time_col', '未知')}"
    )


def _render_empty_report_option(
    title: str, author: str, data_desc: str
) -> None:
    """无分析结果时，提供生成空报告的选项"""
    st.divider()
    st.markdown("### 📋 生成模板报告")
    if st.button("📄 生成空模板报告"):
        sections = [
            {
                "title": "分析说明",
                "content": "本报告为模板，请先完成分析后重新生成。",
            }
        ]
        pdf_bytes = generate_pdf_report(title, sections,
                                         {"author": author, "data_desc": data_desc})
        st.download_button(
            "⬇️ 下载模板 PDF",
            data=pdf_bytes,
            file_name=f"{title}_template.pdf",
            mime="application/pdf",
        )
