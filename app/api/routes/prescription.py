from fastapi import APIRouter, UploadFile, File, Request
from fastapi.responses import JSONResponse

router = APIRouter()

@router.post("/analyze-prescription")
async def analyze_prescription(request: Request, file: UploadFile = File(...)):
    ai_client = getattr(request.app.state, "ai_client", None)
    if not ai_client:
        return JSONResponse(status_code=500, content={"error": "AI Client not initialized"})
    try:
        contents = await file.read()
        analysis = ai_client.analyze_prescription(contents)
        extracted_data = ai_client.extract_patient_info(analysis, {})
        return {"analysis": analysis, "extracted_data": extracted_data}
    except Exception as e:
        return JSONResponse(status_code=500, content={"error": str(e)})