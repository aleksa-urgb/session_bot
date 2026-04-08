"""
export_helper.py - Generator PDF & TXT untuk Bot Rekap Setoran
"""

import os
from datetime import datetime
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import cm
from reportlab.lib import colors
from reportlab.platypus import (
    SimpleDocTemplate, Table, TableStyle, Paragraph,
    Spacer, HRFlowable
)
from reportlab.lib.enums import TA_CENTER, TA_RIGHT, TA_LEFT
from config import PDF_DIR, TXT_DIR

os.makedirs(PDF_DIR, exist_ok=True)
os.makedirs(TXT_DIR, exist_ok=True)


def format_idr(val):
    try:
        return f"Rp {int(val):,}".replace(",", ".")
    except:
        return "Rp 0"


# =====================
# EXPORT TXT
# =====================

def export_txt(judul, data_setoran, data_pengeluaran, ringkasan, label_filter):
    """Generate file .txt rekap"""
    now_str = datetime.now().strftime("%d/%m/%Y %H:%M")
    filename = f"rekap_{label_filter.replace('/', '-').replace(' ', '_')}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
    path = os.path.join(TXT_DIR, filename)

    lines = []
    SEP = "=" * 55
    SEP2 = "-" * 55

    lines.append(SEP)
    lines.append(f"   BOT REKAP SETORAN TELE".center(55))
    lines.append(f"   {judul}".center(55))
    lines.append(f"   Dicetak: {now_str}".center(55))
    lines.append(SEP)
    lines.append("")

    # RINGKASAN
    lines.append("📊 RINGKASAN")
    lines.append(SEP2)
    lines.append(f"  Total Masuk    : {format_idr(ringkasan['masuk'])}")
    lines.append(f"  Total Keluar   : {format_idr(ringkasan['keluar'])}")
    ur = ringkasan['untung_rugi']
    status = "✅ UNTUNG" if ur >= 0 else "❌ RUGI"
    lines.append(f"  Untung / Rugi  : {format_idr(ur)} ({status})")
    lines.append(f"  Transaksi Masuk: {ringkasan['jml_setoran']}")
    lines.append(f"  Transaksi Keluar: {ringkasan['jml_pengeluaran']}")
    lines.append("")

    # DETAIL SETORAN
    if data_setoran:
        lines.append(f"💰 DETAIL SETORAN MASUK ({len(data_setoran)} transaksi)")
        lines.append(SEP2)
        for d in data_setoran:
            lines.append(f"  ID   : {d['id']}")
            lines.append(f"  Nama : {d['nama']}")
            lines.append(f"  Nominal : {format_idr(d['nominal'])}")
            lines.append(f"  Ket  : {d.get('keterangan', '-')}")
            lines.append(f"  Tgl  : {d['tanggal']} {str(d['waktu'])[:8]}")
            lines.append(SEP2)

    # DETAIL PENGELUARAN
    if data_pengeluaran:
        lines.append("")
        lines.append(f"💸 DETAIL PENGELUARAN ({len(data_pengeluaran)} transaksi)")
        lines.append(SEP2)
        for d in data_pengeluaran:
            lines.append(f"  ID   : {d['id']}")
            lines.append(f"  Nama : {d['nama']}")
            lines.append(f"  Nominal : {format_idr(d['nominal'])}")
            lines.append(f"  Ket  : {d.get('keterangan', '-')}")
            lines.append(f"  Tgl  : {d['tanggal']} {str(d['waktu'])[:8]}")
            lines.append(SEP2)

    lines.append("")
    lines.append(SEP)
    lines.append(f"  Bot Rekap Setoran  —  {now_str}".center(55))
    lines.append(SEP)

    with open(path, 'w', encoding='utf-8') as f:
        f.write("\n".join(lines))

    return path


# =====================
# EXPORT PDF
# =====================

