from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.services.openai_client import OpenAIClient
from app.api.routes import root, prescription, voice, report

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
# expose client to routers
app.state.ai_client = ai_client


app.include_router(root.router)
app.include_router(prescription.router)
app.include_router(voice.router)
app.include_router(report.router)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
