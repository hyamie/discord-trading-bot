# Trading Bot Quick Start Guide

**Goal**: Get your trading bot running with live Schwab market data + automated token monitoring.

---

## ✅ What's Done

- ✅ FastAPI trading analysis engine (3-Tier MTF)
- ✅ Schwab API integration (OAuth 2.0)
- ✅ YFinance fallback (local only)
- ✅ Database (Supabase PostgreSQL)
- ✅ Deployed to Railway
- ✅ **Automated token monitoring system**

---

## 🚀 What You Need to Do (15 minutes)

### 1. Get Schwab API Credentials (5 min)

**If you already have them:** Skip to Step 2

**If you don't:**
```
1. Go to: https://developer.schwab.com
2. Register (separate from brokerage account)
3. Create App:
   - Name: trading-bot
   - Callback: https://127.0.0.1:8080/callback
4. Save App Key + Secret
```

---

### 2. Setup Local Environment (2 min)

Create `.env` in project root:
```bash
SCHWAB_API_KEY=your_app_key_here
SCHWAB_API_SECRET=your_app_secret_here
SCHWAB_REDIRECT_URI=https://127.0.0.1:8080/callback
```

---

### 3. Get Refresh Token (3 min)

```bash
cd C:\ClaudeAgents\projects\discord-trading-bot
python scripts/schwab_oauth_helper.py
```

**What happens:**
1. Browser opens → Schwab login
2. You log in with **brokerage** credentials
3. Approve app
4. Terminal displays `SCHWAB_REFRESH_TOKEN=...`
5. Copy that token

---

### 4. Update Railway (2 min)

```
1. Go to: https://railway.app/dashboard
2. Select your project
3. Settings → Variables
4. Add or update:
   - SCHWAB_API_KEY=<from step 1>
   - SCHWAB_API_SECRET=<from step 1>
   - SCHWAB_REDIRECT_URI=https://127.0.0.1:8080/callback
   - SCHWAB_REFRESH_TOKEN=<from step 3>
5. Railway auto-redeploys (wait 2-3 min)
```

---

### 5. Install Automated Monitoring (3 min)

```powershell
cd C:\ClaudeAgents\projects\discord-trading-bot\scripts
.\setup_schwab_monitor.ps1 -Install
```

**What this does:**
- Creates daily Task Scheduler job (9 AM)
- Monitors token expiry
- Warns you 24 hours before expiration
- No more surprise token failures!

---

## 🧪 Test It's Working

### Test Railway Health
```bash
curl https://discord-trading-bot-production.up.railway.app/health
```

**Expected:**
```json
{
  "status": "healthy",
  "schwab_api": true,
  "database": true
}
```

### Test Analysis
```bash
curl -X POST https://discord-trading-bot-production.up.railway.app/analyze \
  -H "Content-Type: application/json" \
  -d '{"ticker": "AAPL", "trade_type": "day"}'
```

**Expected:** JSON with trade plans, entry/stop/target levels

### Test Token Monitor
```powershell
.\setup_schwab_monitor.ps1 -Test
```

**Expected:**
```
Status: HEALTHY
Message: Token healthy - 6.8 days remaining
✅ Token is healthy - no action needed
```

---

## 📅 Weekly Maintenance (2 minutes)

**When monitor warns "Action Required":**

```bash
# 1. Get new token
python scripts/schwab_oauth_helper.py

# 2. Copy the SCHWAB_REFRESH_TOKEN

# 3. Update Railway
#    Railway → Settings → Variables → SCHWAB_REFRESH_TOKEN
```

**That's it!** Railway auto-redeploys, bot keeps running.

---

## 📚 Detailed Guides

| Document | Purpose |
|----------|---------|
| **SCHWAB_TOKEN_AUTOMATION.md** | Complete automation guide |
| **SCHWAB_SETUP_GUIDE.md** | Detailed Schwab API setup |
| **PROJECT_STATUS.md** | Full project status |
| **NEXT_STEPS_SCHWAB.md** | Action items checklist |

---

## 🔧 Commands Reference

### Daily Token Check
```bash
python scripts/schwab_token_monitor.py
```

### Get New Token
```bash
python scripts/schwab_oauth_helper.py
```

### Install Monitoring
```powershell
.\setup_schwab_monitor.ps1 -Install
```

### Test Monitoring
```powershell
.\setup_schwab_monitor.ps1 -Test
```

### Check Railway Health
```bash
curl https://discord-trading-bot-production.up.railway.app/health
```

### Analyze Ticker
```bash
curl -X POST https://discord-trading-bot-production.up.railway.app/analyze \
  -H "Content-Type: application/json" \
  -d '{"ticker": "AAPL", "trade_type": "day"}'
```

---

## 🎯 Success Checklist

- [ ] Schwab developer account created
- [ ] App Key + Secret obtained
- [ ] Local `.env` configured
- [ ] Refresh token obtained
- [ ] Railway variables updated
- [ ] Railway health check passes
- [ ] Analyze endpoint returns data
- [ ] Token monitor installed
- [ ] Token monitor test passes

**When all checked:** You have real-time market data + automated monitoring! 🎉

---

## 💡 Pro Tips

1. **Test on Sunday evening** before Monday market open
2. **Monitor expires on Day 7** - refresh on Day 6 to be safe
3. **Calendar reminder** every Monday: "Check token status"
4. **Railway has old token?** Check Variables page, not `.env`
5. **Market closed?** Test with SPY or QQQ (always active)

---

**Total Setup Time**: 15 minutes
**Weekly Maintenance**: 2 minutes (when warned)
**Daily Monitoring**: Automated

**You're ready to trade! 🚀**
