"""Professional forensics report generation service.

Compiles executive-grade PDF reports containing scan summaries, threat metrics,
and detail tables using ReportLab.
"""

import os
from typing import Dict, Any, List, Optional
from datetime import datetime

from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import (
    SimpleDocTemplate,
    Paragraph,
    Spacer,
    Table,
    TableStyle,
    KeepTogether,
)
from reportlab.pdfgen import canvas

from piracyguard.config import settings
from piracyguard.database.models import ScanJob, ScanResult, Report
from piracyguard.exceptions import ReportNotFoundError
from piracyguard.logging_config import get_logger

logger = get_logger(__name__)


class NumberedCanvas(canvas.Canvas):
    """Canvas that computes total pages dynamically to draw page numbers.

    Also draws professional headers and footers on every page.
    """

    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        self._saved_page_states = []

    def showPage(self) -> None:
        self._saved_page_states.append(dict(self.__dict__))
        self._startPage()

    def save(self) -> None:
        num_pages = len(self._saved_page_states)
        for state in self._saved_page_states:
            self.__dict__.update(state)
            self.draw_page_elements(num_pages)
            super().showPage()
        super().save()

    def draw_page_elements(self, page_count: int) -> None:
        self.saveState()
        
        # ── Color Palette ──
        primary_color = colors.HexColor("#1A365D")  # Deep Blue
        text_color = colors.HexColor("#718096")     # Slate Gray
        
        # Page size info
        width, height = letter

        # ── Header ──
        # Skip header on cover/first page
        if self._pageNumber > 1:
            self.setFont("Helvetica", 8)
            self.setFillColor(text_color)
            self.drawString(54, height - 36, "AI PIRACY GUARD — FORENSIC PIPELINE REPORT")
            self.drawRightString(width - 54, height - 36, f"Generated: {datetime.now().strftime('%Y-%m-%d')}")
            
            # Header line
            self.setStrokeColor(colors.HexColor("#E2E8F0"))
            self.setLineWidth(0.5)
            self.line(54, height - 42, width - 54, height - 42)

        # ── Footer ──
        self.setFont("Helvetica", 8)
        self.setFillColor(text_color)
        self.drawString(54, 36, "CONFIDENTIAL — FOR INTERNAL USE ONLY")
        self.drawRightString(
            width - 54, 36, f"Page {self._pageNumber} of {page_count}"
        )
        
        # Footer line
        self.setStrokeColor(colors.HexColor("#E2E8F0"))
        self.setLineWidth(0.5)
        self.line(54, 46, width - 54, 46)
        
        self.restoreState()


