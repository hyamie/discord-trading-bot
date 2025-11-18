# Discord Trading Bot Setup Guide

**Status**: Ready to Deploy
**Estimated Time**: 20 minutes
**Prerequisites**: FastAPI backend deployed on Railway

---

## Overview

This guide will help you set up the Discord bot that connects to your FastAPI trading analysis backend. Users will be able to request trade analysis directly in Discord by mentioning ticker symbols.

## Architecture

```
Discord Message → n8n Workflow → FastAPI /analyze → Discord Reply
    "SPY"              ↓              ↓                ↓
                  Parse Ticker    Get Analysis    Format Response
                                 (3-Tier MTF)     (Trade Plan)
```

---

## Part 1: Create Discord Bot (5 minutes)

### Step 1: Go to Discord Developer Portal
1. Visit https://discord.com/developers/applications
2. Click "New Application"
3. Name: `Trading Bot` (or your preference)
4. Click "Create"

### Step 2: Configure Bot
1. Go to "Bot" tab in left sidebar
2. Click "Add Bot"
3. Click "Reset Token" and copy the token
   - **IMPORTANT**: Save this token securely - you'll need it for n8n

### Step 3: Set Bot Permissions
1. Still in "Bot" tab, scroll to "Privileged Gateway Intents"
2. Enable:
   - ✅ MESSAGE CONTENT INTENT
   - ✅ SERVER MEMBERS INTENT (optional)
3. Scroll to "Bot Permissions"
4. Select:
   - ✅ Read Messages/View Channels
   - ✅ Send Messages
   - ✅ Read Message History

### Step 4: Get Bot Invite Link
1. Go to "OAuth2" → "URL Generator"
2. Select scopes:
   - ✅ `bot`
3. Select bot permissions (same as above):
   - ✅ Read Messages/View Channels
   - ✅ Send Messages
   - ✅ Read Message History
4. Copy the generated URL at the bottom

### Step 5: Invite Bot to Server
1. Paste the URL in browser
2. Select your Discord server
3. Click "Authorize"
4. The bot should now appear in your server (offline)

---

## Part 2: Get Discord Channel ID (2 minutes)

### Step 1: Enable Developer Mode
1. Open Discord
2. Settings → Advanced
3. Enable "Developer Mode"

### Step 2: Get Channel ID
1. Right-click the channel where you want the bot to respond
2. Click "Copy Channel ID"
3. Save this ID - you'll need it for n8n

---

## Part 3: Import n8n Workflow (8 minutes)

### Step 1: Login to n8n Cloud
1. Visit https://hyamie.app.n8n.cloud/
2. Login with your credentials

### Step 2: Import Workflow
1. Click "Workflows" in sidebar
2. Click "Add workflow" (or press `+`)
3. Click the `⋮` menu (top right)
4. Select "Import from File"
5. Choose: `C:\ClaudeAgents\projects\discord-trading-bot\workflows\discord_trading_bot_v2.json`

### Step 3: Configure Discord Credentials
1. In the workflow, click on "Discord Trigger" node
2. Under "Credentials", click "Select Credential" dropdown
3. Click "Create New Credential"
4. Enter your Discord Bot Token (from Part 1, Step 2)
5. Click "Save"
6. Select the newly created credential

**Repeat for all Discord nodes**:
- Discord Trigger
- Discord Reply
- Error Handler

### Step 4: Update Channel ID (Optional)
If you want to restrict the bot to specific channels:
1. Click "Parse Ticker & Trade Type" node
2. Find the line: `channel_id: $json.channel_id`
3. You can add channel filtering in this node if needed

### Step 5: Test the Workflow
1. Click "Test workflow" button (top right)
2. Go to Discord and send a message with a ticker: `SPY`
3. The workflow should trigger and you'll see the execution in n8n
4. Check Discord for the bot's reply

### Step 6: Activate the Workflow
1. Click the toggle switch at the top (should turn blue/green)
2. The workflow is now live!

---

## Part 4: Test the Bot (5 minutes)

### Supported Commands

The bot recognizes these message formats:

**Basic ticker lookup**:
```
SPY
$AAPL
MSFT
```

**Explicit trade type**:
```
SPY swing          # Request swing trade analysis
AAPL day           # Request day trade analysis (default)
QQQ both           # Request both day and swing analysis
```

**Natural language** (works too):
```
analyze TSLA
check NVDA
!ticker SPY
```

### Expected Responses

**When trade setup is found**:
```
📈 SPY - DAY TRADE SETUP

Direction: LONG
Confidence: 4/5 ⭐⭐⭐⭐

Entry: $658.00
Stop: $655.50
Target 1: $660.50 (1R)
Target 2: $663.00 (2R)
Risk/Reward: 2R

Edges Applied:
✓ Slope Filter (EMA20 rising strongly)
✓ Volume Confirmation (1.5x average)

Rationale:
Long setup with 30m bullish trend confirmed by daily momentum.
Strong conviction with 2 edges: Slope Filter, Volume Confirmation.
News sentiment neutral.

Risk Notes:
Risk 2R (Entry to stop = $2.50); Risk 1-2% of capital per trade;
ATR: $2.50 (volatility measure); Monitor SPY for market context

Analysis Timestamp: 11/18/2025, 9:45:00 AM CT
```

**When no setup is found**:
```
SPY - No trade setups found

The 3-Tier Multi-Timeframe analysis did not find any high-confidence
trade setups. This typically means:
• Trends don't align across timeframes
• Market is ranging/choppy
• No clear entry trigger

This is good - the bot avoids low-probability trades!
```

