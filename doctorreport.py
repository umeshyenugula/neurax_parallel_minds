from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas
from reportlab.lib import colors
from reportlab.lib.utils import ImageReader
from datetime import date
from PIL import Image, ImageEnhance
import urllib.request
import webbrowser
import os
import io


# ========== IMAGE HANDLING ==========
def fetch_image(path_or_url):
    """Fetch image either from local path or URL"""
    if os.path.exists(path_or_url):
        return ImageReader(path_or_url)
    else:
        with urllib.request.urlopen(path_or_url) as response:
            img_data = response.read()
        return ImageReader(io.BytesIO(img_data))


def add_background(c, width, height, bg_source, opacity=0.15):
    """Add background image with opacity"""
    if os.path.exists(bg_source):
        img = Image.open(bg_source).convert("RGBA")
    else:
        with urllib.request.urlopen(bg_source) as response:
            img_data = response.read()
        img = Image.open(io.BytesIO(img_data)).convert("RGBA")

    alpha = img.split()[3]
    alpha = ImageEnhance.Brightness(alpha).enhance(opacity)
    img.putalpha(alpha)

    temp_img = "temp_bg.png"
    img.save(temp_img)

    img_width, img_height = img.size
    x = (width - img_width) / 2
    y = (height - img_height) / 2

    c.drawImage(temp_img, x, y, width=img_width, height=img_height, mask='auto')


# ========== TEXT UTILITIES ==========
def draw_wrapped_text(c, x, y, text, max_width, font="Helvetica", size=11, leading=14):
    """Wrap and draw text in a specified width"""
    c.setFont(font, size)
    words = text.split()
    line = ""
    for word in words:
        test_line = line + word + " "
        if c.stringWidth(test_line, font, size) <= max_width:
            line = test_line
        else:
            c.drawString(x, y, line.strip())
            y -= leading
            line = word + " "
    if line:
        c.drawString(x, y, line.strip())
        y -= leading
    return y, leading


def draw_wrapped_text_height(c, text, max_width, font="Helvetica", size=11, leading=14):
    """Get height of wrapped text"""
    c.setFont(font, size)
    words = text.split()
    line = ""
    lines = []
    for word in words:
        test_line = line + word + " "
        if c.stringWidth(test_line, font, size) <= max_width:
            line = test_line
        else:
            lines.append(line.strip())
            line = word + " "
    if line:
        lines.append(line.strip())
    return len(lines), len(lines) * leading


# ========== PAGE BREAK UTILITY ==========
def check_page_space(c, y, needed, width, height, bg_path=None):
    """Check if enough space exists, else new page"""
    if y - needed < 60:
        c.showPage()
        if bg_path:
            add_background(c, width, height, bg_path, 0.15)
        c.setFillColor(colors.HexColor("#1E3A8A"))
        c.rect(0, height - 70, width, 70, fill=1)
        c.setFont("Helvetica-Bold", 20)
        c.setFillColor(colors.HexColor("#F59E0B"))
        c.drawString(40, height - 45, "Kidney Scan Report Detailed (Doctor Copy)")
        c.setFont("Helvetica", 12)
        c.setFillColor(colors.HexColor("#000000"))
        return height - 100
        
    return y


