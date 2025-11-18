#!/usr/bin/env python3
"""
Schwab OAuth with HTTPS Server - Uses self-signed certificate
"""
import os
import sys
import json
import base64
import requests
import webbrowser
import threading
import ssl
from http.server import HTTPServer, BaseHTTPRequestHandler
from urllib.parse import urlparse, parse_qs
from datetime import datetime, timedelta
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

APP_KEY = os.getenv('SCHWAB_API_KEY')
APP_SECRET = os.getenv('SCHWAB_API_SECRET')
REDIRECT_URI = 'https://127.0.0.1:8080/callback'
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

            # Exchange code immediately
            success = exchange_code_for_tokens(auth_code)

            self.send_response(200)
            self.send_header('Content-type', 'text/html')
            self.end_headers()

            if success:
                html = """
                    <html>
                    <head><title>Success</title></head>
                    <body>
                    <h1>Authorization Successful!</h1>
                    <p>Tokens obtained and saved.</p>
                    <p>Check your terminal for the SCHWAB_REFRESH_TOKEN.</p>
                    <p>You can close this window.</p>
                    </body>
                    </html>
                """
            else:
                html = """
                    <html>
                    <head><title>Error</title></head>
                    <body>
                    <h1>Token Exchange Failed</h1>
                    <p>Check terminal for error details.</p>
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
    print()
    print("[INFO] Exchanging code for tokens (immediately)...")

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

def create_ssl_cert():
    """Create self-signed certificate if not exists"""
    cert_file = Path("data/cert.pem")
    key_file = Path("data/key.pem")

    if cert_file.exists() and key_file.exists():
        return str(cert_file), str(key_file)

    cert_file.parent.mkdir(parents=True, exist_ok=True)

    # Create self-signed cert using openssl
    import subprocess

    try:
        subprocess.run([
            'openssl', 'req', '-x509', '-newkey', 'rsa:4096',
            '-keyout', str(key_file),
            '-out', str(cert_file),
            '-days', '365',
            '-nodes',
            '-subj', '/CN=127.0.0.1'
        ], check=True, capture_output=True)

        return str(cert_file), str(key_file)
    except (subprocess.CalledProcessError, FileNotFoundError):
        print("[ERROR] OpenSSL not found. Using Python's built-in SSL context.")
        return None, None

def main():
    """Main OAuth flow"""
    print("=" * 70)
    print("SCHWAB OAUTH - HTTPS SERVER VERSION")
    print("=" * 70)
    print()

    if not APP_KEY or not APP_SECRET:
        print("[ERROR] Missing Schwab API credentials in .env file")
        return

    # Build authorization URL
    auth_url = f"{AUTH_URL}?client_id={APP_KEY}&redirect_uri={REDIRECT_URI}&response_type=code"

    print("Step 1: Starting HTTPS server on https://127.0.0.1:8080")
    print()

    # Create server
    server = HTTPServer(('127.0.0.1', 8080), CallbackHandler)

    # Try to create SSL context
    cert_file, key_file = create_ssl_cert()

    if cert_file and key_file:
        ssl_context = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
        ssl_context.load_cert_chain(cert_file, key_file)
        server.socket = ssl_context.wrap_socket(server.socket, server_side=True)
    else:
        # Use default SSL context (Python 3.10+)
        ssl_context = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
        ssl_context.check_hostname = False
        ssl_context.verify_mode = ssl.CERT_NONE
        # Generate adhoc certificate
        import tempfile
        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.pem') as cert_temp:
            with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.pem') as key_temp:
                # This won't work without openssl, so just use unencrypted
                print("[WARNING] Could not create SSL certificate. Server may not work.")
                print("          Install OpenSSL or use schwab_oauth_simple.py instead.")

    print("Step 2: Opening browser for Schwab login...")
    print()
    print("If browser doesn't open, visit:")
    print(auth_url)
    print()
    print("NOTE: Your browser will show a security warning because")
    print("      we're using a self-signed certificate. This is normal.")
    print("      Click 'Advanced' -> 'Proceed to 127.0.0.1' to continue.")
    print()
    print("Waiting for callback...")
    print()

    # Open browser
    webbrowser.open(auth_url)

    # Handle requests until done
    while not server_done:
        server.handle_request()

    server.server_close()

    if auth_code:
        print()
        print("[OK] Authentication complete!")
    else:
        print()
        print("[ERROR] No authorization code received")

if __name__ == '__main__':
    main()
