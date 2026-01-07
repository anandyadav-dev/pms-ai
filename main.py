from fastapi import FastAPI, UploadFile, File, WebSocket, WebSocketDisconnect, Request
from fastapi.responses import HTMLResponse, JSONResponse, Response
from fastapi.middleware.cors import CORSMiddleware
from openai_client import OpenAIClient
import os
import io
import json
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib.units import inch
from datetime import datetime

app = FastAPI(title="PMS AI - Prescription & Voice Assistant")

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize OpenAI Client safely
try:
    ai_client = OpenAIClient()
except Exception as e:
    print(f"Warning: AI Client failed to initialize. Check API Key. {e}")
    ai_client = None


@app.post("/analyze-prescription")
async def analyze_prescription(file: UploadFile = File(...)):
    if not ai_client:
        return JSONResponse(
            status_code=500,
            content={"error": "AI Client not initialized"}
        )

    try:
        contents = await file.read()
        analysis = ai_client.analyze_prescription(contents)
        # Extract structured data from the analysis text
        extracted_data = ai_client.extract_patient_info(analysis, {})
        return {"analysis": analysis, "extracted_data": extracted_data}
    except Exception as e:
        return JSONResponse(status_code=500, content={"error": str(e)})


@app.websocket("/ws/voice-assistant")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()

    if not ai_client:
        await websocket.send_text("Error: AI Client not initialized. Please check server logs.")
        await websocket.close()
        return

    try:
        patient_record = {}
        while True:
            data = await websocket.receive_text()
            try:
                patient_record = ai_client.extract_patient_info(data, patient_record)
                await websocket.send_text("DATA_UPDATE:" + json.dumps(patient_record))
            except Exception:
                pass
            # response_text = ai_client.chat_response(data)
            # await websocket.send_text(response_text)

    except WebSocketDisconnect:
        print("Client disconnected")

    except Exception as e:
        print(f"WebSocket Error: {e}")
        try:
            await websocket.close()
        except:
            pass

# Serve frontend
@app.get("/")
async def get():
    with open("templates/index.html", "r", encoding="utf-8") as f:
        html_content = f.read()
    return HTMLResponse(content=html_content, status_code=200)

