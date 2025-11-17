# Next Steps: Schwab API Setup

## ✅ Completed
- [x] Schwab API client implementation with OAuth 2.0
- [x] Auto-authentication with refresh token
- [x] OAuth helper script created (`scripts/schwab_oauth_helper.py`)
- [x] Comprehensive setup guide (`SCHWAB_SETUP_GUIDE.md`)
- [x] Code deployed to Railway

## 🔄 Required Actions (To Get Live Market Data)

### Step 1: Create Schwab Developer Account (5 minutes)

1. Go to https://developer.schwab.com
2. Click "Register" (top right)
3. Create account (NOT your brokerage login - this is separate)
4. Verify email

**Important**: Developer account is different from Schwab brokerage account.

---

### Step 2: Create Schwab App (3 minutes)

1. Log into https://developer.schwab.com
2. Go to "Dashboard" → "Apps"
3. Click "Create App"
4. Fill in:
   - **App Name**: `trading-bot`
   - **Callback URL**: `https://127.0.0.1:8080/callback`
   - **Description**: Personal trading analysis bot

5. **Save these credentials securely**:
   ```
   App Key (Client ID): xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx
   Secret: yyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyy
   ```

---

### Step 3: Add Credentials to Environment (2 minutes)

#### Option A: Local .env file (for running OAuth script)

Create `C:\ClaudeAgents\projects\discord-trading-bot\.env`:

```bash
# Schwab API Credentials (from Step 2)
SCHWAB_API_KEY=your_app_key_here
SCHWAB_API_SECRET=your_secret_here
SCHWAB_REDIRECT_URI=https://127.0.0.1:8080/callback
```

#### Option B: Railway (for production deployment)

Add to Railway project → Settings → Variables:
```bash
SCHWAB_API_KEY=your_app_key_here
SCHWAB_API_SECRET=your_secret_here
SCHWAB_REDIRECT_URI=https://127.0.0.1:8080/callback
```

---

### Step 4: Run OAuth Helper to Get Refresh Token (2 minutes)

```bash
cd C:\ClaudeAgents\projects\discord-trading-bot
python scripts/schwab_oauth_helper.py
```

This will:
1. Open browser to Schwab login
2. You log in with **brokerage credentials** (not developer account)
3. Approve the app
4. Display your `SCHWAB_REFRESH_TOKEN`

**Save this token** - you'll need it for Railway.

---

### Step 5: Add Refresh Token to Railway (1 minute)

Go to Railway → Your Project → Settings → Variables

Add:
```bash
SCHWAB_REFRESH_TOKEN=eyJhbGciOiJSUzI1NiIsInR5cCI6IkpXVCJ9...
```

Railway will automatically redeploy.

---

### Step 6: Test Live Market Data (1 minute)

```bash
# Check health
curl https://discord-trading-bot-production.up.railway.app/health

# Should show: "schwab_api": true

# Test analysis
curl -X POST https://discord-trading-bot-production.up.railway.app/analyze \
  -H "Content-Type: application/json" \
  -d '{"ticker": "AAPL", "trade_type": "day"}'

# Should return trade plans with REAL-TIME data!
```

---

## 🔑 Important Notes

### Token Expiry
- **Access Token**: 30 minutes (auto-refreshed)
- **Refresh Token**: **7 DAYS** (requires manual re-auth)

### Weekly Maintenance
Every Monday (or every 7 days):
1. Run `python scripts/schwab_oauth_helper.py`
2. Get new refresh token
3. Update Railway environment variable

Takes 2 minutes total.

---

## 🆘 Troubleshooting

### "No module named 'dotenv'"
```bash
pip install python-dotenv requests
```

### "Unauthorized" Error
- Check `SCHWAB_API_KEY` and `SCHWAB_API_SECRET` are correct
- Verify callback URL matches exactly: `https://127.0.0.1:8080/callback`

### "Invalid Grant" Error
- Refresh token expired (>7 days old)
- Run `schwab_oauth_helper.py` again

### Still Getting Empty Data
- Check Railway logs: `railway logs`
- Verify market is open (M-F 9:30 AM - 4:00 PM ET)
- Use debug endpoint: `/debug/yfinance/AAPL` (will show yfinance vs schwab comparison)

---

## 📋 Quick Reference

**Files Created:**
- `SCHWAB_SETUP_GUIDE.md` - Complete setup documentation
- `scripts/schwab_oauth_helper.py` - OAuth token generator
- `NEXT_STEPS_SCHWAB.md` - This file (action items)

**Modified Files:**
- `src/utils/schwab_api.py` - OAuth 2.0 implementation
- `src/api/main.py` - Refresh token integration

**Environment Variables Needed:**
```bash
SCHWAB_API_KEY=xxx
SCHWAB_API_SECRET=xxx
SCHWAB_REDIRECT_URI=https://127.0.0.1:8080/callback
SCHWAB_REFRESH_TOKEN=xxx  # Get from OAuth helper
```

---

## 🚀 Ready to Go Live?

Follow Steps 1-6 above in order. Total time: ~15 minutes.

Once complete, your bot will have **real-time market data** with no delays!
