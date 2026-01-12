from fastapi import APIRouter, UploadFile, File, Request, HTTPException
from fastapi.responses import JSONResponse
import logging
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

def clean_extracted_data(data: Dict[str, Any]) -> Dict[str, Any]:
    """Clean and convert OpenAI response to match expected format"""
    if not isinstance(data, dict):
        return {}
    
    cleaned = {}
    
    # Handle basic fields
    for field in ['patient_name', 'age', 'gender', 'doctor_name', 'checkup_details', 'diagnosis']:
        if field in data and data[field] is not None and data[field] != "":
            cleaned[field] = str(data[field])
        else:
            cleaned[field] = None
    
    # Handle date conversion
    if 'checkup_date' in data and data['checkup_date'] and data['checkup_date'] != "":
        try:
            from datetime import datetime
            # Try different date formats
            date_str = str(data['checkup_date'])
            for fmt in ['%d/%m/%y', '%d/%m/%Y', '%Y-%m-%d', '%d-%m-%Y']:
                try:
                    cleaned['checkup_date'] = datetime.strptime(date_str, fmt)
                    break
                except ValueError:
                    continue
            else:
                cleaned['checkup_date'] = None
        except:
            cleaned['checkup_date'] = None
    else:
        cleaned['checkup_date'] = None
    
    # Handle list fields
    for field in ['symptoms', 'notes']:
        if field in data and data[field] is not None:
            if isinstance(data[field], str) and data[field].strip():
                cleaned[field] = [data[field].strip()]
            elif isinstance(data[field], list):
                cleaned[field] = [str(item).strip() for item in data[field] if item and str(item).strip()]
            else:
                cleaned[field] = []
        else:
            cleaned[field] = []
    
    # Handle medicines
    if 'medicines' in data and data['medicines']:
        if isinstance(data['medicines'], list):
            cleaned['medicines'] = []
            for med in data['medicines']:
                if isinstance(med, dict):
                    med_name = med.get('name', '').strip()
                    if med_name:
                        cleaned['medicines'].append({
                            'name': med_name,
                            'dose': str(med.get('dose', '')).strip() if med.get('dose') else None,
                            'frequency': str(med.get('frequency', '')).strip() if med.get('frequency') else None,
                            'duration': str(med.get('duration', '')).strip() if med.get('duration') else None
                        })
                elif isinstance(med, str) and med.strip():
                    cleaned['medicines'].append({'name': med.strip(), 'dose': None, 'frequency': None, 'duration': None})
        else:
            cleaned['medicines'] = []
    else:
        cleaned['medicines'] = []
    
    # Handle medical_tests
    if 'medical_tests' in data and data['medical_tests']:
        if isinstance(data['medical_tests'], list):
            cleaned['medical_tests'] = []
            for test in data['medical_tests']:
                if isinstance(test, dict):
                    test_name = test.get('name', '').strip()
                    if test_name:
                        cleaned['medical_tests'].append({
                            'name': test_name,
                            'details': str(test.get('details', '')).strip() if test.get('details') else None
                        })
                elif isinstance(test, str) and test.strip():
                    cleaned['medical_tests'].append({'name': test.strip(), 'details': None})
        else:
            cleaned['medical_tests'] = []
    else:
        cleaned['medical_tests'] = []
    
    logger.info(f"Final cleaned data: {cleaned}")
    return cleaned

@router.post("/analyze-prescription")
async def analyze_prescription(request: Request, file: UploadFile = File(...)):
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
        
        analysis = ai_client.analyze_prescription(contents)
        raw_extracted_data = ai_client.extract_patient_info(analysis, {})
        cleaned_data = clean_extracted_data(raw_extracted_data)
        
        logger.info(f"Cleaned data: {cleaned_data}")
        
        return {
            "analysis": analysis,
            "extracted_data": cleaned_data
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Prescription analysis error: {e}")
        raise HTTPException(status_code=500, detail="Failed to analyze prescription")