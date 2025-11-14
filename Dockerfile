# Trading Bot API - Dockerfile
# Simplified single-stage build using pandas-ta
# Updated: 2025-11-14 - Fixed llm_client.py syntax error

FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements and install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY src/ ./src/
COPY .env.example .env
COPY start.sh .

# Create necessary directories and make start script executable
RUN mkdir -p logs data && chmod +x start.sh

# Expose port (Railway will provide $PORT env var)
EXPOSE 8000

# Health check - disabled for now to avoid startup issues
# HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
#     CMD python -c "import requests; requests.get('http://localhost:8000/health')"

# Run the application via startup script
CMD ["./start.sh"]
