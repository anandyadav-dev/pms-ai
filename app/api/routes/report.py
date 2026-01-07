from fastapi import APIRouter, Request
from fastapi.responses import Response
from app.services.pdf_service import generate_pdf

router = APIRouter()

@router.post("/generate-report")
async def generate_report(request: Request):
    body = await request.json()
    pdf_bytes = generate_pdf(body)
    headers = {"Content-Disposition": "attachment; filename=medical_report.pdf"}
    return Response(content=pdf_bytes, media_type="application/pdf", headers=headers)