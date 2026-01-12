from fastapi import APIRouter, UploadFile, File, Request, HTTPException
from fastapi.responses import StreamingResponse
import logging
import json
from typing import Dict, Any
from app.services.openai_client import OpenAIClient

router = APIRouter()
logger = logging.getLogger(__name__)

ALLOWED_EXTENSIONS = {".jpg", ".jpeg", ".png", ".bmp", ".tiff"}
MAX_FILE_SIZE = 10 * 1024 * 1024  # 10MB

def validate_file(file: UploadFile) -> None:
    if not file.filename:
        raise HTTPException(status_code=400, detail="No filename provided")
    
    file_ext = file.filename.lower().split('.')[-1]
    if f".{file_ext}" not in ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=400, 
            detail=f"File type not allowed. Allowed types: {', '.join(ALLOWED_EXTENSIONS)}"
        )
    
    if file.size and file.size > MAX_FILE_SIZE:
        raise HTTPException(
            status_code=400,
            detail=f"File too large. Maximum size: {MAX_FILE_SIZE // (1024*1024)}MB"
        )

@router.post("/analyze-prescription-stream")
async def analyze_prescription_stream(request: Request, file: UploadFile = File(...)):
    validate_file(file)
    
    ai_client: OpenAIClient = getattr(request.app.state, "ai_client", None)
    if not ai_client:
        raise HTTPException(status_code=500, detail="AI Client not initialized")
    
    try:
        contents = await file.read()
        if len(contents) > MAX_FILE_SIZE:
            raise HTTPException(
                status_code=400,
                detail=f"File too large. Maximum size: {MAX_FILE_SIZE // (1024*1024)}MB"
            )
        
        async def generate_response():
            full_response = ""
            
            # Stream the analysis
            async for chunk in ai_client.analyze_prescription_stream(contents):
                full_response += chunk
                yield f"data: {chunk}\n\n"
            
            yield "data: [DONE]\n\n"
            
            # Extract structured data from complete response
            try:
                extracted_data = ai_client.extract_patient_info(full_response, {})
                logger.info(f"Extracted data from streaming: {extracted_data}")
                yield f"data: [EXTRACTED_DATA]{json.dumps(extracted_data)}\n\n"
            except Exception as e:
                logger.error(f"Data extraction error: {e}")
                yield f"data: [EXTRACTED_DATA]{{}}\n\n"
        
        return StreamingResponse(
            generate_response(),
            media_type="text/plain",
            headers={
                "Cache-Control": "no-cache",
                "Connection": "keep-alive",
                "Access-Control-Allow-Origin": "*"
            }
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Prescription streaming error: {e}")
        raise HTTPException(status_code=500, detail="Failed to analyze prescription")