class ReportService:
    """Compiles professional forensics reports in PDF or JSON format."""

    @staticmethod
    def generate_pdf_report(
        job: ScanJob,
        results: List[ScanResult],
        dest_path: str
    ) -> str:
        """Generate a professional PDF report from a ScanJob.

        Args:
            job: ScanJob ORM object.
            results: List of ScanResult ORM objects.
            dest_path: Output file destination path.

        Returns:
            Absolute path to the generated PDF.
        """
        logger.info(
            "Generating PDF forensic report",
            extra={"job_uuid": job.uuid, "dest_path": dest_path}
        )

        # Build directory structure
        os.makedirs(os.path.dirname(dest_path), exist_ok=True)

        doc = SimpleDocTemplate(
            dest_path,
            pagesize=letter,
            rightMargin=54,
            leftMargin=54,
            topMargin=54,
            bottomMargin=54
        )

        styles = getSampleStyleSheet()
        
        # Custom Styles
        title_style = ParagraphStyle(
            "ReportTitle",
            parent=styles["Title"],
            fontName="Helvetica-Bold",
            fontSize=24,
            leading=28,
            textColor=colors.HexColor("#1A365D"),
            alignment=0, # Left-aligned
            spaceAfter=15
        )

        h1_style = ParagraphStyle(
            "Heading1_Custom",
            parent=styles["Heading1"],
            fontName="Helvetica-Bold",
            fontSize=16,
            leading=20,
            textColor=colors.HexColor("#2C5282"),
            spaceBefore=15,
            spaceAfter=10,
            keepWithNext=True
        )

        body_style = ParagraphStyle(
            "BodyText_Custom",
            parent=styles["BodyText"],
            fontName="Helvetica",
            fontSize=10,
            leading=14,
            textColor=colors.HexColor("#2D3748")
        )

        table_header_style = ParagraphStyle(
            "TableHeader",
            parent=styles["Normal"],
            fontName="Helvetica-Bold",
            fontSize=9,
            textColor=colors.white
        )

        table_body_style = ParagraphStyle(
            "TableBody",
            parent=styles["Normal"],
            fontName="Helvetica",
            fontSize=8,
            leading=11,
            textColor=colors.HexColor("#2D3748")
        )

        story = []

        # 1. Header Title / Cover Details
        story.append(Paragraph("AI Piracy Guard", title_style))
        story.append(Paragraph("Forensic Media Security Analysis Report", ParagraphStyle(
            "SubTitle", parent=title_style, fontSize=14, leading=18, textColor=colors.HexColor("#4A5568")
        )))
        story.append(Spacer(1, 15))

        # 2. Executive Summary Block
        story.append(Paragraph("Executive Summary", h1_style))
        summary_text = (
            f"This forensic report presents security analysis results for Scan Job <b>{job.uuid}</b>. "
            f"A total of <b>{job.total_files}</b> video files were processed under this job context. "
            f"The scanner performed video fingerprint duplicate matching, facial deepfake classification, "
            f"watermark tampering identification, and container-level metadata forensics."
        )
        story.append(Paragraph(summary_text, body_style))
        story.append(Spacer(1, 10))

        # Job details table
        job_details_data = [
            [Paragraph("Job UUID", table_body_style), Paragraph(job.uuid, table_body_style)],
            [Paragraph("Status", table_body_style), Paragraph(job.status.value.upper(), table_body_style)],
            [Paragraph("Scan Started", table_body_style), Paragraph(job.started_at.strftime("%Y-%m-%d %H:%M:%S UTC") if job.started_at else "N/A", table_body_style)],
            [Paragraph("Scan Completed", table_body_style), Paragraph(job.completed_at.strftime("%Y-%m-%d %H:%M:%S UTC") if job.completed_at else "N/A", table_body_style)],
            [Paragraph("Total Scan Duration", table_body_style), Paragraph(f"{job.duration_seconds} seconds" if job.duration_seconds else "N/A", table_body_style)]
        ]
        
        detail_table = Table(job_details_data, colWidths=[150, 354])
        detail_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (0, -1), colors.HexColor("#F7FAFC")),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor("#E2E8F0")),
            ('PADDING', (0, 0), (-1, -1), 6),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ]))
        story.append(detail_table)
        story.append(Spacer(1, 15))

        # 3. Aggregated Threats Summary
        story.append(Paragraph("Threat Classification", h1_style))
        
        # Count risks
        high_risk_count = sum(1 for r in results if r.risk_level.value in ("HIGH", "CRITICAL"))
        med_risk_count = sum(1 for r in results if r.risk_level.value == "MEDIUM")
        low_risk_count = sum(1 for r in results if r.risk_level.value in ("LOW", "NONE"))

        risk_summary_text = (
            f"The composite multi-signal risk engine flagged <b>{high_risk_count}</b> files as "
            f"HIGH/CRITICAL risk, requiring immediate administrative intervention. <b>{med_risk_count}</b> "
            f"files were marked as MEDIUM risk, indicating moderate anomalies. <b>{low_risk_count}</b> "
            f"files are classified as LOW/NONE threat and deemed clear."
        )
        story.append(Paragraph(risk_summary_text, body_style))
        story.append(Spacer(1, 15))

        # 4. Detailed Scan Results Table
        story.append(Paragraph("Scanned Media List", h1_style))

        headers = [
            Paragraph("Filename", table_header_style),
            Paragraph("Similarity %", table_header_style),
            Paragraph("Deepfake %", table_header_style),
            Paragraph("Watermark %", table_header_style),
            Paragraph("Risk Score", table_header_style),
            Paragraph("Risk Level", table_header_style),
        ]

        table_data = [headers]

        for idx, r in enumerate(results):
            filename = os.path.basename(r.video_path)
            # Truncate filename if too long for table cell
            if len(filename) > 25:
                filename = filename[:22] + "..."

            # Color code risk levels
            level_text = r.risk_level.value if r.risk_level else "NONE"
            if level_text in ("CRITICAL", "HIGH"):
                bg_color_hex = "#FFF5F5"
                text_color_hex = "#E53E3E"
            elif level_text == "MEDIUM":
                bg_color_hex = "#FFFAF0"
                text_color_hex = "#DD6B20"
            else:
                bg_color_hex = "#F0FFF4"
                text_color_hex = "#38A169"

            styled_level = Paragraph(
                f"<font color='{text_color_hex}'><b>{level_text}</b></font>",
                table_body_style
            )

            row = [
                Paragraph(filename, table_body_style),
                Paragraph(f"{r.similarity_score:.1f}%" if r.similarity_score is not None else "0.0%", table_body_style),
                Paragraph(f"{r.deepfake_score:.1f}%" if r.deepfake_score is not None else "0.0%", table_body_style),
                Paragraph(f"{r.watermark_present_score:.1f}%" if r.watermark_present_score is not None else "0.0%", table_body_style),
                Paragraph(f"{r.risk_score:.1f}" if r.risk_score is not None else "0.0", table_body_style),
                styled_level
            ]
            table_data.append(row)

        results_table = Table(table_data, colWidths=[150, 70, 70, 70, 64, 80])
        
        # Apply style sheet to table
        t_style = TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor("#1A365D")),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor("#CBD5E0")),
            ('PADDING', (0, 0), (-1, -1), 6),
        ])

        # Apply zebra striping and custom threat backgrounds
        for i in range(1, len(table_data)):
            # Determine color code based on row
            res_item = results[i-1]
            level_text = res_item.risk_level.value if res_item.risk_level else "NONE"
            
            if level_text in ("CRITICAL", "HIGH"):
                row_bg = colors.HexColor("#FFF5F5")
            elif level_text == "MEDIUM":
                row_bg = colors.HexColor("#FFFAF0")
            else:
                if i % 2 == 0:
                    row_bg = colors.HexColor("#F7FAFC")
                else:
                    row_bg = colors.white

            t_style.add('BACKGROUND', (0, i), (-1, i), row_bg)

        results_table.setStyle(t_style)
        story.append(results_table)
        story.append(Spacer(1, 15))

        # 5. Build Document
        doc.build(story, canvasmaker=NumberedCanvas)

        logger.info("PDF report generation complete", extra={"job_uuid": job.uuid})
        return dest_path
