#!/usr/bin/env python3
"""
Schwab OAuth with Local Server - Catches callback instantly
"""
import os
import sys
import json
import base64
import requests
import webbrowser
import threading
from http.server import HTTPServer, BaseHTTPRequestHandler
from urllib.parse import urlparse, parse_qs
from datetime import datetime, timedelta
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

APP_KEY = os.getenv('SCHWAB_API_KEY')
APP_SECRET = os.getenv('SCHWAB_API_SECRET')
REDIRECT_URI = 'http://127.0.0.1:8080/callback'  # HTTP not HTTPS
AUTH_URL = 'https://api.schwabapi.com/v1/oauth/authorize'
TOKEN_URL = 'https://api.schwabapi.com/v1/oauth/token'
TOKEN_METADATA_FILE = Path("data/schwab_token_metadata.json")

auth_code = None
server_done = False

class CallbackHandler(BaseHTTPRequestHandler):
    """HTTP handler to capture OAuth callback"""

    def do_GET(self):
        """Handle OAuth callback"""
        global auth_code, server_done

        query = urlparse(self.path).query
        params = parse_qs(query)

        if 'code' in params:
            auth_code = params['code'][0]
            self.send_response(200)
            self.send_header('Content-type', 'text/html')
            self.end_headers()
            html = """
                <html>
                <head><title>Success</title></head>
                <body>
                <h1>Authorization Successful!</h1>
                <p>Exchanging code for tokens...</p>
                <p>You can close this window.</p>
                </body>
                </html>
            """
            self.wfile.write(html.encode('utf-8'))
            server_done = True
        else:
            self.send_response(400)
            self.send_header('Content-type', 'text/html')
            self.end_headers()
            html = """
                <html>
                <head><title>Failed</title></head>
                <body>
                <h1>Authorization Failed</h1>
                <p>No code received.</p>
                </body>
                </html>
            """
            self.wfile.write(html.encode('utf-8'))

    def log_message(self, format, *args):
        """Suppress default logging"""
        pass

def exchange_code_for_tokens(code):
    """Exchange authorization code for tokens"""
    credentials = f"{APP_KEY}:{APP_SECRET}"
    encoded_credentials = base64.b64encode(credentials.encode()).decode()

    headers = {
        'Authorization': f'Basic {encoded_credentials}',
        'Content-Type': 'application/x-www-form-urlencoded'
    }

    data = {
        'grant_type': 'authorization_code',
        'code': code,
        'redirect_uri': REDIRECT_URI
    }

    try:
        response = requests.post(TOKEN_URL, headers=headers, data=data)
        response.raise_for_status()

        token_data = response.json()
        refresh_token = token_data.get('refresh_token', '')

        # Save metadata
        TOKEN_METADATA_FILE.parent.mkdir(parents=True, exist_ok=True)

        metadata = {
            'refresh_token': refresh_token,
            'created_at': datetime.now().isoformat(),
            'expires_at': (datetime.now() + timedelta(days=7)).isoformat(),
            'last_updated': datetime.now().isoformat()
        }

        with open(TOKEN_METADATA_FILE, 'w') as f:
            json.dump(metadata, f, indent=2)

        print()
        print("=" * 70)
        print("[SUCCESS] Tokens obtained!")
        print("=" * 70)
        print()
        print("SCHWAB_REFRESH_TOKEN=" + refresh_token)
        print()
        print("=" * 70)
        print()
        print("[INFO] Next Steps:")
        print("  1. Copy the SCHWAB_REFRESH_TOKEN value above")
        print("  2. Go to Railway -> Settings -> Variables")
        print("  3. Update: SCHWAB_REFRESH_TOKEN")
        print("  4. Railway will auto-redeploy")
        print()
        print("Metadata saved to:", TOKEN_METADATA_FILE)
        print("Expires:", metadata['expires_at'])

        return True

    except requests.exceptions.RequestException as e:
        print(f"[ERROR] Token exchange failed: {e}")
        if hasattr(e, 'response') and e.response is not None:
            print(f"Response: {e.response.text}")
        return False

def main():
    """Main OAuth flow"""
    print("=" * 70)
    print("SCHWAB OAUTH - LOCAL SERVER VERSION")
    print("=" * 70)
    print()

    if not APP_KEY or not APP_SECRET:
        print("[ERROR] Missing Schwab API credentials in .env file")
        return

    # Build authorization URL
    auth_url = f"{AUTH_URL}?client_id={APP_KEY}&redirect_uri={REDIRECT_URI}&response_type=code"

    print("Step 1: Starting local server on http://127.0.0.1:8080")
    print()

    # Start server in background thread
    server = HTTPServer(('127.0.0.1', 8080), CallbackHandler)

    def run_server():
        while not server_done:
            server.handle_request()

    server_thread = threading.Thread(target=run_server, daemon=True)
    server_thread.start()

    print("Step 2: Opening browser for Schwab login...")
    print()
    print("If browser doesn't open, visit:")
    print(auth_url)
    print()
    print("Waiting for callback...")
    print()

    # Open browser
    webbrowser.open(auth_url)

    # Wait for callback
    server_thread.join(timeout=120)  # 2 minute timeout

    if auth_code:
        print("[OK] Authorization code received!")
        print()
        print("Step 3: Exchanging code for tokens (immediately)...")

        if exchange_code_for_tokens(auth_code):
            print()
            print("[OK] Authentication complete!")
        else:
            print()
            print("[ERROR] Token exchange failed")
    else:
        print("[ERROR] No authorization code received (timeout or failed)")

    server.server_close()

if __name__ == '__main__':
    main()
