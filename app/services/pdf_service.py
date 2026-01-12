import io
from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib.units import inch
from datetime import datetime

def generate_pdf(body: dict) -> bytes:
    import logging
    logger = logging.getLogger(__name__)
    
    logger.info(f"PDF generation started with data: {body}")
    
    try:
        # Validate input data
        if not body or not isinstance(body, dict):
            logger.error("Invalid input data for PDF generation")
            body = {}
        
        buffer = io.BytesIO()
        doc = SimpleDocTemplate(buffer, pagesize=letter, rightMargin=40, leftMargin=40, topMargin=40, bottomMargin=40)
        styles = getSampleStyleSheet()
        story = []
        
        # Header styles
        header_style = ParagraphStyle('Header', parent=styles['Heading1'], fontSize=24, textColor=colors.HexColor('#2c3e50'), alignment=1, spaceAfter=10)
        sub_header_style = ParagraphStyle('SubHeader', parent=styles['Normal'], fontSize=10, textColor=colors.HexColor('#7f8c8d'), alignment=1, spaceAfter=30)
        section_header_style = ParagraphStyle('SectionHeader', parent=styles['Heading2'], fontSize=14, textColor=colors.HexColor('#34495e'), spaceBefore=15, spaceAfter=10, borderPadding=5, borderColor=colors.HexColor('#bdc3c7'), borderWidth=0, backColor=colors.HexColor('#ecf0f1'))
        
        # Header
        story.append(Paragraph("PMS AI MEDICAL CENTER", header_style))
        story.append(Paragraph("123 Health Avenue, Medical District, Tech City - 560001<br/>Phone: +91 98765 43210 | Email: contact@pms-ai.com", sub_header_style))
        story.append(Spacer(1, 10))
        
        # Patient Information
        patient_name = str(body.get('patient_name', 'N/A'))
        current_date = datetime.now().strftime('%d-%b-%Y')
        age = str(body.get('age', '--'))
        gender = str(body.get('gender', '--'))
        doctor_name = str(body.get('doctor_name', 'Dr. AI Assistant'))
        patient_id = f"#PMS-{datetime.now().strftime('%Y%m%d%H%M')}"
        
        patient_data = [
            [Paragraph(f"<b>Patient Name:</b> {patient_name}", styles['Normal']),
             Paragraph(f"<b>Date:</b> {current_date}", styles['Normal'])],
            [Paragraph(f"<b>Age/Gender:</b> {age} / {gender}", styles['Normal']),
             Paragraph(f"<b>Doctor:</b> {doctor_name}", styles['Normal'])],
            [Paragraph(f"<b>Patient ID:</b> {patient_id}", styles['Normal']),
             Paragraph(f"<b>Consultation Type:</b> General", styles['Normal'])],
        ]
        t_info = Table(patient_data, colWidths=[3.5*inch, 3.5*inch])
        t_info.setStyle(TableStyle([
            ('BOX', (0,0), (-1,-1), 1, colors.HexColor('#bdc3c7')), 
            ('INNERGRID', (0,0), (-1,-1), 0.5, colors.HexColor('#ecf0f1')), 
            ('TOPPADDING', (0,0), (-1,-1), 8), 
            ('BOTTOMPADDING', (0,0), (-1,-1), 8), 
            ('LEFTPADDING', (0,0), (-1,-1), 12)
        ]))
        story.append(t_info)
        story.append(Spacer(1, 20))
        
        # Clinical Assessment
        story.append(Paragraph("Clinical Assessment", section_header_style))
        symptoms = body.get("symptoms", [])
        if not isinstance(symptoms, list):
            symptoms = []
        symptoms_text = ", ".join(str(s) for s in symptoms) if symptoms else "No symptoms recorded."
        story.append(Paragraph(f"<b>Symptoms Reported:</b><br/>{symptoms_text}", styles['Normal']))
        story.append(Spacer(1, 10))
        
        diagnosis = str(body.get('diagnosis', 'Pending Evaluation'))
        story.append(Paragraph(f"<b>Diagnosis:</b> {diagnosis}", styles['Normal']))
        story.append(Spacer(1, 5))
        
        checkup_details = str(body.get('checkup_details', 'Routine checkup performed.'))
        story.append(Paragraph(f"<b>Checkup Details:</b> {checkup_details}", styles['Normal']))
        story.append(Spacer(1, 20))
        
        # Medical Tests
        story.append(Paragraph("Medical Tests", section_header_style))
        tests = body.get("medical_tests", [])
        if not isinstance(tests, list):
            tests = []
        if tests:
            test_data = [['Test Name', 'Details']]
            for t in tests:
                if isinstance(t, dict):
                    test_name = str(t.get("name", "Unknown"))
                    test_details = str(t.get("details", "--"))
                else:
                    test_name = str(t)
                    test_details = "--"
                test_data.append([Paragraph(test_name, styles['Normal']), test_details])
            t_tests = Table(test_data, colWidths=[3.5*inch, 3.5*inch])
            t_tests.setStyle(TableStyle([
                ('BACKGROUND', (0,0), (-1,0), colors.HexColor('#3498db')),
                ('TEXTCOLOR', (0,0), (-1,0), colors.whitesmoke),
                ('ALIGN', (0,0), (-1,-1), 'LEFT'),
                ('FONTNAME', (0,0), (-1,0), 'Helvetica-Bold'),
                ('FONTSIZE', (0,0), (-1,0), 10),
                ('BOTTOMPADDING', (0,0), (-1,0), 10),
                ('BACKGROUND', (0,1), (-1,-1), colors.HexColor('#f8f9fa')),
                ('GRID', (0,0), (-1,-1), 1, colors.HexColor('#bdc3c7')),
                ('TOPPADDING', (0,0), (-1,-1), 8),
                ('BOTTOMPADDING', (0,0), (-1,-1), 8)
            ]))
            story.append(t_tests)
        else:
            story.append(Paragraph("No medical tests recommended.", styles['Normal']))
        story.append(Spacer(1, 20))
        
        # Prescription
        story.append(Paragraph("Prescription / Rx", section_header_style))
        medicines = body.get("medicines", [])
        if not isinstance(medicines, list):
            medicines = []
        if medicines:
            med_data = [['Medicine Name', 'Dosage', 'Frequency', 'Duration']]
            for m in medicines:
                if isinstance(m, dict):
                    med_name = str(m.get("name", "Unknown"))
                    med_dose = str(m.get("dose", "--"))
                    med_frequency = str(m.get("frequency", "--"))
                    med_duration = str(m.get("duration", "5 Days"))
                else:
                    med_name = str(m)
                    med_dose = "--"
                    med_frequency = "--"
                    med_duration = "5 Days"
                med_data.append([Paragraph(med_name, styles['Normal']), med_dose, med_frequency, med_duration])
            t_meds = Table(med_data, colWidths=[3*inch, 1.5*inch, 1.5*inch, 1*inch])
            t_meds.setStyle(TableStyle([
                ('BACKGROUND', (0,0), (-1,0), colors.HexColor('#3498db')), 
                ('TEXTCOLOR', (0,0), (-1,0), colors.whitesmoke), 
                ('ALIGN', (0,0), (-1,-1), 'LEFT'), 
                ('FONTNAME', (0,0), (-1,0), 'Helvetica-Bold'), 
                ('FONTSIZE', (0,0), (-1,0), 10), 
                ('BOTTOMPADDING', (0,0), (-1,0), 10), 
                ('BACKGROUND', (0,1), (-1,-1), colors.HexColor('#f8f9fa')), 
                ('GRID', (0,0), (-1,-1), 1, colors.HexColor('#bdc3c7')), 
                ('TOPPADDING', (0,0), (-1,-1), 8), 
                ('BOTTOMPADDING', (0,0), (-1,-1), 8)
            ]))
            story.append(t_meds)
        else:
            story.append(Paragraph("No medicines prescribed.", styles['Normal']))
        story.append(Spacer(1, 30))
        story.append(Spacer(1, 20))
        
        # Generate simple notes
        notes = []
        
        # Handle notes from patient data - ensure it's a list for Pydantic
        patient_notes = body.get("notes", [])
        if isinstance(patient_notes, str):
            # If notes is a string, split by newlines or commas
            if '\n' in patient_notes:
                notes = [note.strip() for note in patient_notes.split('\n') if note.strip()]
            elif ',' in patient_notes:
                notes = [note.strip() for note in patient_notes.split(',') if note.strip()]
            else:
                # Single long note - split into sentences
                sentences = [s.strip() + '.' for s in patient_notes.split('.') if s.strip()]
                notes = [s for s in sentences if s and s != '.']
        elif isinstance(patient_notes, list):
            notes = [str(note).strip() for note in patient_notes if str(note).strip()]
        else:
            notes = []
        
        # Add default notes if no notes provided
        if not notes:
            notes = ["Take rest and drink plenty of water", "Follow up after 5 days if symptoms persist"]
        
        notes_text = "<br/>".join(f"• {note}" for note in notes)
        
        # Footer
        footer_data = [[Paragraph(f"<b>Notes:</b><br/>{notes_text}", styles['Normal'])], [Spacer(1, 30)], [Paragraph("_______________________<br/><b>Dr. AI Assistant</b><br/>Chief Medical Officer", ParagraphStyle('Signature', parent=styles['Normal'], alignment=2))]]
        t_footer = Table(footer_data, colWidths=[7*inch])
        t_footer.setStyle(TableStyle([('ALIGN', (0,-1), (-1,-1), 'RIGHT')]))
        story.append(t_footer)
        
        # Build PDF
        logger.info("Building PDF document...")
        doc.build(story)
        
        pdf_bytes = buffer.getvalue()
        buffer.close()
        
        # Validate PDF bytes
        pdf_size = len(pdf_bytes)
        logger.info(f"PDF generated successfully. Size: {pdf_size} bytes")
        
        if pdf_size == 0:
            raise ValueError("Generated PDF is empty")
        
        # Check if it looks like a valid PDF (starts with %PDF)
        if not pdf_bytes.startswith(b'%PDF'):
            logger.error("Generated data is not a valid PDF")
            raise ValueError("Generated data is not a valid PDF")
        
        return pdf_bytes
        
    except Exception as e:
        logger.error(f"PDF generation error: {e}")
        # Return a simple PDF as fallback
        try:
            buffer = io.BytesIO()
            doc = SimpleDocTemplate(buffer, pagesize=letter)
            story = [Paragraph("Error generating detailed PDF. Please try again.", getSampleStyleSheet()['Normal'])]
            doc.build(story)
            fallback_bytes = buffer.getvalue()
            buffer.close()
            logger.info("Fallback PDF generated")
            return fallback_bytes
        except Exception as fallback_error:
            logger.error(f"Fallback PDF generation failed: {fallback_error}")
            # Return minimal PDF bytes
            return b'%PDF-1.4\n1 0 obj\n<<\n/Length 44\nstream\nBT\n/F1 12 Tf 72 770 Td\n(Error generating PDF) Tj\nET\nendstream\nendobj\ntrailer\n<<\n/Root 1 0 R\n>>\nstartxref\n1\n%%EOF'
