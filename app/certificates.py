from pathlib import Path
from reportlab.lib.pagesizes import landscape, A4
from reportlab.lib import colors
from reportlab.pdfgen import canvas

def generate_certificate(output_path: Path, name: str, course: str, event_name: str, issuer: str) -> None:
    """Generate one PDF using a single predefined template."""
    output_path.parent.mkdir(parents=True, exist_ok=True)
    width, height = landscape(A4)
    pdf = canvas.Canvas(str(output_path), pagesize=(width, height))
    pdf.setTitle(f"Certificate - {name}")
    pdf.setStrokeColor(colors.HexColor("#B08D36"))
    pdf.setLineWidth(4)
    pdf.rect(28, 28, width - 56, height - 56)
    pdf.setFillColor(colors.HexColor("#234E70"))
    pdf.setFont("Helvetica-Bold", 28)
    pdf.drawCentredString(width / 2, height - 115, "CERTIFICATE OF COMPLETION")
    pdf.setFillColor(colors.HexColor("#333333"))
    pdf.setFont("Helvetica", 15)
    pdf.drawCentredString(width / 2, height - 165, "This certificate is proudly presented to")
    pdf.setFillColor(colors.HexColor("#111111"))
    pdf.setFont("Helvetica-Bold", 26)
    pdf.drawCentredString(width / 2, height - 215, name[:90])
    pdf.setFillColor(colors.HexColor("#333333"))
    pdf.setFont("Helvetica", 14)
    pdf.drawCentredString(width / 2, height - 260, f"For successfully completing: {course[:100]}")
    pdf.drawCentredString(width / 2, height - 290, f"Event / Program: {event_name[:100]}")
    pdf.setStrokeColor(colors.HexColor("#777777"))
    pdf.line(width / 2 - 100, 95, width / 2 + 100, 95)
    pdf.setFont("Helvetica-Bold", 12)
    pdf.drawCentredString(width / 2, 75, issuer[:100])
    pdf.setFont("Helvetica", 9)
    pdf.drawCentredString(width / 2, 52, "Authorized issuer")
    pdf.save()