**When error occurs**:
```
⚠️ Error analyzing SPY: Service temporarily unavailable

Please try again or contact support if the issue persists.
```

---

## Troubleshooting

### Bot doesn't respond
1. **Check n8n workflow is active** (toggle should be on)
2. **Check Discord bot is online** (should show as online in server)
3. **Check channel permissions** - bot needs "Read Messages" and "Send Messages"
4. **Check n8n execution log** - look for errors in recent executions

### Bot responds with error
1. **Check Railway deployment** - visit https://discord-trading-bot-production-f596.up.railway.app/health
2. **Check Schwab credentials** - ensure SCHWAB_REFRESH_TOKEN is valid
3. **Check n8n logs** - click on failed execution to see error details

### "Invalid ticker" or empty response
1. **Ticker format** - use 1-5 uppercase letters (SPY, AAPL, MSFT)
2. **Market hours** - during market hours you'll get more data
3. **Valid symbols** - ensure ticker exists (try on Yahoo Finance first)

---

## Advanced Configuration

### Customize Response Format

Edit the "Format Discord Response" node to change how results are displayed:

**Add emojis**:
```javascript
const directionEmoji = plan.direction === 'long' ? '🚀' : '📉';
```

**Change timestamp format**:
```javascript
new Date(data.analysis_timestamp).toLocaleString('en-US', {
  timeZone: 'America/New_York',
  dateStyle: 'short',
  timeStyle: 'short'
})
```

**Add market hours check**:
```javascript
const now = new Date();
const hour = now.getHours();
const isMarketHours = hour >= 9 && hour < 16; // 9 AM - 4 PM ET

if (!isMarketHours) {
  response += '\\n\\n*Note: Market is currently closed*';
}
```

### Add Reaction Emojis

You can make the bot react to messages:

1. Add a "Discord" node after "Parse Ticker"
2. Set operation to "Add Reaction"
3. Choose emoji (👍, 📊, 🔍, etc.)

### Multi-Channel Support

To allow the bot in multiple channels:

1. Get channel IDs for all channels
2. In "Parse Ticker & Trade Type" node, add filter:

```javascript
const allowedChannels = [
  'CHANNEL_ID_1',
  'CHANNEL_ID_2',
  'CHANNEL_ID_3'
];

if (!allowedChannels.includes($json.channel_id)) {
  return [];
}
```

### Rate Limiting

To prevent spam:

1. Add a "Redis" or "Memory Store" node
2. Track last request time per user
3. Reject if < 10 seconds since last request

---

## Monitoring & Maintenance

### Check Bot Health
```bash
# Test FastAPI backend
curl https://discord-trading-bot-production-f596.up.railway.app/health
```

### Monitor n8n Executions
1. Go to https://hyamie.app.n8n.cloud/
2. Click "Executions" in sidebar
3. Review recent runs for errors

### Update Workflow
1. Make changes in n8n editor
2. Click "Save"
3. Changes take effect immediately (workflow stays active)

---

## Usage Examples

### Quick Analysis
```
User: SPY
Bot: [Full analysis with entry, stop, targets]
```

### Swing Trade
```
User: AAPL swing
Bot: [Swing trade analysis with weekly/daily timeframes]
```

### Multiple Tickers
```
User: SPY AAPL MSFT
Bot: [Responds to first ticker only - SPY]
```

*To analyze multiple tickers, send separate messages*

---

## Security Notes

1. **Bot Token**: Keep your Discord bot token secret - never commit to Git
2. **n8n Credentials**: Stored securely in n8n Cloud (encrypted)
3. **API Rate Limits**: Schwab allows 120 calls/min - bot uses ~1 call per ticker
4. **Channel Restrictions**: Consider limiting bot to specific channels

---

## Cost & Performance

### API Calls per Request
- 1 call to FastAPI `/analyze`
- FastAPI makes 3 calls to Schwab (higher, middle, lower timeframes)
- **Total**: ~3-4 Schwab API calls per Discord message

### Response Time
- Typical: 2-5 seconds
- Includes: Data fetching + indicator calculation + LLM rationale (if enabled)

### Limits
- **Schwab API**: 120 calls/minute = ~30 ticker requests/minute
- **n8n Cloud**: No execution limits on Pro plan
- **Discord**: Standard rate limits apply

---

## Next Steps

1. ✅ Deploy Discord bot
2. ✅ Test with various tickers
3. 📊 Monitor usage and performance
4. 🔧 Customize response format to your preference
5. 📈 Share bot with trading group
6. 🤖 Consider adding more commands (help, list, stats)

---

## Support

**Documentation**:
- FastAPI Docs: `/docs` endpoint on Railway
- n8n Docs: https://docs.n8n.io
- Discord API: https://discord.com/developers/docs

**Troubleshooting**:
1. Check `SESSION_HANDOFF_LIVE_MARKET.md` for FastAPI setup
2. Check n8n execution logs for errors
3. Check Railway logs: `railway logs --tail 100`

**Quick Reference**:
- n8n Cloud: https://hyamie.app.n8n.cloud/
- Railway Dashboard: https://railway.app/dashboard
- FastAPI Health: https://discord-trading-bot-production-f596.up.railway.app/health

---

**Status**: Ready for Production ✅
**Last Updated**: 2025-11-18
**Version**: 2.0 (FastAPI Integration)
