from fastapi import APIRouter, WebSocket, WebSocketDisconnect
import asyncio
import json
import logging
from app.services.fast_extract import quick_extract

router = APIRouter()
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@router.websocket("/ws/voice-assistant")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    ai_client = getattr(websocket.app.state, "ai_client", None)
    if not ai_client:
        await websocket.send_text("Error: AI Client not initialized. Please check server logs.")
        await websocket.close()
        return
    try:
        patient_record = {}
        while True:
            data = await websocket.receive_text()
            try:
                fast = quick_extract(data, patient_record)
                patient_record = {**patient_record, **fast}
                await websocket.send_text("PRIORITY_UPDATE:" + json.dumps(fast))
            except Exception as e:
                logger.error(f"Fast extract error: {e}")
                await websocket.send_text("ERROR:Failed to extract quick data")
            
            async def ai_task(t):
                try:
                    logger.info(f"Processing user input: {t}")
                    # Stream the response
                    response_text = ""
                    async for chunk in ai_client.chat_response_stream(t):
                        response_text += chunk
                        await websocket.send_text("STREAM:" + chunk)
                    
                    # Send complete response as single message
                    await websocket.send_text("AI_RESPONSE:" + response_text)
                    
                    # Only extract structured data from user input, not AI response
                    # Use user's exact words for report
                    logger.info(f"Extracting patient info from: {t}")
                    res = ai_client.extract_patient_info(t, patient_record)
                    logger.info(f"Extracted data: {res}")
                    patient_record.update(res or {})
                    logger.info(f"Updated patient record: {patient_record}")
                    await websocket.send_text("DATA_UPDATE:" + json.dumps(patient_record))
                    await websocket.send_text("STREAM_COMPLETE:")
                except Exception as e:
                    logger.error(f"AI task error: {e}")
                    await websocket.send_text("ERROR:AI processing failed")
            
            asyncio.create_task(ai_task(data))
    except WebSocketDisconnect:
        logger.info("WebSocket disconnected")
    except Exception as e:
        logger.error(f"WebSocket error: {e}")
        await websocket.close()
