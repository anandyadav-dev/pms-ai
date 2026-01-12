from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import os
from app.services.openai_client import OpenAIClient
from app.api.routes import root, prescription, prescription_stream, voice, report

app = FastAPI(title="PMS AI - Prescription & Voice Assistant")

# CORS middleware - more secure configuration
allowed_origins = os.getenv("ALLOWED_ORIGINS", "http://localhost:3000,http://localhost:8080,http://localhost:8000").split(",")
app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS", "HEAD"],
    allow_headers=["*"],
)

# Initialize OpenAI Client safely with better error handling
import logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def validate_env_vars():
    required_vars = ["OPENAI_API_KEY"]
    missing_vars = []
    
    for var in required_vars:
        if not os.getenv(var):
            missing_vars.append(var)
    
    if missing_vars:
        logger.error(f"Missing required environment variables: {missing_vars}")
        raise ValueError(f"Missing required environment variables: {missing_vars}")

try:
    validate_env_vars()
    ai_client = OpenAIClient()
    logger.info("AI Client initialized successfully")
except Exception as e:
    logger.error(f"AI Client failed to initialize: {e}")
    ai_client = None
# expose client to routers
app.state.ai_client = ai_client


app.include_router(root.router)
app.include_router(prescription.router)
app.include_router(prescription_stream.router)
app.include_router(voice.router)
app.include_router(report.router)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
