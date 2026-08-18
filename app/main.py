from fastapi import FastAPI
from app.core.config import settings

app = FastAPI(
    title=settings.PROJECT_NAME,
    description="DataPilot: Automated Data Analysis & Grounded AI Intelligence Engine",
    version="1.0.0"
)

@app.get("/")
def health_check():
    return {
        "status": "online",
        "app_name": settings.PROJECT_NAME,
        "max_upload_mb": settings.MAX_UPLOAD_SIZE_MB,
        "debug_mode": settings.DEBUG
    }