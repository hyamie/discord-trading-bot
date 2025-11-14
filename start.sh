#!/bin/bash
# Railway startup script with debugging

echo "========================================="
echo "Railway Environment Debug Info"
echo "========================================="
echo "PORT: ${PORT}"
echo "Working directory: $(pwd)"
echo "Python version: $(python --version)"
echo "Files in src/api/:"
ls -la src/api/
echo "========================================="

# Start the application (full version now that Railway is configured)
exec uvicorn src.api.main:app --host 0.0.0.0 --port ${PORT:-8000}
