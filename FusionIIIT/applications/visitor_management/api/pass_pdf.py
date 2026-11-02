"""Printable / saveable digital pass with QR (AFR-027, AFR-066) and Code128 barcode."""

import io

from reportlab.graphics import renderPDF
from reportlab.graphics.barcode import code128
from reportlab.graphics.barcode.qr import QrCodeWidget
from reportlab.graphics.shapes import Drawing
from reportlab.lib.pagesizes import A6
from reportlab.lib.units import mm
from reportlab.pdfgen import canvas


def render_pass_pdf(visit, visit_pass):
    buffer = io.BytesIO()
    width, height = A6
    pdf = canvas.Canvas(buffer, pagesize=A6)
    pdf.setTitle("Visitor pass {}".format(visit_pass.pass_number))

    pdf.setFont("Helvetica-Bold", 12)
    pdf.drawString(8 * mm, height - 12 * mm, "IIITDM Jabalpur - Visitor Pass")
    pdf.setFont("Helvetica", 8)
    pdf.drawString(8 * mm, height - 17 * mm, "{}  |  {}".format(visit_pass.get_pass_type_display(), visit.reference))

    qr = QrCodeWidget(visit_pass.qr_token)
    x0, y0, x1, y1 = qr.getBounds()
    size = 42 * mm
    drawing = Drawing(size, size, transform=[size / (x1 - x0), 0, 0, size / (y1 - y0), 0, 0])
    drawing.add(qr)
    renderPDF.draw(drawing, pdf, (width - size) / 2, height - 64 * mm)

    lines = [
        ("Visitor", visit.visitor.full_name),
        ("Host", visit.host.user.get_full_name() or visit.host.user.username),
        ("Valid from", visit_pass.valid_from.strftime("%d %b %Y %H:%M")),
        ("Valid until", visit_pass.valid_until.strftime("%d %b %Y %H:%M")),
        ("Zones", ", ".join(visit_pass.permitted_zones.values_list("code", flat=True)) or "General areas"),
        ("OTP", visit_pass.otp),
    ]
    y = height - 72 * mm
    for label, value in lines:
        pdf.setFont("Helvetica-Bold", 8)
        pdf.drawString(8 * mm, y, label + ":")
        pdf.setFont("Helvetica", 8)
        pdf.drawString(28 * mm, y, str(value)[:48])
        y -= 5 * mm

    barcode = code128.Code128(visit_pass.pass_number, barHeight=10 * mm, barWidth=0.9)
    barcode.drawOn(pdf, (width - barcode.width) / 2, 10 * mm)
    pdf.setFont("Helvetica", 7)
    pdf.drawCentredString(width / 2, 6 * mm, visit_pass.pass_number)
    pdf.showPage()
    pdf.save()
    return buffer.getvalue()
