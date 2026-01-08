from fastapi import APIRouter, WebSocket, WebSocketDisconnect
import asyncio
import json
from app.services.fast_extract import quick_extract

router = APIRouter()

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
            except Exception:
                pass
            async def ai_task(t):
                try:
                    res = ai_client.extract_patient_info(t, patient_record)
                    patient_record.update(res or {})
                    await websocket.send_text("DATA_UPDATE:" + json.dumps(patient_record))
                except Exception:
                    pass
            asyncio.create_task(ai_task(data))
    except WebSocketDisconnect:
        pass
