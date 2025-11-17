"""
Schwab Token Expiry Monitor and Auto-Refresh System
Monitors Schwab refresh token expiry and automates the renewal process
"""

import os
import sys
import time
import json
import base64
import requests
from datetime import datetime, timedelta
from pathlib import Path
from dotenv import load_dotenv
from loguru import logger

# Load environment variables
load_dotenv()

# Configuration
TOKEN_METADATA_FILE = Path("data/schwab_token_metadata.json")
SCHWAB_API_KEY = os.getenv('SCHWAB_API_KEY')
SCHWAB_API_SECRET = os.getenv('SCHWAB_API_SECRET')
SCHWAB_REDIRECT_URI = os.getenv('SCHWAB_REDIRECT_URI', 'https://127.0.0.1:8080/callback')
SCHWAB_REFRESH_TOKEN = os.getenv('SCHWAB_REFRESH_TOKEN')

# Token lifespans
REFRESH_TOKEN_LIFESPAN_DAYS = 7
ACCESS_TOKEN_LIFESPAN_MINUTES = 30
WARNING_THRESHOLD_DAYS = 1  # Warn when 1 day remaining

logger.add(
    "logs/schwab_token_monitor_{time}.log",
    rotation="1 day",
    retention="30 days",
    level="INFO"
)


def load_token_metadata():
    """Load token metadata from file"""
    if TOKEN_METADATA_FILE.exists():
        try:
            with open(TOKEN_METADATA_FILE, 'r') as f:
                return json.load(f)
        except Exception as e:
            logger.warning(f"Failed to load token metadata: {e}")
    return None


def save_token_metadata(refresh_token: str, created_at: datetime = None):
    """Save token metadata to file"""
    if created_at is None:
        created_at = datetime.now()

    TOKEN_METADATA_FILE.parent.mkdir(parents=True, exist_ok=True)

    metadata = {
        'refresh_token': refresh_token,
        'created_at': created_at.isoformat(),
        'expires_at': (created_at + timedelta(days=REFRESH_TOKEN_LIFESPAN_DAYS)).isoformat(),
        'last_checked': datetime.now().isoformat()
    }

    with open(TOKEN_METADATA_FILE, 'w') as f:
        json.dump(metadata, f, indent=2)

    logger.info(f"Token metadata saved. Expires at: {metadata['expires_at']}")


def check_token_expiry():
    """Check if refresh token is about to expire"""
    metadata = load_token_metadata()

    if not metadata:
        logger.warning("No token metadata found. Run schwab_oauth_helper.py first.")
        return {
            'status': 'unknown',
            'days_remaining': None,
            'needs_refresh': True,
            'message': 'No token metadata found'
        }

    created_at = datetime.fromisoformat(metadata['created_at'])
    expires_at = datetime.fromisoformat(metadata['expires_at'])
    now = datetime.now()

    days_remaining = (expires_at - now).total_seconds() / 86400
    hours_remaining = (expires_at - now).total_seconds() / 3600

    if days_remaining <= 0:
        status = 'expired'
        needs_refresh = True
        message = f"Token EXPIRED {abs(days_remaining):.1f} days ago!"
    elif days_remaining <= WARNING_THRESHOLD_DAYS:
        status = 'warning'
        needs_refresh = True
        message = f"Token expires in {hours_remaining:.1f} hours - ACTION REQUIRED"
    else:
        status = 'healthy'
        needs_refresh = False
        message = f"Token healthy - {days_remaining:.1f} days remaining"

    result = {
        'status': status,
        'created_at': created_at.isoformat(),
        'expires_at': expires_at.isoformat(),
        'days_remaining': days_remaining,
        'hours_remaining': hours_remaining,
        'needs_refresh': needs_refresh,
        'message': message
    }

    # Update last checked
    metadata['last_checked'] = now.isoformat()
    with open(TOKEN_METADATA_FILE, 'w') as f:
        json.dump(metadata, f, indent=2)

    return result


def test_token_validity():
    """Test if the current refresh token is still valid by attempting to get an access token"""
    if not SCHWAB_REFRESH_TOKEN:
        logger.error("No SCHWAB_REFRESH_TOKEN in environment")
        return False

    try:
        # Encode credentials
        credentials = f"{SCHWAB_API_KEY}:{SCHWAB_API_SECRET}"
        encoded_credentials = base64.b64encode(credentials.encode()).decode()

        # Request access token
        url = "https://api.schwab.com/oauth/token"
        headers = {
            'Authorization': f'Basic {encoded_credentials}',
            'Content-Type': 'application/x-www-form-urlencoded'
        }
        data = {
            'grant_type': 'refresh_token',
            'refresh_token': SCHWAB_REFRESH_TOKEN
        }

        response = requests.post(url, headers=headers, data=data, timeout=10)

        if response.status_code == 200:
            logger.info("✅ Refresh token is valid - successfully obtained access token")
            return True
        else:
            logger.error(f"❌ Refresh token invalid - Status: {response.status_code}")
            logger.error(f"Response: {response.text}")
            return False

    except Exception as e:
        logger.error(f"Failed to test token validity: {e}")
        return False


def send_notification(status_info: dict):
    """Send notification about token status (placeholder for future integration)"""
    if status_info['needs_refresh']:
        logger.warning(f"🚨 NOTIFICATION: {status_info['message']}")
        # Future: Send email, Slack, Discord notification
    else:
        logger.info(f"✅ {status_info['message']}")


def update_railway_token(new_refresh_token: str):
    """Update Railway environment variable with new refresh token"""
    logger.info("To update Railway token:")
    logger.info("1. Go to https://railway.app/dashboard")
    logger.info("2. Select your project")
    logger.info("3. Go to Settings → Variables")
    logger.info(f"4. Update SCHWAB_REFRESH_TOKEN with: {new_refresh_token[:20]}...")
    logger.info("5. Railway will auto-redeploy")


def main():
    """Main monitoring function"""
    logger.info("=" * 60)
    logger.info("Schwab Token Monitor - Starting Check")
    logger.info("=" * 60)

    # Check token expiry
    status_info = check_token_expiry()

    logger.info(f"Status: {status_info['status'].upper()}")
    logger.info(f"Message: {status_info['message']}")

    if status_info['days_remaining'] is not None:
        logger.info(f"Days remaining: {status_info['days_remaining']:.2f}")
        logger.info(f"Hours remaining: {status_info['hours_remaining']:.2f}")

    # Test token validity
    if SCHWAB_REFRESH_TOKEN:
        logger.info("\nTesting token validity...")
        is_valid = test_token_validity()

        if not is_valid and status_info['status'] != 'expired':
            logger.warning("Token shows unexpired but is invalid - may have been revoked")
            status_info['needs_refresh'] = True
            status_info['message'] = "Token invalid - manual refresh required"

    # Send notification if needed
    send_notification(status_info)

    # Provide action items
    if status_info['needs_refresh']:
        logger.warning("\n" + "=" * 60)
        logger.warning("ACTION REQUIRED: Refresh Token")
        logger.warning("=" * 60)
        logger.warning("Run the following command to get a new refresh token:")
        logger.warning("  python scripts/schwab_oauth_helper.py")
        logger.warning("\nThen update Railway environment variable:")
        logger.warning("  SCHWAB_REFRESH_TOKEN=<new_token>")
        logger.warning("=" * 60)
        return 1  # Exit code 1 indicates action needed

    logger.info("\n✅ Token is healthy - no action needed")
    return 0  # Exit code 0 indicates healthy


if __name__ == "__main__":
    sys.exit(main())
