import logging
from datetime import datetime
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer
)
from reportlab.lib.styles import (
    getSampleStyleSheet, ParagraphStyle
)
from reportlab.lib.pagesizes import A4
from reportlab.lib.enums import TA_JUSTIFY
from reportlab.lib.units import inch
from pathlib import Path

logger = logging.getLogger(__name__)


def create_styles():
    styles = getSampleStyleSheet()

    styles.add(ParagraphStyle(
        name='CategoryTitle',
        parent=styles['Heading1'],
        fontSize=18,
        textColor='#1a1a1a',
        spaceBefore=16,
        spaceAfter=10,
        leading=22,
        fontName='Helvetica-Bold'
    ))

    styles.add(ParagraphStyle(
        name='CapsuleTitle',     # FIXED: No name conflict
        parent=styles['Heading2'],
        fontSize=14,
        textColor='#333333',
        spaceBefore=12,
        spaceAfter=8,
        leading=18,
        fontName='Helvetica-Bold'
    ))

    styles.add(ParagraphStyle(
        name='Summary',
        parent=styles['BodyText'],
        fontSize=11,
        textColor='#2c2c2c',
        alignment=TA_JUSTIFY,
        leading=16,
        spaceAfter=10
    ))

    styles.add(ParagraphStyle(
        name='SectionHeader',
        parent=styles['Heading3'],
        fontSize=12,
        textColor='#444444',
        spaceBefore=10,
        spaceAfter=6,
        fontName='Helvetica-Bold'
    ))

    styles.add(ParagraphStyle(
        name='ListItem',
        parent=styles['BodyText'],
        fontSize=10,
        textColor='#404040',
        leftIndent=16,
        leading=14,
        spaceAfter=4
    ))

    styles.add(ParagraphStyle(
        name='Meta',
        parent=styles['BodyText'],
        fontSize=9,
        textColor='#666666',
        leading=12,
        spaceAfter=6
    ))

    return styles


def build_pdf_from_markdown(md_file: str, output_pdf: str):
    """
    DIRECT markdown → PDF converter
    (No HTML, no external renderers)
    Parses your UPSC capsule structure reliably.
    """

    md_file = Path(md_file)
    text = md_file.read_text(encoding="utf-8")

    styles = create_styles()
    story = []

    # PDF Header
    story.append(Paragraph("<b>UPSC News Capsules</b>", styles["Heading1"]))
    story.append(Paragraph(
        f"Generated on: {datetime.utcnow().strftime('%d %B %Y')}",
        styles["Normal"]
    ))
    story.append(Spacer(1, 0.3 * inch))

    current_category = None
    current_title = None
    section = None
    summary_buffer = []
    pyq_list = []
    syl_list = []
    meta_buffer = []

    def flush_article():
        """Write the current article to PDF."""
        if current_title:
            story.append(Paragraph(current_title, styles["CapsuleTitle"]))

        if summary_buffer:
            story.append(Paragraph(" ".join(summary_buffer), styles["Summary"]))

        if pyq_list:
            story.append(Paragraph("Relevant PYQ:", styles["SectionHeader"]))
            for item in pyq_list:
                story.append(Paragraph(f"• {item}", styles["ListItem"]))

        if syl_list:
            story.append(Paragraph("Relevant Syllabus:", styles["SectionHeader"]))
            for item in syl_list:
                story.append(Paragraph(f"• {item}", styles["ListItem"]))

        for m in meta_buffer:
            story.append(Paragraph(m, styles["Meta"]))

        story.append(Spacer(1, 0.2 * inch))

    # ---- MAIN MARKDOWN PARSER ----
    for ln in text.splitlines():
        ln = ln.strip()
        if not ln:
            continue

        # NEW: ignore markdown separators
        if ln.strip() == "---":
            continue

        # Category (## ...)
        if ln.startswith("## "):
            flush_article()
            current_category = ln[3:]
            story.append(Paragraph(current_category, styles["CategoryTitle"]))

            # reset article fields
            current_title = None
            summary_buffer = []
            pyq_list = []
            syl_list = []
            meta_buffer = []
            continue

        # Article title (### ...)
        if ln.startswith("### "):
            flush_article()
            current_title = ln[4:]
            summary_buffer = []
            pyq_list = []
            syl_list = []
            meta_buffer = []
            section = "summary"
            continue

        # Section headers
        if ln.lower().startswith("**relevant pyq**"):
            section = "pyq"
            continue

        if ln.lower().startswith("**relevant syllabus**"):
            section = "syllabus"
            continue

        # Bullet items
        if ln.startswith("-") or ln.startswith("*"):
            item = ln.lstrip("-* ").strip()
            if section == "pyq":
                pyq_list.append(item)
            elif section == "syllabus":
                syl_list.append(item)
            else:
                meta_buffer.append(item)
            continue

        # Default summary
        if section == "summary":
            summary_buffer.append(ln)
        else:
            meta_buffer.append(ln)

    # Flush last article
    flush_article()

    # ---- BUILD PDF ----
    doc = SimpleDocTemplate(
        output_pdf,
        pagesize=A4,
        rightMargin=0.5 * inch,
        leftMargin=0.75 * inch,
        topMargin=0.75 * inch,
        bottomMargin=0.75 * inch
    )

    doc.build(story)
    logger.info(f"PDF created: {output_pdf}")

    return output_pdf
