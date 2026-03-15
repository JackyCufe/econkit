"""
PDF 报告生成模块
使用 ReportLab 生成学术风格分析报告
"""
from __future__ import annotations

import io
import datetime
from typing import Any, Optional

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import cm
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle,
    PageBreak, KeepTogether, Image as RLImage
)
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_JUSTIFY


# ── 颜色常量 ─────────────────────────────────────────────────────────────────
COLOR_DARK_BLUE  = colors.HexColor("#2C3E50")
COLOR_RED        = colors.HexColor("#E74C3C")
COLOR_LIGHT_BLUE = colors.HexColor("#EBF5FB")
COLOR_GRAY       = colors.HexColor("#95A5A6")
COLOR_WHITE      = colors.white
COLOR_BORDER     = colors.HexColor("#2C3E50")


# ── 字体注册 ─────────────────────────────────────────────────────────────────
def _register_fonts() -> bool:
    """尝试注册中文字体，返回是否成功"""
    import os
    font_paths = [
        # macOS
        "/Library/Fonts/Songti.ttc",
        "/System/Library/Fonts/PingFang.ttc",
        "/Library/Fonts/Arial Unicode.ttf",
        # Linux
        "/usr/share/fonts/truetype/wqy/wqy-microhei.ttc",
    ]
    for path in font_paths:
        if os.path.exists(path):
            try:
                pdfmetrics.registerFont(TTFont("ChineseFont", path))
                return True
            except Exception:
                continue
    return False


_FONT_REGISTERED = _register_fonts()
_FONT_NAME = "ChineseFont" if _FONT_REGISTERED else "Helvetica"


# ── 样式构建 ──────────────────────────────────────────────────────────────────
def _build_styles() -> dict[str, ParagraphStyle]:
    """构建文档样式"""
    base = getSampleStyleSheet()
    font = _FONT_NAME

    styles = {
        "title": ParagraphStyle(
            "EconTitle",
            fontName=font,
            fontSize=18,
            textColor=COLOR_DARK_BLUE,
            alignment=TA_CENTER,
            spaceAfter=6,
            leading=22,
        ),
        "subtitle": ParagraphStyle(
            "EconSubtitle",
            fontName=font,
            fontSize=11,
            textColor=COLOR_GRAY,
            alignment=TA_CENTER,
            spaceAfter=20,
        ),
        "h1": ParagraphStyle(
            "EconH1",
            fontName=font,
            fontSize=14,
            textColor=COLOR_DARK_BLUE,
            spaceBefore=16,
            spaceAfter=8,
            borderPad=4,
        ),
        "h2": ParagraphStyle(
            "EconH2",
            fontName=font,
            fontSize=12,
            textColor=COLOR_DARK_BLUE,
            spaceBefore=10,
            spaceAfter=6,
        ),
        "body": ParagraphStyle(
            "EconBody",
            fontName=font,
            fontSize=10,
            leading=16,
            alignment=TA_JUSTIFY,
            spaceAfter=6,
        ),
        "note": ParagraphStyle(
            "EconNote",
            fontName=font,
            fontSize=8,
            textColor=COLOR_GRAY,
            spaceAfter=4,
        ),
        "highlight": ParagraphStyle(
            "EconHighlight",
            fontName=font,
            fontSize=10,
            textColor=COLOR_RED,
            spaceAfter=4,
        ),
    }
    return styles


# ── 三线表构建 ─────────────────────────────────────────────────────────────────
def _build_three_line_table(
    headers: list[str],
    rows: list[list[Any]],
    col_widths: Optional[list[float]] = None,
) -> Table:
    """
    构建 ReportLab 三线表
    """
    data = [headers] + rows
    if col_widths is None:
        available = 17.0 * cm
        col_widths = [available / len(headers)] * len(headers)

    table = Table(data, colWidths=col_widths, repeatRows=1)
    table.setStyle(TableStyle([
        # 顶线（粗）
        ("LINEABOVE",    (0, 0), (-1, 0),  1.5, COLOR_DARK_BLUE),
        # 表头与数据分隔线（细）
        ("LINEBELOW",    (0, 0), (-1, 0),  0.8, COLOR_DARK_BLUE),
        # 底线（粗）
        ("LINEBELOW",    (0, -1), (-1, -1), 1.5, COLOR_DARK_BLUE),
        # 表头样式
        ("BACKGROUND",   (0, 0), (-1, 0),  COLOR_LIGHT_BLUE),
        ("TEXTCOLOR",    (0, 0), (-1, 0),  COLOR_DARK_BLUE),
        ("FONTNAME",     (0, 0), (-1, 0),  _FONT_NAME),
        ("FONTSIZE",     (0, 0), (-1, 0),  9),
        ("FONTSIZE",     (0, 1), (-1, -1), 9),
        ("FONTNAME",     (0, 1), (-1, -1), _FONT_NAME),
        # 对齐
        ("ALIGN",        (0, 0), (-1, 0),  "CENTER"),
        ("ALIGN",        (0, 1), (-1, -1), "CENTER"),
        ("ALIGN",        (0, 1), (0, -1),  "LEFT"),     # 第一列左对齐
        # 内边距
        ("TOPPADDING",   (0, 0), (-1, -1), 4),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
        # 交替行背景
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [COLOR_WHITE, colors.HexColor("#F8F9FA")]),
    ]))
    return table


