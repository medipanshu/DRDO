from reportlab.lib.pagesizes import A4
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Image, Table, TableStyle, PageBreak
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib import colors
from reportlab.lib.units import inch
from reportlab.lib.enums import TA_CENTER
from datetime import datetime
import os
from PIL import Image as PILImage, ImageDraw, ImageFont
from io import BytesIO

def generate_pdf_report(
    pdf_path,
    original_image_path,
    detected_image_path,
    checklist,
    inspector_name="Inspector Name",
    signature_path=None,
    logo_path="Assets/DRDOLogo.png"
):
    doc = SimpleDocTemplate(pdf_path, pagesize=A4,
                            rightMargin=50, leftMargin=50,
                            topMargin=50, bottomMargin=50)
    styles = getSampleStyleSheet()
    story = []

    # --- Centered Logo ---
    logo_width = 60
    logo_height = 60
    if os.path.exists(logo_path):
        logo = Image(logo_path, width=logo_width, height=logo_height)
        logo.hAlign = 'CENTER'
        story.append(logo)
    else:
        story.append(Spacer(1, logo_height))

    story.append(Spacer(1, 10))

    # --- Centered Title ---
    title_style = styles["Title"].clone('centeredTitle')
    title_style.alignment = 1  # 1 = TA_CENTER
    title = Paragraph("<b><font size=18>Welding Defect Report</font></b>", title_style)
    story.append(title)
    story.append(Spacer(1, 12))

    # Date and Time
    now = datetime.now()
    date_str = now.strftime("%d-%b-%Y")
    time_str = now.strftime("%H:%M:%S")
    datetime_table = [[f"Date: {date_str}", f"Time: {time_str}"]]
    dt_table = Table(datetime_table, colWidths=[250, 250])
    dt_table.setStyle(TableStyle([
        ('ALIGN', (1, 0), (1, 0), 'RIGHT'),  # Align the second column (time) to the right
    ]))
    story.append(dt_table)
    story.append(Spacer(1, 20))

    # Images
    img_table = []
    if os.path.exists(original_image_path):
        orig_img = Image(original_image_path, width=220, height=160)
    else:
        orig_img = Paragraph("No Original Image", styles["Normal"])

    if os.path.exists(original_image_path):
        # det_img = Image(detected_image_path, width=220, height=160)
        det_img_pil = PILImage.open(detected_image_path).convert("RGB")
        draw = ImageDraw.Draw(det_img_pil)
        try:
            font = ImageFont.truetype("arial.ttf", 18)
        except:
            font = ImageFont.load_default()

        for item in checklist:
            defect = item.get("defect_class", "Defect")
            bbox = item.get("bbox")
            shape_type = item.get("shape_type")
            points = item.get("points")
            color = (255, 0, 0)  # Red for defects

            if bbox:
                x, y, w, h = map(int, bbox)
                draw.rectangle([x, y, x + w, y + h], outline=color, width=3)
                draw.text((x, y - 20), str(defect), fill=color, font=font)
                
            elif shape_type in ("polygon", "freehand") and points:
                pts = [(int(p.x()), int(p.y())) for p in points]
                if len(pts) > 1:
                    draw.line(pts + [pts[0]], fill=color, width=3)
                if pts:
                    draw.text(pts[0], str(defect), fill=color, font=font)

        # Save to BytesIO buffer
        det_img_buffer = BytesIO()
        det_img_pil.save(det_img_buffer, format="PNG")
        det_img_buffer.seek(0)
        det_img = Image(det_img_buffer, width=220, height=160)

    else:
        det_img = Paragraph("No Detected Image", styles["Normal"])

    # Define a centered paragraph style
    centered_style = styles["Normal"].clone('centeredStyle')
    centered_style.alignment = TA_CENTER

    img_table.append([
        Paragraph("<b>Original Image</b>", centered_style),
        Paragraph("<b>Detected Image</b>", centered_style)
    ])
    img_table.append([orig_img, det_img])

    img_table_obj = Table(img_table, colWidths=[260, 260])
    img_table_obj.setStyle(TableStyle([
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),  # Center all cells
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
    ]))
    story.append(img_table_obj)
    story.append(Spacer(1, 20))

    # Defect List Table
    story.append(Paragraph("<b>Detected Defects</b>", styles["Heading3"]))
    story.append(Spacer(1, 10))

    if not checklist:
        story.append(Paragraph("No defects detected.", styles["Normal"]))
    else:
        defect_data = [["#", "Defect Type", "Confidence", "Coordinates / Points"]]
        for idx, item in enumerate(checklist, 1):
            defect = item.get("defect_class", "Unknown")
            conf = f"{item.get('confidence', '-'):.2f}" if isinstance(item.get("confidence"), float) else "-"
            bbox = item.get("bbox")
            shape_type = item.get("shape_type")
            points = item.get("points")
            if bbox:
                coord = f"x={bbox[0]}, y={bbox[1]}, w={bbox[2]}, h={bbox[3]}"
                coord_paragraph = Paragraph(coord, styles["Normal"])
            elif shape_type in ("polygon", "freehand") and points:
                pts_list = [f"({int(p.x())},{int(p.y())})" for p in points]
                # Wrap every 4 points per line for better readability
                pts_wrapped = "<br/>".join([", ".join(pts_list[i:i+4]) for i in range(0, len(pts_list), 4)])
                coord_paragraph = Paragraph(f"Points:<br/>{pts_wrapped}", styles["Normal"])
            else:
                coord_paragraph = Paragraph("No coordinates", styles["Normal"])

            defect_data.append([str(idx), defect, conf, coord_paragraph])

        table = Table(defect_data, colWidths=[30, 130, 80, 240])
        table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor("#d3d3d3")),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.black),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ]))
        story.append(table)

    story.append(Spacer(1, 50))

    # Inspector Name and Signature
    inspector_table = [[
        Paragraph("<b>Inspector Name:</b>", styles["Normal"]),
        Paragraph(inspector_name, styles["Normal"])
    ]]
    if signature_path and os.path.exists(signature_path):
        sign_img = Image(signature_path, width=80, height=40)
        inspector_table.append([Paragraph("<b>Signature:</b>", styles["Normal"]), sign_img])

    inspector_table_obj = Table(inspector_table, colWidths=[100, 390])
    inspector_table_obj.setStyle(TableStyle([
        ('ALIGN', (1, 0), (1, -1), 'LEFT'),  # Align the right column (name/signature) to the left
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
    ]))
    story.append(inspector_table_obj)
    story.append(Spacer(1, 20))

    # Footer with page number
    def add_page_number(canvas_doc, doc_obj):
        page_num = canvas_doc.getPageNumber()
        text = f"Page {page_num}"
        canvas_doc.setFont('Helvetica', 9)
        canvas_doc.drawRightString(545, 20, text)

    doc.build(story, onFirstPage=add_page_number, onLaterPages=add_page_number)

# --- Example usage for testing ---
if __name__ == "__main__":
    checklist = [
        {"defect_class": "crack", "confidence": 0.92, "bbox": (100, 120, 50, 60)},
        {"defect_class": "porosity", "confidence": 0.81, "bbox": (200, 220, 40, 30)},
    ]
    generate_pdf_report(
        "welding_defect_report.pdf",
        "Assets/box1.png",
        "Assets/box2.png",
        checklist,
        inspector_name= "XYZ",
        signature_path="Assets/signatur.png",
        logo_path="Assets/DRDOLogo.png"
    )
