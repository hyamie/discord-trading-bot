# Schwab Token Automation Guide

**Problem**: Schwab API refresh tokens expire every 7 days, requiring manual re-authentication.

**Solution**: Automated monitoring system with daily checks and reminders.

---

## 🎯 Overview

This automated system solves the 7-day Schwab refresh token expiry problem with:

1. **Token Monitoring** - Daily automated checks of token expiry
2. **Early Warnings** - Alerts when token has <24 hours remaining
3. **Easy Refresh** - One-command token renewal process
4. **Metadata Tracking** - Local storage of token creation/expiry dates

---

## 📦 Components

### 1. Token Monitor (`scripts/schwab_token_monitor.py`)

**What it does:**
- Checks when your refresh token expires
- Tests if token is still valid
- Warns you when action is needed (< 24 hours remaining)
- Saves token metadata locally

**Exit codes:**
- `0` = Token healthy (> 1 day remaining)
- `1` = Action required (token expiring or expired)

**Run manually:**
```bash
cd C:\ClaudeAgents\projects\discord-trading-bot
python scripts/schwab_token_monitor.py
```

**Output example:**
```
============================================================
Schwab Token Monitor - Starting Check
============================================================
Status: HEALTHY
Message: Token healthy - 5.2 days remaining
Days remaining: 5.23
Hours remaining: 125.52

Testing token validity...
✅ Refresh token is valid - successfully obtained access token

✅ Token is healthy - no action needed
```

---

### 2. OAuth Helper (`scripts/schwab_oauth_helper.py`)

**What it does:**
- Opens browser for Schwab login
- Obtains new refresh token (valid 7 days)
- Saves token metadata for monitoring
- Provides Railway deployment instructions

**When to run:**
- Initial setup
- Every 7 days (or when monitor warns)
- After token expiry

**Run:**
```bash
cd C:\ClaudeAgents\projects\discord-trading-bot
python scripts/schwab_oauth_helper.py
```

**Process:**
1. Opens browser → Schwab login
2. You approve the app
3. Script captures authorization code
4. Exchanges code for refresh token
5. Displays token + Railway update instructions
6. Saves metadata to `data/schwab_token_metadata.json`

---

### 3. Task Scheduler Setup (`scripts/setup_schwab_monitor.ps1`)

**What it does:**
- Creates Windows Scheduled Task for daily monitoring
- Runs at 9:00 AM every day
- Also runs 5 minutes after system startup
- Provides exit code for automation (0=good, 1=action needed)

**Install:**
```powershell
cd C:\ClaudeAgents\projects\discord-trading-bot\scripts
.\setup_schwab_monitor.ps1 -Install
```

**Test:**
```powershell
.\setup_schwab_monitor.ps1 -Test
```

**Uninstall:**
```powershell
.\setup_schwab_monitor.ps1 -Uninstall
```

---

## 🚀 Quick Start Guide

### Initial Setup (15 minutes)

