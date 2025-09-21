from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas
from reportlab.lib import colors
from reportlab.lib.utils import ImageReader
import urllib.request, io, os, webbrowser
from datetime import date
from PIL import Image, ImageEnhance

# ---------- Image Handling ----------
def fetch_image(path_or_url):
    """Fetch image either from local path or URL"""
    if os.path.exists(path_or_url):
        return ImageReader(path_or_url)
    else:
        with urllib.request.urlopen(path_or_url) as response:
            img_data = response.read()
        return ImageReader(io.BytesIO(img_data))

def add_background(c, width, height, bg_url, opacity=0.15):
    """Add background image with opacity"""
    if os.path.exists(bg_url):
        img = Image.open(bg_url).convert("RGBA")
    else:
        with urllib.request.urlopen(bg_url) as response:
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

# ---------- Text Handling ----------
def draw_wrapped_text(c, x, y, text, max_width, font="Helvetica", size=11, leading=14):
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

# ---------- Page Handling ----------
def new_page(c, width, height, bg_url=None):
    """Add new page, background, and header"""
    c.showPage()
    if bg_url:
        add_background(c, width, height, bg_url, 0.15)
    # header
    c.setFillColor(colors.HexColor("#1E3A8A"))
    c.rect(0, height - 70, width, 70, fill=1)
    c.setFont("Helvetica-Bold", 20)
    c.setFillColor(colors.HexColor("#F59E0B"))
    c.drawString(40, height - 45, "Kidney Scan Report")
    return height - 100

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