# ========== MAIN REPORT FUNCTION ==========
def create_kidney_report(
        filename,
        patient_info: dict,
        findings: dict,
        scanned_image_path=None,
        bg_path=None,
        suggestions=None,
        report_title="Kidney Scan Report Detailed (Doctor Copy)",
        show_pdf=True
):
    c = canvas.Canvas(filename, pagesize=A4)
    width, height = A4

    if bg_path:
        add_background(c, width, height, bg_path, 0.15)

    # Header
    c.setFillColor(colors.HexColor("#1E3A8A"))
    c.rect(0, height - 70, width, 70, fill=1)
    c.setFont("Helvetica-Bold", 20)
    c.setFillColor(colors.HexColor("#F59E0B"))
    c.drawString(40, height - 45, report_title)

    # Patient Info
    y = height - 100
    c.setFont("Helvetica-Bold", 12)
    c.setFillColor(colors.HexColor("#F59E0B"))
    c.drawString(40, y, "Patient Name:")
    c.drawString(300, y, "Gender:")
    c.setFillColor(colors.black)
    c.setFont("Helvetica", 12)
    c.drawString(125, y, patient_info.get('name', 'N/A'))
    c.drawString(350, y, patient_info.get('gender', 'N/A'))

    y -= 20
    c.setFont("Helvetica-Bold", 12)
    c.setFillColor(colors.HexColor("#F59E0B"))
    c.drawString(40, y, "Patient ID:")
    c.drawString(300, y, "Age:")
    c.setFillColor(colors.black)
    c.setFont("Helvetica", 12)
    c.drawString(110, y, patient_info.get('id', 'N/A'))
    c.drawString(330, y, str(patient_info.get('age', 'N/A')))

    y -= 20
    c.setFont("Helvetica-Bold", 12)
    c.setFillColor(colors.HexColor("#F59E0B"))
    c.drawString(40, y, "Address:")
    c.drawString(300, y, "Date Of Report:")
    c.setFillColor(colors.black)
    c.setFont("Helvetica", 12)
    c.drawString(400, y, str(patient_info.get("report_date", date.today())))
    y, _ = draw_wrapped_text(c, 100, y, patient_info.get('address', 'N/A'), width - 400)
    y -= 20

    # AI Overview
    ai_overview = findings.get('ai_overview', 'No overview available.')
    needed_height = draw_wrapped_text_height(c, ai_overview, width - 100)[1] + 50
    y = check_page_space(c, y, needed_height, width, height, bg_path)

    c.setFont("Helvetica-Bold", 13)
    c.setFillColor(colors.HexColor("#1E3A8A"))
    c.drawString(40, y, "AI Overview:")
    c.setFont("Helvetica", 12)
    c.setFillColor(colors.black)
    y, _ = draw_wrapped_text(c, 60, y - 20, ai_overview, width - 100)
    y -= 10

    # Findings Box
    details = [
        ("Kidney Stone Detection:", findings.get('detection', 'N/A')),
        ("Location:", findings.get('location', 'N/A')),
    ]
    if findings.get('detection', '').lower() == "detected":
        details += [
            ("Stone Size:", findings.get('stone_size', 'N/A')),
            ("Number of Stones:", findings.get('number_of_stones', 'N/A')),
        ]
    details.append(("Conclusion:", findings.get('conclusion', 'N/A')))

    total_height = sum(draw_wrapped_text_height(c, val, width - 260)[1] + 20 for _, val in details)
    box_height = total_height + 20
    y = check_page_space(c, y, box_height + 40, width, height, bg_path)

    c.setFont("Helvetica-Bold", 13)
    c.setFillColor(colors.HexColor("#1E3A8A"))
    c.drawString(40, y, "Findings:")
    box_x, box_width = 30, width - 60
    box_y = y - box_height - 10
    c.setStrokeColor(colors.HexColor("#FD9595"))
    c.setLineWidth(1)
    c.rect(box_x, box_y, box_width, box_height)

    text_y = y - 30
    text_x = 50
    for label, val in details:
        c.setFont("Helvetica-Bold", 12)
        c.setFillColor(colors.HexColor("#F59E0B"))
        c.drawString(text_x, text_y, label)
        c.setFont("Helvetica", 12)
        c.setFillColor(colors.black)
        text_y, _ = draw_wrapped_text(c, text_x + 160, text_y, val, width - 260)
        text_y -= 15

    y = box_y - 30

    # Doctor Suggestions
    y = check_page_space(c, y, 100, width, height, bg_path)
    c.setFont("Helvetica-Bold", 13)
    c.setFillColor(colors.HexColor("#1E3A8A"))
    c.drawString(40, y, "Suggestions for Doctors:")
    y -= 20
    c.setFont("Helvetica", 12)
    c.setFillColor(colors.black)

    if not suggestions:
        suggestions = findings.get("doctor_suggestions", [])

    for sug in suggestions:
        needed_height = draw_wrapped_text_height(c, f"- {sug}", width - 100)[1] + 10
        y = check_page_space(c, y, needed_height, width, height, bg_path)
        y, _ = draw_wrapped_text(c, 60, y, f"- {sug}", width - 100)
        y -= 20

    # Footer
    y = check_page_space(c, y, 60, width, height, bg_path)
    c.setFont("Helvetica", 10)
    c.setFillColor(colors.gray)
    c.drawString(40, 70, "This report is generated by AI and is intended for review by a qualified medical professional.")
    c.setFillColor(colors.HexColor("#F59E0B"))
    c.setFont("Helvetica-Bold", 12)
    c.drawString(width - 140, 40, "Powered By LithoLens")

    c.save()
    if show_pdf:
        webbrowser.open_new(r'file://' + os.path.abspath(filename))
