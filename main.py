from fastapi import FastAPI, UploadFile, File, WebSocket, WebSocketDisconnect
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from gemini_client import GeminiClient
import os

app = FastAPI(title="PMS AI - Prescription & Voice Assistant")

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize Gemini Client
# We initialize it lazily or here if API key is present. 
# To avoid crash on start if key is missing, we can wrap it.
try:
    gemini_client = GeminiClient()
except Exception as e:
    print(f"Warning: Gemini Client failed to initialize. Check API Key. {e}")
    gemini_client = None

@app.post("/analyze-prescription")
async def analyze_prescription(file: UploadFile = File(...)):
    if not gemini_client:
        return JSONResponse(status_code=500, content={"error": "Gemini Client not initialized"})
    
    try:
        contents = await file.read()
        analysis = gemini_client.analyze_prescription(contents)
        return {"analysis": analysis}
    except Exception as e:
        return JSONResponse(status_code=500, content={"error": str(e)})

@app.websocket("/ws/voice-assistant")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    if not gemini_client:
        await websocket.send_text("Error: Gemini Client not initialized. Please check server logs.")
        await websocket.close()
        return

    try:
        while True:
            data = await websocket.receive_text()
            # process the received text (transcription)
            response_text = gemini_client.chat_response(data)
            await websocket.send_text(response_text)
    except WebSocketDisconnect:
        print("Client disconnected")
    except Exception as e:
        print(f"WebSocket Error: {e}")
        try:
            await websocket.close()
        except:
            pass

# Serve a simple HTML frontend
@app.get("/")
async def get():
    with open("templates/index.html", "r", encoding="utf-8") as f:
        html_content = f.read()
    return HTMLResponse(content=html_content, status_code=200)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
