#!/usr/bin/env python3
"""
Schwab OAuth using schwab-py library - Handles OAuth automatically
"""
import os
import json
from pathlib import Path
from datetime import datetime, timedelta
from dotenv import load_dotenv
import schwab

load_dotenv()

APP_KEY = os.getenv('SCHWAB_API_KEY')
APP_SECRET = os.getenv('SCHWAB_API_SECRET')
REDIRECT_URI = os.getenv('SCHWAB_REDIRECT_URI', 'https://127.0.0.1:8080/callback')
TOKEN_FILE = Path("data/schwab_token.json")
TOKEN_METADATA_FILE = Path("data/schwab_token_metadata.json")

def main():
    """Main OAuth flow using schwab-py"""
    print("=" * 70)
    print("SCHWAB OAUTH - EASY VERSION (using schwab-py)")
    print("=" * 70)
    print()

    if not APP_KEY or not APP_SECRET:
        print("[ERROR] Missing Schwab API credentials in .env file")
        return

    # Create data directory
    TOKEN_FILE.parent.mkdir(parents=True, exist_ok=True)

    print("Step 1: Opening browser for Schwab login...")
    print()
    print("The schwab-py library will:")
    print("  1. Open your browser")
    print("  2. Handle the OAuth flow automatically")
    print("  3. Save tokens to", TOKEN_FILE)
    print()
    print("After logging in and approving:")
    print("  - The browser will redirect to a local server")
    print("  - Tokens will be automatically exchanged")
    print()
    input("Press ENTER to continue...")
    print()

    try:
        # Use schwab's easy client factory
        # This handles the entire OAuth flow automatically
        client = schwab.auth.easy_client(
            api_key=APP_KEY,
            app_secret=APP_SECRET,
            callback_url=REDIRECT_URI,
            token_path=str(TOKEN_FILE)
        )

        print()
        print("=" * 70)
        print("[SUCCESS] Authentication complete!")
        print("=" * 70)
        print()

        # Read the token file to get the refresh token
        with open(TOKEN_FILE, 'r') as f:
            token_data = json.load(f)

        refresh_token = token_data.get('refresh_token', '')

        # Save metadata
        metadata = {
            'refresh_token': refresh_token,
            'created_at': datetime.now().isoformat(),
            'expires_at': (datetime.now() + timedelta(days=7)).isoformat(),
            'last_updated': datetime.now().isoformat()
        }

        with open(TOKEN_METADATA_FILE, 'w') as f:
            json.dump(metadata, f, indent=2)

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
        print("Token saved to:", TOKEN_FILE)
        print("Metadata saved to:", TOKEN_METADATA_FILE)
        print("Expires:", metadata['expires_at'])
        print()

    except Exception as e:
        print()
        print("[ERROR] Authentication failed:", str(e))
        print()
        import traceback
        traceback.print_exc()

if __name__ == '__main__':
    main()
