"""
Minimal FastAPI app for testing Railway deployment
"""
import os
from datetime import datetime
from fastapi import FastAPI, Request
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="Trading Bot API - Minimal")

@app.middleware("http")
async def log_requests(request: Request, call_next):
    logger.info(f"Incoming request: {request.method} {request.url}")
    response = await call_next(request)
    logger.info(f"Response status: {response.status_code}")
    return response

@app.get("/")
async def root():
    logger.info("Root endpoint called")
    return {
        "service": "Trading Bot API",
        "status": "running (minimal mode)",
        "timestamp": datetime.now().isoformat()
    }

@app.get("/health")
async def health():
    logger.info("Health endpoint called")
    return {
        "status": "healthy",
        "mode": "minimal",
        "timestamp": datetime.now().isoformat(),
        "port": os.getenv('PORT', '8000')
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main_minimal:app",
        host="0.0.0.0",
        port=int(os.getenv('PORT', 8000)),
        log_level="info"
    )
