"""
Minimal FastAPI app for testing Railway deployment
"""
import os
from datetime import datetime
from fastapi import FastAPI

app = FastAPI(title="Trading Bot API - Minimal")

@app.get("/")
async def root():
    return {
        "service": "Trading Bot API",
        "status": "running (minimal mode)",
        "timestamp": datetime.now().isoformat()
    }

@app.get("/health")
async def health():
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
