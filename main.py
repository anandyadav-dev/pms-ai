from fastapi import FastAPI, UploadFile, File, WebSocket, WebSocketDisconnect
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from openai_client import OpenAIClient
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
        return {"analysis": analysis}
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
        while True:
            data = await websocket.receive_text()
            response_text = ai_client.chat_response(data)
            await websocket.send_text(response_text)

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


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