# ── 页眉页脚 ──────────────────────────────────────────────────────────────────
def _header_footer(canvas, doc) -> None:
    """绘制页眉和页脚"""
    canvas.saveState()
    width, _ = A4

    # 页眉
    canvas.setStrokeColor(COLOR_DARK_BLUE)
    canvas.setLineWidth(0.8)
    canvas.line(2*cm, A4[1] - 1.5*cm, width - 2*cm, A4[1] - 1.5*cm)
    canvas.setFont(_FONT_NAME, 8)
    canvas.setFillColor(COLOR_GRAY)
    canvas.drawString(2*cm, A4[1] - 1.2*cm, "EconKit 计量经济学分析报告")
    canvas.drawRightString(width - 2*cm, A4[1] - 1.2*cm,
                           datetime.datetime.now().strftime("%Y-%m-%d"))

    # 页脚
    canvas.line(2*cm, 1.5*cm, width - 2*cm, 1.5*cm)
    canvas.drawCentredString(width / 2, 1.0*cm, f"第 {doc.page} 页")
    canvas.restoreState()


# ── 主生成函数 ─────────────────────────────────────────────────────────────────
def _fig_to_image(fig, max_width: float = 15.0) -> Optional[RLImage]:
    """将 matplotlib Figure 转为 ReportLab Image 对象"""
    try:
        import matplotlib.pyplot as plt
        buf = io.BytesIO()
        fig.savefig(buf, format="png", dpi=150, bbox_inches="tight", facecolor="white")
        buf.seek(0)
        img = RLImage(buf)
        # 按比例缩放到页面宽度
        scale = (max_width * cm) / img.drawWidth
        img.drawWidth  *= scale
        img.drawHeight *= scale
        return img
    except Exception:
        return None


def generate_pdf_report(
    title: str,
    sections: list[dict],
    metadata: Optional[dict] = None,
) -> bytes:
    """
    生成 PDF 报告

    Args:
        title: 报告标题
        sections: 各分析节列表，每节格式：
            {
                "title": str,
                "content": str,          # 文字描述
                "table_headers": list,   # 可选：表格表头
                "table_rows": list,      # 可选：表格数据
                "figure": plt.Figure,    # 可选：matplotlib 图表
                "note": str,             # 可选：注释
            }
        metadata: 元数据 {"author", "data_desc", "date"}

    Returns:
        PDF 字节流
    """
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        leftMargin=2*cm,
        rightMargin=2*cm,
        topMargin=2.5*cm,
        bottomMargin=2.5*cm,
        title=title,
    )

    styles = _build_styles()
    story: list = []

    # ── 封面 ──────────────────────────────────────────────────────────────────
    story.append(Spacer(1, 3*cm))
    story.append(Paragraph(title, styles["title"]))
    story.append(Spacer(1, 0.5*cm))
    story.append(Paragraph(
        "EconKit 计量经济学实证分析系统",
        styles["subtitle"]
    ))

    if metadata:
        date_str = metadata.get("date", datetime.datetime.now().strftime("%Y年%m月%d日"))
        story.append(Paragraph(f"生成时间：{date_str}", styles["subtitle"]))
        if data_desc := metadata.get("data_desc"):
            story.append(Paragraph(f"数据说明：{data_desc}", styles["subtitle"]))

    story.append(Spacer(1, 1*cm))

    # 装饰线
    story.append(Table([[""]], colWidths=[17*cm],
                       style=[("LINEABOVE", (0,0), (-1,-1), 2, COLOR_DARK_BLUE),
                              ("LINEBELOW", (0,0), (-1,-1), 2, COLOR_DARK_BLUE)]))
    story.append(PageBreak())

    # ── 目录 ──────────────────────────────────────────────────────────────────
    story.append(Paragraph("目  录", styles["h1"]))
    for i, section in enumerate(sections, 1):
        story.append(Paragraph(
            f"{i}. {section.get('title', '分析结果')}",
            styles["body"]
        ))
    story.append(PageBreak())

    # ── 各分析节 ─────────────────────────────────────────────────────────────
    for i, section in enumerate(sections, 1):
        section_title = section.get("title", f"分析 {i}")
        content = section.get("content", "")
        table_headers = section.get("table_headers")
        table_rows = section.get("table_rows")
        note = section.get("note", "")

        block: list = []
        block.append(Paragraph(f"{i}. {section_title}", styles["h1"]))

        if content:
            for line in content.strip().split("\n"):
                if line.strip():
                    block.append(Paragraph(line.strip(), styles["body"]))

        if table_headers and table_rows:
            block.append(Spacer(1, 0.3*cm))
            tbl = _build_three_line_table(table_headers, table_rows)
            block.append(tbl)
            block.append(Spacer(1, 0.2*cm))

        # 嵌入图表
        figure = section.get("figure")
        if figure is not None:
            rl_img = _fig_to_image(figure)
            if rl_img is not None:
                block.append(Spacer(1, 0.3*cm))
                block.append(rl_img)
                block.append(Spacer(1, 0.2*cm))

        if note:
            block.append(Paragraph(f"注：{note}", styles["note"]))

        block.append(Spacer(1, 0.5*cm))
        story.append(KeepTogether(block))

    # ── 免责声明 ──────────────────────────────────────────────────────────────
    story.append(PageBreak())
    story.append(Paragraph("免责声明", styles["h1"]))
    story.append(Paragraph(
        "本报告由 EconKit 系统自动生成，仅供学术研究参考。"
        "分析结果的解读和使用需结合具体研究背景，"
        "对于重要决策建议咨询专业计量经济学家。",
        styles["note"]
    ))

    doc.build(story, onFirstPage=_header_footer, onLaterPages=_header_footer)
    return buffer.getvalue()
