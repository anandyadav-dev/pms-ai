import io
from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib.units import inch
from datetime import datetime

def generate_pdf(body: dict) -> bytes:
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=letter, rightMargin=40, leftMargin=40, topMargin=40, bottomMargin=40)
    styles = getSampleStyleSheet()
    story = []
    header_style = ParagraphStyle('Header', parent=styles['Heading1'], fontSize=24, textColor=colors.HexColor('#2c3e50'), alignment=1, spaceAfter=10)
    sub_header_style = ParagraphStyle('SubHeader', parent=styles['Normal'], fontSize=10, textColor=colors.HexColor('#7f8c8d'), alignment=1, spaceAfter=30)
    section_header_style = ParagraphStyle('SectionHeader', parent=styles['Heading2'], fontSize=14, textColor=colors.HexColor('#34495e'), spaceBefore=15, spaceAfter=10, borderPadding=5, borderColor=colors.HexColor('#bdc3c7'), borderWidth=0, backColor=colors.HexColor('#ecf0f1'))
    story.append(Paragraph("PMS AI MEDICAL CENTER", header_style))
    story.append(Paragraph("123 Health Avenue, Medical District, Tech City - 560001<br/>Phone: +91 98765 43210 | Email: contact@pms-ai.com", sub_header_style))
    story.append(Spacer(1, 10))
    patient_data = [
        [Paragraph(f"<b>Patient Name:</b> {body.get('patient_name') or 'N/A'}", styles['Normal']),
         Paragraph(f"<b>Date:</b> {datetime.now().strftime('%d-%b-%Y')}", styles['Normal'])],
        [Paragraph(f"<b>Age/Gender:</b> {body.get('age') or '--'} / {body.get('gender') or '--'}", styles['Normal']),
         Paragraph(f"<b>Doctor:</b> {body.get('doctor_name') or 'Dr. AI Assistant'}", styles['Normal'])],
        [Paragraph(f"<b>Patient ID:</b> #PMS-{datetime.now().strftime('%Y%m%d%H%M')}", styles['Normal']),
         Paragraph(f"<b>Consultation Type:</b> General", styles['Normal'])],
    ]
    t_info = Table(patient_data, colWidths=[3.5*inch, 3.5*inch])
    t_info.setStyle(TableStyle([('BOX', (0,0), (-1,-1), 1, colors.HexColor('#bdc3c7')), ('INNERGRID', (0,0), (-1,-1), 0.5, colors.HexColor('#ecf0f1')), ('TOPPADDING', (0,0), (-1,-1), 8), ('BOTTOMPADDING', (0,0), (-1,-1), 8), ('LEFTPADDING', (0,0), (-1,-1), 12)]))
    story.append(t_info)
    story.append(Spacer(1, 20))
    story.append(Paragraph("Clinical Assessment", section_header_style))
    symptoms = body.get("symptoms") or []
    symptoms_text = ", ".join(symptoms) if symptoms else "No symptoms recorded."
    story.append(Paragraph(f"<b>Symptoms Reported:</b><br/>{symptoms_text}", styles['Normal']))
    story.append(Spacer(1, 10))
    story.append(Paragraph(f"<b>Diagnosis:</b> {body.get('diagnosis') or 'Pending Evaluation'}", styles['Normal']))
    story.append(Spacer(1, 5))
    story.append(Paragraph(f"<b>Checkup Details:</b> {body.get('checkup_details') or 'Routine checkup performed.'}", styles['Normal']))
    story.append(Spacer(1, 20))
    story.append(Paragraph("Prescription / Rx", section_header_style))
    medicines = body.get("medicines") or []
    if medicines:
        med_data = [['Medicine Name', 'Dosage', 'Frequency', 'Duration']]
        for m in medicines:
            med_data.append([Paragraph(m.get("name") or "Unknown", styles['Normal']), m.get("dose") or "--", m.get("frequency") or "--", m.get("duration") or "5 Days"])
        t_meds = Table(med_data, colWidths=[3*inch, 1.5*inch, 1.5*inch, 1*inch])
        t_meds.setStyle(TableStyle([('BACKGROUND', (0,0), (-1,0), colors.HexColor('#3498db')), ('TEXTCOLOR', (0,0), (-1,0), colors.whitesmoke), ('ALIGN', (0,0), (-1,-1), 'LEFT'), ('FONTNAME', (0,0), (-1,0), 'Helvetica-Bold'), ('FONTSIZE', (0,0), (-1,0), 10), ('BOTTOMPADDING', (0,0), (-1,0), 10), ('BACKGROUND', (0,1), (-1,-1), colors.HexColor('#f8f9fa')), ('GRID', (0,0), (-1,-1), 1, colors.HexColor('#bdc3c7')), ('TOPPADDING', (0,0), (-1,-1), 8), ('BOTTOMPADDING', (0,0), (-1,-1), 8)]))
        story.append(t_meds)
    else:
        story.append(Paragraph("No medicines prescribed.", styles['Normal']))
    story.append(Spacer(1, 30))
    story.append(Spacer(1, 20))
    footer_data = [[Paragraph("<b>Notes:</b><br/>Take rest and drink plenty of water. Follow up after 5 days if symptoms persist.", styles['Normal'])], [Spacer(1, 30)], [Paragraph("_______________________<br/><b>Dr. AI Assistant</b><br/>Chief Medical Officer", ParagraphStyle('Signature', parent=styles['Normal'], alignment=2))]]
    t_footer = Table(footer_data, colWidths=[7*inch])
    t_footer.setStyle(TableStyle([('ALIGN', (0,-1), (-1,-1), 'RIGHT')]))
    story.append(t_footer)
    doc.build(story)
    pdf_bytes = buffer.getvalue()
    buffer.close()
    return pdf_bytes