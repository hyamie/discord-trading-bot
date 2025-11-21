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

# Test import before starting
echo "Testing main.py import..."
python -c "from src.api.main import app; print('SUCCESS: main.py imported')" 2>&1 || {
    echo "FAILED: main.py import error"
    echo "Falling back to minimal app"
    exec uvicorn src.api.main_minimal:app --host 0.0.0.0 --port ${PORT:-8000}
}

# Network connectivity diagnostic
echo "========================================="
echo "Network Connectivity Test to Supabase"
echo "========================================="
echo "Testing direct connection (port 5432)..."
curl -v --connect-timeout 10 telnet://db.isjvcytbwanionrtvplq.supabase.co:5432 2>&1
echo "Curl exit code: $?"
echo ""
echo "Testing pooler connection (port 6543)..."
curl -v --connect-timeout 10 telnet://aws-0-us-east-1.pooler.supabase.com:6543 2>&1
echo "Curl exit code: $?"
echo "========================================="

# Start the application (full version)
echo "Starting full application..."
exec uvicorn src.api.main:app --host 0.0.0.0 --port ${PORT:-8000} --log-level debug