# ---------- Main Report ----------
def create_report(filename, patient_info, findings, original_image_url=None, detected_image_url=None):
    c = canvas.Canvas(filename, pagesize=A4)
    width, height = A4
    bg_url = "https://encrypted-tbn0.gstatic.com/images?q=tbn:ANd9GcSu_1AZt0XZURuAVwGuLvdmaD2jzApZ7NygGA&s"

    add_background(c, width, height, bg_url, 0.15)

    # Header
    c.setFillColor(colors.HexColor("#1E3A8A"))
    c.rect(0, height - 70, width, 70, fill=1)
    c.setFont("Helvetica-Bold", 20)
    c.setFillColor(colors.HexColor("#F59E0B"))
    c.drawString(40, height - 45, "Kidney Scan Report")

    y = height - 100

    # ---------- Patient Info ----------
    c.setFont("Helvetica-Bold", 12)
    c.setFillColor(colors.HexColor("#F59E0B"))
    c.drawString(40, y, "Patient Name:")
    c.drawString(300, y, "Gender:")
    c.setFont("Helvetica", 12)
    c.setFillColor(colors.black)
    c.drawString(125, y, patient_info['name'])
    c.drawString(350, y, patient_info['gender'])
    y -= 20

    c.setFont("Helvetica-Bold", 12)
    c.setFillColor(colors.HexColor("#F59E0B"))
    c.drawString(40, y, "Patient ID:")
    c.drawString(300, y, "Age:")
    c.setFont("Helvetica", 12)
    c.setFillColor(colors.black)
    c.drawString(110, y, patient_info['id'])
    c.drawString(330, y, str(patient_info['age']))
    y -= 20

    c.setFont("Helvetica-Bold", 12)
    c.setFillColor(colors.HexColor("#F59E0B"))
    c.drawString(40, y, "Address:")
    c.drawString(300, y, "Date Of Report:")
    c.setFont("Helvetica", 12)
    c.setFillColor(colors.black)
    c.drawString(400, y, str(date.today()))
    y, _ = draw_wrapped_text(c, 100, y, patient_info['address'], width - 400)
    y -= 20

    # ---------- Findings Section ----------
    c.setStrokeColor(colors.HexColor("#FD9595"))
    c.setLineWidth(1)
    c.line(30, y, width - 30, y)
    y -= 30
    c.setFont("Helvetica-Bold", 14)
    c.setFillColor(colors.HexColor("#F59E0B"))
    c.drawString(width / 3 + 10, y, " Scanned Image Analysis")
    y -= 40

    box_x, box_width = 30, width - 60
    text_x = 50
    text_width = box_width - 200
    text_y = y

    # Collect findings
    details = [
        ("Kidney Stone Detection:", findings['detection']),
        ("Location:", findings['location']),
    ]
    if findings['detection'].lower() == "detected":
        details += [("Stone Size:", findings['stone_size']),
                    ("Number of Stones:", findings['number_of_stones'])]
    details.append(("Conclusion:", findings['conclusion']))

    # --- Dry run to calculate height ---
    temp_y = text_y
    for label, val in details:
        temp_y -= 20
        words = val.split()
        line = ""
        for word in words:
            test_line = line + word + " "
            if c.stringWidth(test_line, "Helvetica", 12) <= text_width:
                line = test_line
            else:
                temp_y -= 14
                line = word + " "
        if line:
            temp_y -= 14
        temp_y -= 15

    box_height = (y - temp_y) + 40
    box_y = y - box_height + 20

    # --- Draw rectangle ---
    c.rect(box_x, box_y, box_width, box_height)

    # --- Render findings text ---
    text_y = y - 10
    for label, val in details:
        text_y -= 20
        c.setFont("Helvetica-Bold", 12)
        c.setFillColor(colors.HexColor("#F59E0B"))
        c.drawString(text_x, text_y, label)
        c.setFont("Helvetica", 12)
        c.setFillColor(colors.black)
        text_y, _ = draw_wrapped_text(c, text_x + 160, text_y, val, text_width)
        text_y -= 15

    y = box_y - 40

    # ---------- Scanned Images ----------
    image_height = 140
    image_width = 140
    needed_height = image_height + 40
    y = check_page_space(c, y, needed_height, width, height, bg_url)

    c.setFont("Helvetica-Bold", 12)
    c.setFillColor(colors.HexColor("#F59E0B"))
    c.drawString(40, y, "Scanned Images:")

    x_start = 50
    y_image = y - 20

    if original_image_url:
        img1 = fetch_image(original_image_url)
        c.drawImage(img1, x_start, y_image - image_height, width=image_width, height=image_height, mask='auto')
        c.setFont("Helvetica", 10)
        c.setFillColor(colors.gray)
        c.drawString(x_start, y_image - image_height - 12, "Original Scan")

    if detected_image_url:
        img2 = fetch_image(detected_image_url)
        x2 = x_start + image_width + 30
        c.drawImage(img2, x2, y_image - image_height, width=image_width, height=image_height, mask='auto')
        c.setFont("Helvetica", 10)
        c.setFillColor(colors.gray)
        c.drawString(x2, y_image - image_height - 12, "AI Detected Scan")

    y -= needed_height + 20

    # ---------- Recommendations ----------
    recos = [
        "1. Drink 2-3 liters of water daily.",
        "2. Reduce salt intake.",
        "3. Avoid excessive protein-rich food.",
        "4. Follow-up with urologist in 2 weeks.",
        "5. Maintain balanced diet and exercise."
    ]
    c.setFont("Helvetica-Bold", 12)
    c.setFillColor(colors.HexColor("#F59E0B"))
    c.drawString(40, y, "Recommendation:")
    y -= 20
    c.setFont("Helvetica", 12)
    c.setFillColor(colors.black)
    for rec in recos:
        y = check_page_space(c, y, 20, width, height, bg_url)
        c.drawString(60, y, rec)
        y -= 20

    # ---------- Footer ----------
    y = check_page_space(c, y, 60, width, height, bg_url)
    c.setFont("Helvetica", 10)
    c.setFillColor(colors.gray)
    c.drawString(40, 70, "This report is generated by AI and is intended for clinical review by a qualified healthcare professional.")
    c.setFillColor(colors.HexColor("#F59E0B"))
    c.setFont("Helvetica-Bold", 12)
    c.drawString(width - 140, 40, "Powered By LithoLens")

    c.save()
    webbrowser.open_new(r'file://' + os.path.abspath(filename))



