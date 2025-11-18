"""
Simple Schwab OAuth - Manual Code Entry
"""
import os
import base64
import requests
import webbrowser
from dotenv import load_dotenv
import json
from datetime import datetime, timedelta
from pathlib import Path

load_dotenv()

APP_KEY = os.getenv('SCHWAB_API_KEY')
APP_SECRET = os.getenv('SCHWAB_API_SECRET')
REDIRECT_URI = os.getenv('SCHWAB_REDIRECT_URI', 'https://127.0.0.1:8080/callback')

print("="*70)
print("SCHWAB OAUTH - SIMPLE VERSION")
print("="*70)
print()

if not APP_KEY or not APP_SECRET:
    print("[ERROR] Missing credentials in .env file")
    exit(1)

# Build authorization URL
auth_url = f"https://api.schwabapi.com/v1/oauth/authorize?client_id={APP_KEY}&redirect_uri={REDIRECT_URI}&response_type=code"

print("Step 1: Opening Schwab login page...")
print()
print("URL:", auth_url)
print()

# Open browser
webbrowser.open(auth_url)

print("After logging in and approving:")
print("1. You'll be redirected to https://127.0.0.1:8080/callback?code=...")
print("2. The page will show 'can't be reached' - THIS IS NORMAL")
print("3. Copy the ENTIRE URL from your browser's address bar")
print()

# Get the callback URL from user
callback_url = input("Paste the full callback URL here: ").strip()

# Extract the code parameter
if "code=" in callback_url:
    code_part = callback_url.split("code=")[1]
    # Remove everything after & or # if present
    if "&" in code_part:
        auth_code = code_part.split("&")[0]
    elif "#" in code_part:
        auth_code = code_part.split("#")[0]
    else:
        auth_code = code_part

    # URL decode %40 to @
    auth_code = auth_code.replace("%40", "@")

    print()
    print("Extracted code:", auth_code[:30] + "...")
    print()
    print("Step 2: Exchanging code for tokens...")

    # Exchange for tokens
    credentials = f"{APP_KEY}:{APP_SECRET}"
    encoded_credentials = base64.b64encode(credentials.encode()).decode()

    headers = {
        'Authorization': f'Basic {encoded_credentials}',
        'Content-Type': 'application/x-www-form-urlencoded'
    }

    data = {
        'grant_type': 'authorization_code',
        'code': auth_code,
        'redirect_uri': REDIRECT_URI
    }

    response = requests.post('https://api.schwabapi.com/v1/oauth/token', headers=headers, data=data)

    if response.status_code == 200:
        token_data = response.json()
        refresh_token = token_data.get('refresh_token', '')

        # Save metadata
        TOKEN_METADATA_FILE = Path('data/schwab_token_metadata.json')
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
        print("="*70)
        print("[SUCCESS] Tokens obtained!")
        print("="*70)
        print()
        print("SCHWAB_REFRESH_TOKEN=" + refresh_token)
        print()
        print("="*70)
        print()
        print("[INFO] Next Steps:")
        print("  1. Copy the SCHWAB_REFRESH_TOKEN value above")
        print("  2. Go to Railway -> Settings -> Variables")
        print("  3. Update: SCHWAB_REFRESH_TOKEN")
        print("  4. Railway will auto-redeploy")
        print()
        print("Metadata saved to:", TOKEN_METADATA_FILE)
        print("Expires:", metadata['expires_at'])
    else:
        print()
        print("[ERROR] Token exchange failed")
        print("Status:", response.status_code)
        print("Response:", response.text)
else:
    print("[ERROR] No 'code=' found in URL")
    print("Make sure you copied the entire callback URL")
