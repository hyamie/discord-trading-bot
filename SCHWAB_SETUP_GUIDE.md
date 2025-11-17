# Schwab API Setup Guide

## Overview

Schwab provides **real-time market data** (not delayed) through their Trader API. This guide walks through the complete setup process.

---

## Key Facts About Schwab API

### ✅ Advantages
- **Real-time data**: No 15-minute delay like most free APIs
- **Comprehensive**: Quotes, chains, historical data, account info
- **Free**: No cost for individual developers
- **Reliable**: Professional-grade infrastructure

### ⚠️ Challenges
- **OAuth Required**: Must complete browser-based authentication
- **7-Day Token Expiry**: Refresh tokens expire after 7 days (requires re-auth)
- **Manual Initial Setup**: Can't fully automate first-time authentication

---

## Step 1: Create Schwab Developer Account

1. Go to https://developer.schwab.com
2. Click "Register" (top right)
3. Create a **separate** account (NOT your brokerage login)
4. Verify your email

**Note**: Your developer account is different from your Schwab brokerage account.

---

## Step 2: Create an App

1. Log into https://developer.schwab.com
2. Go to "Dashboard" → "Apps"
3. Click "Create App"
4. Fill in:
   - **App Name**: `trading-bot` (or your choice)
   - **Callback URL**: `https://127.0.0.1:8080/callback`
   - **Description**: Personal trading bot

5. Save your credentials:
   - **App Key** (Client ID)
   - **Secret**

**IMPORTANT**: Save these credentials securely - you'll need them for deployment.

---

## Step 3: One-Time Authentication (Local Machine)

You need to complete OAuth flow ONCE on your local machine to get initial tokens.

### Prerequisites
- Python 3.11+
- Your Schwab brokerage account credentials

### Run the Authentication Script

```bash
cd /c/ClaudeAgents/projects/discord-trading-bot
python scripts/schwab_oauth_helper.py
```

This script will:
1. Open your browser to Schwab login
2. You log in with your **brokerage credentials**
3. Approve the app
4. Capture the refresh token
5. Display it for you to save

**Output**: You'll get a `SCHWAB_REFRESH_TOKEN` value like:
```
SCHWAB_REFRESH_TOKEN=eyJhbGciOiJSUzI1NiIsInR5cCI6IkpXVCJ9...
```

---

## Step 4: Configure Railway Environment Variables

Add these to your Railway project (Settings → Variables):

```bash
# Schwab API Credentials (from Step 2)
SCHWAB_API_KEY=your_app_key_here
SCHWAB_API_SECRET=your_secret_here
SCHWAB_REDIRECT_URI=https://127.0.0.1:8080/callback

# Refresh Token (from Step 3)
SCHWAB_REFRESH_TOKEN=your_refresh_token_here
```

**Security Note**: Never commit these to git! They're only in Railway environment variables.

---

## Step 5: Deploy and Test

Once environment variables are set, Railway will redeploy automatically.

Test the API:
```bash
curl https://your-railway-app.railway.app/health
# Should show schwab_api: true

curl -X POST https://your-railway-app.railway.app/analyze \
  -H "Content-Type: application/json" \
  -d '{"ticker": "AAPL", "trade_type": "day"}'
# Should return trade plans with real-time data!
```

---

## How It Works

### Token Flow

```
Initial (One-time on local machine):
User → Browser → Schwab Login → Authorization Code → Refresh Token
                                                      (Save to Railway)

Production (Automated on Railway):
API Request → Check Access Token
            → Expired? Use Refresh Token → New Access Token
            → Make API Call → Return Data
```

### Token Lifespan
- **Access Token**: 30 minutes (automatically refreshed)
- **Refresh Token**: 7 days (requires manual re-auth after expiry)

### Maintenance Required
- **Every 7 days**: Re-run `schwab_oauth_helper.py` to get new refresh token
- **Update Railway**: Add new `SCHWAB_REFRESH_TOKEN` value

---

## Automation Options

### Option A: Manual Weekly Refresh (Recommended for Individual Use)
- Every Monday morning, run the helper script
- Takes 2 minutes
- Most reliable

### Option B: Automated Browser Automation (Advanced)
- Use Puppeteer/Selenium to automate login
- Requires storing Schwab credentials
- Security risk (credentials in environment)
- Complex to maintain

### Option C: Serverless Function (Advanced)
- Deploy helper script to AWS Lambda
- Trigger weekly via CloudWatch Events
- Store tokens in AWS Secrets Manager
- More infrastructure to manage

**Recommendation**: Start with Option A. It's simple and secure.

---

## Troubleshooting

### "Unauthorized" Error
- Check if `SCHWAB_API_KEY` and `SCHWAB_API_SECRET` are correct
- Verify callback URL matches exactly: `https://127.0.0.1:8080/callback`

### "Invalid Grant" Error
- Refresh token expired (>7 days old)
- Run `schwab_oauth_helper.py` again to get new token

### "Empty Data" or "No Plans"
- Check if access token is valid (look at logs)
- Verify market is open (M-F 9:30 AM - 4:00 PM ET)
- Test with `/debug/schwab/AAPL` endpoint

### "Rate Limit" Error
- Schwab allows 120 calls/minute
- Bot respects this limit automatically
- If hitting limit, reduce frequency of analysis requests

---

## Security Best Practices

### ✅ DO:
- Store tokens in Railway environment variables
- Use HTTPS for all API calls
- Rotate refresh token regularly
- Monitor API usage

### ❌ DON'T:
- Commit tokens to git
- Share refresh tokens
- Use same token across multiple apps
- Store credentials in code

---

## Cost

**$0/month**

Schwab API is completely free for individual developers.

---

## Support Resources

- **Schwab Developer Portal**: https://developer.schwab.com
- **Documentation**: https://developer.schwab.com/products/trader-api--individual
- **schwab-py Library**: https://schwab-py.readthedocs.io
- **Community**: Reddit r/algotrading, QuantConnect forums

---

## Next Steps

1. ✅ Complete Steps 1-2 (Create account & app)
2. ✅ Run `schwab_oauth_helper.py` (Get refresh token)
3. ✅ Add environment variables to Railway
4. ✅ Test with real market data
5. ✅ Set weekly reminder to refresh token

**Ready to proceed?** Run the helper script next!