def export_pdf(judul, data_setoran, data_pengeluaran, ringkasan, label_filter):
    """Generate file .pdf rekap"""
    filename = f"rekap_{label_filter.replace('/', '-').replace(' ', '_')}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"
    path = os.path.join(PDF_DIR, filename)
    now_str = datetime.now().strftime("%d/%m/%Y %H:%M")

    doc = SimpleDocTemplate(
        path, pagesize=A4,
        topMargin=1.5*cm, bottomMargin=1.5*cm,
        leftMargin=1.5*cm, rightMargin=1.5*cm
    )

    styles = getSampleStyleSheet()
    style_title = ParagraphStyle("title",
        fontSize=16, fontName="Helvetica-Bold",
        alignment=TA_CENTER, textColor=colors.HexColor("#1F4E79"),
        spaceAfter=4)
    style_sub = ParagraphStyle("sub",
        fontSize=10, fontName="Helvetica",
        alignment=TA_CENTER, textColor=colors.grey,
        spaceAfter=12)
    style_h2 = ParagraphStyle("h2",
        fontSize=12, fontName="Helvetica-Bold",
        textColor=colors.HexColor("#1F4E79"),
        spaceBefore=10, spaceAfter=4)
    style_body = styles["Normal"]

    story = []

    # Header
    story.append(Paragraph("📋 BOT REKAP SETORAN TELE", style_title))
    story.append(Paragraph(f"{judul} &nbsp; | &nbsp; Dicetak: {now_str}", style_sub))
    story.append(HRFlowable(width="100%", thickness=2, color=colors.HexColor("#1F4E79")))
    story.append(Spacer(1, 0.3*cm))

    # Ringkasan table
    story.append(Paragraph("📊 Ringkasan", style_h2))
    ur = ringkasan['untung_rugi']
    ur_color = colors.HexColor("#375623") if ur >= 0 else colors.HexColor("#C00000")
    ur_label = "UNTUNG ✅" if ur >= 0 else "RUGI ❌"

    sum_data = [
        ["Keterangan", "Nilai"],
        ["Total Uang Masuk", format_idr(ringkasan['masuk'])],
        ["Total Pengeluaran", format_idr(ringkasan['keluar'])],
        [f"Untung / Rugi ({ur_label})", format_idr(abs(ur))],
        ["Transaksi Masuk", str(ringkasan['jml_setoran'])],
        ["Transaksi Keluar", str(ringkasan['jml_pengeluaran'])],
    ]
    tbl = Table(sum_data, colWidths=[9*cm, 7*cm])
    tbl.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#1F4E79")),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("FONTSIZE", (0, 0), (-1, -1), 10),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.HexColor("#EBF3FB"), colors.white]),
        ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
        ("ALIGN", (1, 0), (1, -1), "RIGHT"),
        ("FONTNAME", (0, 3), (-1, 3), "Helvetica-Bold"),
        ("TEXTCOLOR", (0, 3), (-1, 3), ur_color),
        ("PADDING", (0, 0), (-1, -1), 6),
    ]))
    story.append(tbl)
    story.append(Spacer(1, 0.4*cm))

    # Detail setoran
    if data_setoran:
        story.append(Paragraph(f"💰 Detail Setoran Masuk ({len(data_setoran)} transaksi)", style_h2))
        tbl_data = [["ID", "Nama", "Nominal", "Keterangan", "Tanggal"]]
        for d in data_setoran:
            tbl_data.append([
                str(d['id']),
                str(d['nama']),
                format_idr(d['nominal']),
                str(d.get('keterangan', '-'))[:40],
                f"{d['tanggal']} {str(d['waktu'])[:5]}"
            ])
        tbl_s = Table(tbl_data, colWidths=[1.2*cm, 4.5*cm, 3.5*cm, 5.5*cm, 3.5*cm])
        tbl_s.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#1F4E79")),
            ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
            ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
            ("FONTSIZE", (0, 0), (-1, -1), 8),
            ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.HexColor("#E2EFDA"), colors.white]),
            ("GRID", (0, 0), (-1, -1), 0.4, colors.grey),
            ("ALIGN", (2, 0), (2, -1), "RIGHT"),
            ("PADDING", (0, 0), (-1, -1), 4),
        ]))
        story.append(tbl_s)
        story.append(Spacer(1, 0.4*cm))

    # Detail pengeluaran
    if data_pengeluaran:
        story.append(Paragraph(f"💸 Detail Pengeluaran ({len(data_pengeluaran)} transaksi)", style_h2))
        tbl_data = [["ID", "Nama/Keperluan", "Nominal", "Keterangan", "Tanggal"]]
        for d in data_pengeluaran:
            tbl_data.append([
                str(d['id']),
                str(d['nama']),
                format_idr(d['nominal']),
                str(d.get('keterangan', '-'))[:40],
                f"{d['tanggal']} {str(d['waktu'])[:5]}"
            ])
        tbl_p = Table(tbl_data, colWidths=[1.2*cm, 4.5*cm, 3.5*cm, 5.5*cm, 3.5*cm])
        tbl_p.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#C00000")),
            ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
            ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
            ("FONTSIZE", (0, 0), (-1, -1), 8),
            ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.HexColor("#FCE4D6"), colors.white]),
            ("GRID", (0, 0), (-1, -1), 0.4, colors.grey),
            ("ALIGN", (2, 0), (2, -1), "RIGHT"),
            ("PADDING", (0, 0), (-1, -1), 4),
        ]))
        story.append(tbl_p)

    story.append(Spacer(1, 0.5*cm))
    story.append(HRFlowable(width="100%", thickness=1, color=colors.grey))
    story.append(Paragraph(
        f"Dokumen ini digenerate otomatis oleh Bot Rekap Setoran  —  {now_str}",
        ParagraphStyle("footer", fontSize=8, textColor=colors.grey, alignment=TA_CENTER)
    ))

    doc.build(story)
    return path
