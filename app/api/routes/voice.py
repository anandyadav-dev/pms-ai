from fastapi import APIRouter, WebSocket, WebSocketDisconnect
import json

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
                patient_record = ai_client.extract_patient_info(data, patient_record)
                await websocket.send_text("DATA_UPDATE:" + json.dumps(patient_record))
            except Exception:
                pass
    except WebSocketDisconnect:
        pass