**Step 1: Get Schwab credentials** (if you don't have them)
1. Go to https://developer.schwab.com
2. Register for developer account
3. Create app with callback: `https://127.0.0.1:8080/callback`
4. Save App Key and Secret

**Step 2: Set environment variables**

Create `.env` file in project root:
```bash
SCHWAB_API_KEY=your_app_key
SCHWAB_API_SECRET=your_app_secret
SCHWAB_REDIRECT_URI=https://127.0.0.1:8080/callback
```

**Step 3: Get initial refresh token**
```bash
python scripts/schwab_oauth_helper.py
```
- Follow browser prompts
- Log in with Schwab brokerage credentials
- Copy the SCHWAB_REFRESH_TOKEN

**Step 4: Update Railway**
1. Go to Railway → Your Project → Variables
2. Add/update: `SCHWAB_REFRESH_TOKEN=<token_from_step_3>`
3. Railway auto-redeploys

**Step 5: Install automated monitoring**
```powershell
cd C:\ClaudeAgents\projects\discord-trading-bot\scripts
.\setup_schwab_monitor.ps1 -Install
```

**Done!** The system will now check your token daily.

---

## 📅 Weekly Maintenance (2 minutes)

### When Monitor Warns "Action Required"

**Option A: Manual (recommended for first time)**
```bash
# 1. Run OAuth helper
python scripts/schwab_oauth_helper.py

# 2. Copy the new SCHWAB_REFRESH_TOKEN

# 3. Update Railway
#    Railway → Settings → Variables → SCHWAB_REFRESH_TOKEN
```

**Option B: Quick CLI**
```bash
# Run helper, get token, manually update Railway
cd C:\ClaudeAgents\projects\discord-trading-bot
python scripts/schwab_oauth_helper.py
```

**After updating Railway:**
- Railway automatically redeploys
- Wait 2-3 minutes for deployment
- Test: `curl https://discord-trading-bot-production.up.railway.app/health`
- Should show `"schwab_api": true`

---

## 🔧 How It Works

### Token Lifecycle

```
Day 0: Get Refresh Token
   ↓
   ├─ Access Token (30 min TTL) ← Auto-refreshed by SchwabAPIClient
   └─ Refresh Token (7 days TTL) ← Requires manual renewal

Day 1-5: Daily Monitor Checks
   ✅ Status: Healthy

Day 6: Daily Monitor Checks
   ⚠️  Status: Warning (< 24 hours)
   📧 Action Required

Day 7: Token Expires
   ❌ Status: Expired
   🚨 API calls will fail
```

### Monitoring Flow

```
Task Scheduler (9 AM daily)
   ↓
schwab_token_monitor.py
   ↓
Load metadata (data/schwab_token_metadata.json)
   ↓
Calculate days remaining
   ↓
Test token validity (API call)
   ↓
   ├─ Healthy (>1 day) → Exit 0 → No alert
   └─ Warning/Expired → Exit 1 → Take action!
```

### Refresh Flow

```
schwab_oauth_helper.py
   ↓
Open browser → Schwab login
   ↓
User approves app
   ↓
Get authorization code
   ↓
Exchange for refresh token
   ↓
Save metadata locally
   ↓
Display Railway update instructions
   ↓
User updates Railway env var
   ↓
Railway auto-redeploys
```

---

## 📊 Files and Locations

| File | Purpose | Location |
|------|---------|----------|
| **schwab_token_monitor.py** | Daily token check | `scripts/` |
| **schwab_oauth_helper.py** | Get new token | `scripts/` |
| **setup_schwab_monitor.ps1** | Task Scheduler setup | `scripts/` |
| **schwab_token_metadata.json** | Token metadata (created on first run) | `data/` |
| **.env** | Local credentials (NOT in git) | Project root |

---

## 🛠️ Troubleshooting

### "Token expired" but you just refreshed it

**Cause**: Railway still has old token

**Fix:**
```bash
# Verify Railway has new token
railway variables

# If old, update it
# Railway → Settings → Variables → SCHWAB_REFRESH_TOKEN
```

---

### Monitor shows "No token metadata found"

**Cause**: First run, or metadata file missing

**Fix:**
```bash
# Run OAuth helper to create metadata
python scripts/schwab_oauth_helper.py
```

---

### Task Scheduler not running

**Check task exists:**
```powershell
Get-ScheduledTask -TaskName "SchwabTokenMonitor"
```

**Check last run:**
```powershell
Get-ScheduledTaskInfo -TaskName "SchwabTokenMonitor"
```

**Test manually:**
```powershell
.\setup_schwab_monitor.ps1 -Test
```

---

### "Unauthorized" error when testing token

**Possible causes:**
1. Token expired (>7 days old)
2. Token was manually revoked
3. Wrong API credentials

**Fix:**
```bash
# Get fresh token
python scripts/schwab_oauth_helper.py

# Verify .env has correct credentials
cat .env | grep SCHWAB
```

---

## 🔔 Future Enhancements

### Potential additions:
- [ ] Email notifications when token expiring
- [ ] Slack/Discord webhook alerts
- [ ] Auto-update Railway via API (requires Railway API token)
- [ ] Desktop notifications (Windows Toast)
- [ ] SMS alerts via Twilio
- [ ] Browser extension for one-click refresh

---

## 📚 Related Documentation

- **SCHWAB_SETUP_GUIDE.md** - Complete Schwab API setup
- **NEXT_STEPS_SCHWAB.md** - Quick action items
- **PROJECT_STATUS.md** - Overall project status

---

## 💡 Tips

### Best Practices

1. **Run monitor manually once a week** even if not automated
   ```bash
   python scripts/schwab_token_monitor.py
   ```

2. **Keep credentials secure**
   - Never commit `.env` to git
   - Store Railway tokens in secure password manager

3. **Set calendar reminder**
   - Every Monday: Check token status
   - Easier than debugging expired tokens!

4. **Test after Railway updates**
   ```bash
   curl https://discord-trading-bot-production.up.railway.app/health
   # Should show "schwab_api": true
   ```

### Common Workflow

**Sunday evening prep:**
```bash
# Check status
python scripts/schwab_token_monitor.py

# If expiring soon, refresh now
python scripts/schwab_oauth_helper.py

# Update Railway immediately
# (avoids Monday morning market open issues)
```

---

## 🎯 Success Metrics

**You know it's working when:**
- ✅ Task Scheduler shows "Running" status
- ✅ `data/schwab_token_metadata.json` exists
- ✅ Monitor exit code = 0 (healthy)
- ✅ Railway `/health` shows `"schwab_api": true`
- ✅ `/analyze` endpoint returns trade plans with real data

---

## 📞 Quick Reference

### Daily Check
```bash
python scripts/schwab_token_monitor.py
```

### Weekly Refresh (when warned)
```bash
python scripts/schwab_oauth_helper.py
# → Copy token → Update Railway
```

### Install Automation
```powershell
.\setup_schwab_monitor.ps1 -Install
```

### Test Everything
```powershell
.\setup_schwab_monitor.ps1 -Test
```

---

**Status**: Automated token monitoring system complete
**Maintenance**: 2 minutes per week
**Reliability**: Daily checks prevent token expiry surprises
**Last Updated**: 2025-11-17
