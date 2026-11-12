"""
Generates the clinical PDF report shown in the "ECG Report" mockup:
header with patient/report metadata, ECG waveform (Lead II), an analysis
parameters table, and an interpretation/finding box.
"""

import os
import tempfile
from datetime import datetime

import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import mm
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, Image
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle

ACCENT = colors.HexColor("#EF4444")
DARK = colors.HexColor("#141A2A")
MUTED = colors.HexColor("#6B7280")
GOOD_BG = colors.HexColor("#E8F7EE")
GOOD_TEXT = colors.HexColor("#15803D")
WARN_BG = colors.HexColor("#FEF3E2")
WARN_TEXT = colors.HexColor("#B45309")


def _make_waveform_chart(cleaned_signal, sampling_rate, rpeaks, tmp_dir):
    fig, ax = plt.subplots(figsize=(6.6, 2.0), dpi=150)
    fig.patch.set_facecolor("white")
    ax.set_facecolor("white")

    t = np.arange(len(cleaned_signal)) / sampling_rate
    ax.plot(t, cleaned_signal, color="#1f2937", linewidth=0.8)

    if rpeaks is not None and len(rpeaks):
        peak_t = np.array(rpeaks) / sampling_rate
        peak_y = np.array(cleaned_signal)[np.array(rpeaks)]
        ax.scatter(peak_t, peak_y, color="#EF4444", s=18, zorder=3)

    ax.set_xlabel("Time (s)", fontsize=8)
    ax.set_title("ECG Waveform (Lead II)", fontsize=9, color="#141A2A", loc="left")
    ax.tick_params(labelsize=7, colors="#374151")
    for spine in ax.spines.values():
        spine.set_color("#d1d5db")
    fig.tight_layout()

    path = os.path.join(tmp_dir, "waveform.png")
    fig.savefig(path, facecolor="white")
    plt.close(fig)
    return path


def generate_ecg_report_pdf(report_row, patient_row, doctor_name, cleaned_signal,
                             sampling_rate, rpeaks, output_path):
    """
    report_row: dict from database.reports (includes report_code, params, finding, status)
    patient_row: dict from database.patients
    """
    styles = getSampleStyleSheet()
    title_style = ParagraphStyle("Title2", parent=styles["Title"], textColor=DARK, fontSize=18)
    subtitle_style = ParagraphStyle("Sub2", parent=styles["Normal"], textColor=MUTED, fontSize=9, spaceAfter=12)
    section_style = ParagraphStyle("Sec2", parent=styles["Heading3"], textColor=ACCENT, fontSize=12, spaceBefore=10, spaceAfter=6)
    body_style = ParagraphStyle("Body2", parent=styles["Normal"], textColor=DARK, fontSize=10, leading=14)
    disclaimer_style = ParagraphStyle("Disc2", parent=styles["Normal"], textColor=MUTED, fontSize=8, leading=11, spaceBefore=14)

    doc = SimpleDocTemplate(
        output_path, pagesize=A4,
        topMargin=16 * mm, bottomMargin=14 * mm, leftMargin=18 * mm, rightMargin=18 * mm,
    )
    story = []

    story.append(Paragraph("Cardiac Rhythm Analysis System", title_style))
    story.append(Paragraph("ECG Analysis Report", subtitle_style))

    meta = [
        ["Patient Name", patient_row["name"], "Date of Report", datetime.now().strftime("%d %B %Y")],
        ["Patient ID", patient_row["patient_code"], "Report ID", report_row["report_code"]],
    ]
    meta_table = Table(meta, colWidths=[28 * mm, 55 * mm, 28 * mm, 55 * mm])
    meta_table.setStyle(TableStyle([
        ("FONTSIZE", (0, 0), (-1, -1), 9.5),
        ("FONTNAME", (0, 0), (0, -1), "Helvetica-Bold"),
        ("FONTNAME", (2, 0), (2, -1), "Helvetica-Bold"),
        ("TEXTCOLOR", (0, 0), (0, -1), MUTED),
        ("TEXTCOLOR", (2, 0), (2, -1), MUTED),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
    ]))
    story.append(meta_table)
    story.append(Spacer(1, 6))

    with tempfile.TemporaryDirectory() as tmp_dir:
        chart_path = _make_waveform_chart(cleaned_signal, sampling_rate, rpeaks, tmp_dir)
        story.append(Image(chart_path, width=170 * mm, height=52 * mm))

        story.append(Paragraph("Analysis Parameters", section_style))
        p = report_row
        param_rows = [
            ["Parameter", "Value"],
            ["Heart Rate", f"{p['heart_rate']} BPM" if p["heart_rate"] is not None else "-"],
            ["RR Interval", f"{p['rr_interval']} s" if p["rr_interval"] is not None else "-"],
            ["PR Interval", f"{p['pr_interval']} s" if p["pr_interval"] is not None else "-"],
            ["QRS Duration", f"{p['qrs_duration']} s" if p["qrs_duration"] is not None else "-"],
            ["QT Interval", f"{p['qt_interval']} s" if p["qt_interval"] is not None else "-"],
            ["QTc Interval", f"{p['qtc_interval']} s" if p["qtc_interval"] is not None else "-"],
            ["Beat Count", str(p["beat_count"])],
            ["Signal Duration", f"{p['signal_duration']} s"],
        ]
        param_table = Table(param_rows, colWidths=[70 * mm, 100 * mm])
        param_table.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), DARK),
            ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
            ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
            ("FONTSIZE", (0, 0), (-1, -1), 9.5),
            ("GRID", (0, 0), (-1, -1), 0.4, colors.HexColor("#e5e7eb")),
            ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#f9fafb")]),
            ("TOPPADDING", (0, 0), (-1, -1), 4),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
        ]))
        story.append(param_table)

        story.append(Paragraph("Interpretation", section_style))
        is_stable = report_row["status"] == "Stable"
        bg = GOOD_BG if is_stable else WARN_BG
        fg = GOOD_TEXT if is_stable else WARN_TEXT
        finding_table = Table([[f"Finding: {report_row['finding']}"]], colWidths=[170 * mm])
        finding_table.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, -1), bg),
            ("TEXTCOLOR", (0, 0), (-1, -1), fg),
            ("FONTNAME", (0, 0), (-1, -1), "Helvetica-Bold"),
            ("FONTSIZE", (0, 0), (-1, -1), 11),
            ("TOPPADDING", (0, 0), (-1, -1), 8),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 8),
            ("LEFTPADDING", (0, 0), (-1, -1), 10),
        ]))
        story.append(finding_table)

        if report_row.get("clinician_notes"):
            story.append(Paragraph("Clinician Notes", section_style))
            story.append(Paragraph(report_row["clinician_notes"], body_style))

        prepared_by = f"Prepared by {doctor_name}" if doctor_name else "Prepared by Cardiac Rhythm Analysis System"
        story.append(Paragraph(
            f"{prepared_by}. This report is generated by an automated clinical screening tool using "
            "rule-based threshold comparison. It is intended to support - not replace - the treating "
            "clinician's professional judgment and diagnosis.",
            disclaimer_style,
        ))

        doc.build(story)

    return output_path
