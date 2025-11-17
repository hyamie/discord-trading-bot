#!/usr/bin/env python3
"""
Schwab OAuth Helper Script
One-time script to obtain refresh token for server deployment
"""

import os
import sys
import json
import webbrowser
from http.server import HTTPServer, BaseHTTPRequestHandler
from urllib.parse import urlparse, parse_qs
from datetime import datetime, timedelta
from pathlib import Path
from dotenv import load_dotenv
import base64
import requests

# Load environment from project root
load_dotenv()

# Configuration
APP_KEY = os.getenv('SCHWAB_API_KEY')
APP_SECRET = os.getenv('SCHWAB_API_SECRET')
REDIRECT_URI = os.getenv('SCHWAB_REDIRECT_URI', 'https://127.0.0.1:8080/callback')
AUTH_URL = 'https://api.schwabapi.com/v1/oauth/authorize'
TOKEN_URL = 'https://api.schwabapi.com/v1/oauth/token'
TOKEN_METADATA_FILE = Path("data/schwab_token_metadata.json")

# Global to store the authorization code
auth_code = None


def save_token_metadata(refresh_token: str, created_at: datetime = None):
    """Save token metadata for monitoring"""
    if created_at is None:
        created_at = datetime.now()

    TOKEN_METADATA_FILE.parent.mkdir(parents=True, exist_ok=True)

    metadata = {
        'refresh_token': refresh_token,
        'created_at': created_at.isoformat(),
        'expires_at': (created_at + timedelta(days=7)).isoformat(),
        'last_updated': datetime.now().isoformat()
    }

    with open(TOKEN_METADATA_FILE, 'w') as f:
        json.dump(metadata, f, indent=2)

    print(f"💾 Token metadata saved to: {TOKEN_METADATA_FILE}")
    print(f"   Expires at: {metadata['expires_at']}")


class CallbackHandler(BaseHTTPRequestHandler):
    """HTTP handler to capture OAuth callback"""

    def do_GET(self):
        """Handle OAuth callback"""
        global auth_code

        # Parse the query parameters
        query = urlparse(self.path).query
        params = parse_qs(query)

        if 'code' in params:
            auth_code = params['code'][0]
            self.send_response(200)
            self.send_header('Content-type', 'text/html')
            self.end_headers()
            self.wfile.write(b"""
                <html>
                <head><title>Authorization Successful</title></head>
                <body>
                <h1>✅ Authorization Successful!</h1>
                <p>You can close this window and return to the terminal.</p>
                </body>
                </html>
            """)
        else:
            self.send_response(400)
            self.send_header('Content-type', 'text/html')
            self.end_headers()
            self.wfile.write(b"""
                <html>
                <head><title>Authorization Failed</title></head>
                <body>
                <h1>❌ Authorization Failed</h1>
                <p>No authorization code received.</p>
                </body>
                </html>
            """)

    def log_message(self, format, *args):
        """Suppress default logging"""
        pass


def get_authorization_code():
    """Step 1: Get authorization code via browser flow"""
    print("=" * 70)
    print("SCHWAB API OAUTH HELPER")
    print("=" * 70)
    print()

    if not APP_KEY or not APP_SECRET:
        print("❌ ERROR: Missing Schwab API credentials!")
        print()
        print("Please set these environment variables:")
        print("  SCHWAB_API_KEY=your_app_key")
        print("  SCHWAB_API_SECRET=your_app_secret")
        print()
        print("Get these from: https://developer.schwab.com/dashboard/apps")
        return None

    # Build authorization URL
    auth_params = {
        'client_id': APP_KEY,
        'redirect_uri': REDIRECT_URI,
        'response_type': 'code',
    }
    auth_request_url = f"{AUTH_URL}?{'&'.join(f'{k}={v}' for k, v in auth_params.items())}"

    print("Step 1: Opening browser for Schwab login...")
    print()
    print("If browser doesn't open automatically, visit this URL:")
    print(auth_request_url)
    print()
    print("After logging in and approving, you'll be redirected back here.")
    print()

    # Open browser
    webbrowser.open(auth_request_url)

    # Start local server to receive callback
    print("Starting local server on https://127.0.0.1:8080 ...")
    print("Waiting for OAuth callback...")
    print()

    server = HTTPServer(('127.0.0.1', 8080), CallbackHandler)

    # Handle one request (the callback)
    server.handle_request()
    server.server_close()

    if auth_code:
        print("✅ Authorization code received!")
        return auth_code
    else:
        print("❌ Failed to receive authorization code")
        return None


def exchange_code_for_tokens(code):
    """Step 2: Exchange authorization code for tokens"""
    print()
    print("Step 2: Exchanging code for tokens...")

    # Create Basic Auth header
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

        print("✅ Tokens obtained successfully!")
        print()

        # Save metadata for monitoring
        refresh_token = token_data.get('refresh_token', '')
        if refresh_token:
            save_token_metadata(refresh_token)

        print()
        print("=" * 70)
        print("🎉 SUCCESS! Save these values to Railway:")
        print("=" * 70)
        print()
        print("SCHWAB_REFRESH_TOKEN=" + refresh_token)
        print()
        print("=" * 70)
        print()
        print("📋 Next Steps:")
        print("  1. Copy the SCHWAB_REFRESH_TOKEN value above")
        print("  2. Go to Railway → Your Project → Variables")
        print("  3. Add or update variable: SCHWAB_REFRESH_TOKEN")
        print("  4. Paste the token value")
        print("  5. Railway will automatically redeploy")
        print()
        print("⏰ Important: Refresh token expires in 7 days")
        print("   Run 'python scripts/schwab_token_monitor.py' daily to check status")
        print("   Automated reminders available via Windows Task Scheduler")
        print()

        return token_data

    except requests.exceptions.RequestException as e:
        print(f"❌ Error exchanging code for tokens: {e}")
        if hasattr(e, 'response') and e.response is not None:
            print(f"Response: {e.response.text}")
        return None


def main():
    """Main flow"""
    # Step 1: Get authorization code
    code = get_authorization_code()

    if not code:
        print("❌ Authentication failed - no authorization code")
        return

    # Step 2: Exchange for tokens
    tokens = exchange_code_for_tokens(code)

    if not tokens:
        print("❌ Authentication failed - couldn't get tokens")
        return

    print("✅ Authentication complete!")
    print()
    print("Your bot can now access real-time Schwab market data! 🚀")


if __name__ == '__main__':
    main()
