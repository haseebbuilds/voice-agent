from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv
from config.database import init_db, close_db
from routes.intake_routes import router
import uvicorn

load_dotenv()

app = FastAPI(
    title="Voice Intake Agent API",
    description="Legal intake system with voice-based call handling",
    version="1.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(router)

@app.on_event("startup")
async def startup_event():
    from config.settings import settings
    
    email_valid = settings.validate_email_config()
    
    try:
        await init_db()
    except Exception as e:
        pass

@app.on_event("shutdown")
async def shutdown_event():
    await close_db()

@app.get("/")
async def root():
    return {
        "message": "Voice Intake Agent API",
        "status": "running",
        "version": "1.0.0"
    }

@app.get("/health")
async def health_check():
    return {"status": "healthy"}

if __name__ == "__main__":
    import sys
    sys.stdout.reconfigure(line_buffering=True)
    sys.stderr.reconfigure(line_buffering=True)
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True, log_level="info")