@app.post("/generate-report")
async def generate_report(request: Request):
    body = await request.json()
    buffer = io.BytesIO()
    
    doc = SimpleDocTemplate(
        buffer,
        pagesize=letter,
        rightMargin=40,
        leftMargin=40,
        topMargin=40,
        bottomMargin=40
    )

    styles = getSampleStyleSheet()
    story = []

    # --- Header Style ---
    header_style = ParagraphStyle(
        'Header',
        parent=styles['Heading1'],
        fontSize=24,
        textColor=colors.HexColor('#2c3e50'),
        alignment=1,  # Center
        spaceAfter=10
    )
    
    sub_header_style = ParagraphStyle(
        'SubHeader',
        parent=styles['Normal'],
        fontSize=10,
        textColor=colors.HexColor('#7f8c8d'),
        alignment=1,  # Center
        spaceAfter=30
    )

    section_header_style = ParagraphStyle(
        'SectionHeader',
        parent=styles['Heading2'],
        fontSize=14,
        textColor=colors.HexColor('#34495e'),
        spaceBefore=15,
        spaceAfter=10,
        borderPadding=5,
        borderColor=colors.HexColor('#bdc3c7'),
        borderWidth=0,
        backColor=colors.HexColor('#ecf0f1')
    )

    # --- 1. Hospital Header ---
    story.append(Paragraph("PMS AI MEDICAL CENTER", header_style))
    story.append(Paragraph("123 Health Avenue, Medical District, Tech City - 560001<br/>Phone: +91 98765 43210 | Email: contact@pms-ai.com", sub_header_style))
    story.append(Spacer(1, 10))

    # --- 2. Patient Info Grid ---
    # Create a table for patient details
    patient_data = [
        [
            Paragraph(f"<b>Patient Name:</b> {body.get('patient_name') or 'N/A'}", styles['Normal']),
            Paragraph(f"<b>Date:</b> {datetime.now().strftime('%d-%b-%Y')}", styles['Normal'])
        ],
        [
            Paragraph(f"<b>Age/Gender:</b> {body.get('age') or '--'} / {body.get('gender') or '--'}", styles['Normal']),
            Paragraph(f"<b>Doctor:</b> {body.get('doctor_name') or 'Dr. AI Assistant'}", styles['Normal'])
        ],
        [
            Paragraph(f"<b>Patient ID:</b> #PMS-{datetime.now().strftime('%Y%m%d%H%M')}", styles['Normal']),
            Paragraph(f"<b>Consultation Type:</b> General", styles['Normal'])
        ]
    ]

    t_info = Table(patient_data, colWidths=[3.5*inch, 3.5*inch])
    t_info.setStyle(TableStyle([
        ('BOX', (0,0), (-1,-1), 1, colors.HexColor('#bdc3c7')),
        ('INNERGRID', (0,0), (-1,-1), 0.5, colors.HexColor('#ecf0f1')),
        ('TOPPADDING', (0,0), (-1,-1), 8),
        ('BOTTOMPADDING', (0,0), (-1,-1), 8),
        ('LEFTPADDING', (0,0), (-1,-1), 12),
    ]))
    story.append(t_info)
    story.append(Spacer(1, 20))

    # --- 3. Vitals & Symptoms ---
    story.append(Paragraph("Clinical Assessment", section_header_style))
    
    # Symptoms
    symptoms = body.get("symptoms") or []
    symptoms_text = ", ".join(symptoms) if symptoms else "No symptoms recorded."
    story.append(Paragraph(f"<b>Symptoms Reported:</b><br/>{symptoms_text}", styles['Normal']))
    story.append(Spacer(1, 10))

    # Diagnosis & Checkup
    story.append(Paragraph(f"<b>Diagnosis:</b> {body.get('diagnosis') or 'Pending Evaluation'}", styles['Normal']))
    story.append(Spacer(1, 5))
    story.append(Paragraph(f"<b>Checkup Details:</b> {body.get('checkup_details') or 'Routine checkup performed.'}", styles['Normal']))
    story.append(Spacer(1, 20))

    # --- 4. Prescriptions (Table) ---
    story.append(Paragraph("Prescription / Rx", section_header_style))

    medicines = body.get("medicines") or []
    if medicines:
        med_data = [['Medicine Name', 'Dosage', 'Frequency', 'Duration']]
        for m in medicines:
            med_data.append([
                Paragraph(m.get("name") or "Unknown", styles['Normal']),
                m.get("dose") or "--",
                m.get("frequency") or "--",
                m.get("duration") or "5 Days" # Default duration if not present
            ])
        
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
            ('BOTTOMPADDING', (0,0), (-1,-1), 8),
        ]))
        story.append(t_meds)
    else:
        story.append(Paragraph("No medicines prescribed.", styles['Normal']))

    story.append(Spacer(1, 30))

    # --- 5. Footer ---
    story.append(Spacer(1, 20))
    
    footer_data = [
        [Paragraph("<b>Notes:</b><br/>Take rest and drink plenty of water. Follow up after 5 days if symptoms persist.", styles['Normal'])],
        [Spacer(1, 30)],
        [Paragraph("_______________________<br/><b>Dr. AI Assistant</b><br/>Chief Medical Officer", ParagraphStyle('Signature', parent=styles['Normal'], alignment=2))]
    ]
    t_footer = Table(footer_data, colWidths=[7*inch])
    t_footer.setStyle(TableStyle([
        ('ALIGN', (0,-1), (-1,-1), 'RIGHT'),
    ]))
    story.append(t_footer)

    # Build PDF
    doc.build(story)
    
    pdf_bytes = buffer.getvalue()
    buffer.close()
    headers = {"Content-Disposition": "attachment; filename=medical_report.pdf"}
    return Response(content=pdf_bytes, media_type="application/pdf", headers=headers)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
