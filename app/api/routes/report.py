from fastapi import APIRouter, Request, HTTPException
from fastapi.responses import Response
import logging
from app.services.pdf_service import generate_pdf

router = APIRouter()
logger = logging.getLogger(__name__)

@router.post("/generate-report")
async def generate_report(request: Request):
    try:
        body = await request.json()
        
        # Validate that body is a dictionary
        if not isinstance(body, dict):
            logger.error(f"Invalid request body type: {type(body)}")
            raise HTTPException(status_code=400, detail="Invalid request data")
        
        logger.info(f"Generating PDF with data: {body}")
        pdf_bytes = generate_pdf(body)
        
        headers = {"Content-Disposition": "attachment; filename=medical_report.pdf"}
        return Response(content=pdf_bytes, media_type="application/pdf", headers=headers)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Report generation error: {e}")
        raise HTTPException(status_code=500, detail="Failed to generate report")