# Discord Trading Bot - Quick Start

**Time to Deploy**: 20 minutes
**Status**: Ready ✅

---

## What You're Getting

A Discord bot that lets you and your trading group request professional-grade trade analysis simply by typing ticker symbols in chat.

**Example**:
```
You: SPY
Bot: 📈 SPY - DAY TRADE SETUP

     Direction: LONG
     Confidence: 4/5 ⭐⭐⭐⭐

     Entry: $658.00
     Stop: $655.50
     Targets: $660.50 / $663.00

     [Full analysis with edges, rationale, risk notes]
```

---

## The 20-Minute Setup

### Prerequisites (Already Done ✅)
- ✅ FastAPI backend deployed on Railway
- ✅ Schwab API working with live market data
- ✅ 3-Tier MTF analysis engine operational

### 3 Steps to Go Live

#### Step 1: Create Discord Bot (5 min)
1. Go to https://discord.com/developers/applications
2. Create new application → Add bot
3. Copy bot token (you'll paste it in n8n)
4. Enable "Message Content Intent"
5. Generate invite URL and add bot to your server

**Detailed guide**: See Part 1 in `DISCORD_BOT_SETUP.md`

#### Step 2: Import n8n Workflow (8 min)
1. Login to https://hyamie.app.n8n.cloud/
2. Import workflow from: `workflows/discord_trading_bot_v2.json`
3. Add your Discord bot token to all Discord nodes
4. Click "Activate workflow"

**Detailed guide**: See Part 3 in `DISCORD_BOT_SETUP.md`

#### Step 3: Test It! (2 min)
1. Go to your Discord server
2. Type: `SPY`
3. Wait 3-5 seconds
4. Bot should reply with trade analysis

---

## How It Works

```
Discord          n8n             FastAPI         Discord
  ↓               ↓                 ↓               ↓
"SPY"  →  Parse Ticker  →  /analyze  →  Format  →  Reply
           +trade_type      (Schwab     Response    with
                            + 3-Tier              Trade
                             MTF)                  Plan
```

**The Flow**:
1. User types ticker in Discord
2. n8n workflow catches the message
3. Sends ticker to your FastAPI backend
4. Backend fetches live data from Schwab
5. Runs 3-Tier Multi-Timeframe analysis
6. Returns trade plan (or "no setup" if market is choppy)
7. n8n formats the response beautifully
8. Bot replies in Discord thread

---

## What Users Can Do

### Basic Commands
```
SPY              # Day trade analysis (default)
$AAPL            # Day trade analysis
MSFT swing       # Swing trade analysis
QQQ both         # Both day and swing analysis
```

### Natural Language (Also Works)
```
analyze TSLA
check NVDA
!ticker SPY
```

---

## Response Types

### ✅ High-Confidence Setup Found
- Entry, stop, and two targets
- Risk/reward ratio
- Confidence score (1-5 stars)
- Edge filters applied
- AI-generated rationale
- Risk management notes
- Market context

### ⚠️ No Setup Found
- Clear explanation why
- Market conditions summary
- "This is good - avoiding bad trades"

### ❌ Error
- User-friendly error message
- Suggestion to retry

---

## Why This is Powerful

### For Day Trading
- **Higher TF**: 30-minute bars (macro trend)
- **Middle TF**: Daily bars (trend confirmation)
- **Lower TF**: 1-minute bars (precise entry)

### For Swing Trading
- **Higher TF**: Weekly bars (macro trend)
- **Middle TF**: Daily bars (confirmation)
- **Lower TF**: 30-minute bars (entry zone)

### Safety Features
- Only generates plans when all timeframes align
- Avoids choppy/ranging markets
- 5 edge filters for high-probability setups
- ATR-based risk management
- Confidence scoring prevents overtrading

---

## Quick Test Checklist

After setup, test these scenarios:

- [ ] `SPY` - Should return analysis
- [ ] `AAPL swing` - Should return swing analysis
- [ ] `XYZ` - Invalid ticker should handle gracefully
- [ ] Message from bot - Should ignore (not loop)
- [ ] Random chat - Should only respond to tickers

---

## Monitoring

### Check Backend Health
```bash
curl https://discord-trading-bot-production-f596.up.railway.app/health
```

Should return: `{"status":"healthy"}`

### Check n8n Executions
1. Visit https://hyamie.app.n8n.cloud/
2. Click "Executions"
3. See real-time workflow runs

### Check Bot is Online
- Bot should show as "Online" in Discord server
- If offline, check n8n workflow is activated

---

## Usage Limits

- **Schwab API**: 120 calls/minute
- **Per ticker**: ~3 API calls
- **Capacity**: ~30-40 ticker requests per minute
- **Response time**: 2-5 seconds

For most trading groups, this is MORE than enough.

---

## Customization Options

Want to customize the bot? Easy! Edit the "Format Discord Response" node:

### Add Your Branding
```javascript
const response = `🤖 **${ticker}** Trading Analysis\\n\\n` +
  `*Powered by [Your Name] Trading System*\\n\\n` +
  // ... rest of response
```

### Change Emoji
```javascript
const directionEmoji = plan.direction === 'long' ? '🚀' : '💥';
```

### Add Disclaimers
```javascript
const disclaimer = '\\n\\n*Not financial advice. Trade at your own risk.*';
return [{ response: response + disclaimer, ... }];
```

---

## Troubleshooting

### "Bot not responding"
1. Check workflow is active (toggle on)
2. Check bot has permissions in channel
3. Check n8n execution log for errors

### "Error analyzing ticker"
1. Check Railway backend is up
2. Check Schwab refresh token is valid
3. Try a different ticker (SPY always works)

### "Response is slow"
- Normal during first request after idle (cold start)
- Subsequent requests are 2-5 seconds
- Schwab API fetches live data (worth the wait!)

---

## Next Steps After Setup

1. **Share with trading group** - Invite members to the Discord channel
2. **Set usage guidelines** - Maybe 1-2 queries per user per minute
3. **Monitor performance** - Check n8n execution times
4. **Collect feedback** - See what tickers people analyze most
5. **Customize formatting** - Make it yours!

---

## Support Files

- **Full Setup Guide**: `DISCORD_BOT_SETUP.md` (comprehensive)
- **FastAPI Guide**: `SESSION_HANDOFF_LIVE_MARKET.md` (backend)
- **Workflow File**: `workflows/discord_trading_bot_v2.json`

---

## What's Working Right Now

✅ FastAPI backend (Railway)
✅ Schwab API integration (live data)
✅ 3-Tier Multi-Timeframe analysis
✅ Technical indicators (EMA, MACD, RSI, ATR)
✅ 5 edge filters
✅ Confidence scoring
✅ AI rationale generation
✅ n8n workflow (ready to import)
✅ Discord bot framework

**What's Left**: Just your 20 minutes to set it up!

---

**Ready to go?** Open `DISCORD_BOT_SETUP.md` and follow the detailed steps.

**Questions?** All answers are in the full setup guide.

**Let's go! 🚀**
