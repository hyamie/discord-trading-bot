# Trading Bot API - Deployment Guide

**Version**: 1.0.0
**Last Updated**: 2025-11-12
**Architecture**: Hybrid (n8n Cloud + Railway Python API + Supabase)

---

## Quick Start Summary

1. **Deploy Python API to Railway** (~30 min)
2. **Setup Supabase Database** (~15 min)
3. **Configure n8n Workflows** (~1 hour)
4. **Test End-to-End** (~30 min)

**Total**: ~2-3 hours to fully deployed system

---

## Prerequisites

### Required API Keys

- [ ] **Schwab API**: Key + Secret (developer.schwab.com) ✅ APPROVED
- [ ] **Anthropic Claude** OR **OpenAI GPT**: For trade rationale generation
- [ ] **Railway Account**: Free tier (railway.app)
- [ ] **Supabase Account**: Already have subscription ✅
- [ ] **n8n Cloud**: Already have subscription ✅

### Optional API Keys

- [ ] **Finnhub**: Free tier (finnhub.io) - Company news
- [ ] **NewsAPI**: Free tier (newsapi.org) - Market news
- [ ] **Alpha Vantage**: Free tier (alphavantage.co) - Backup price data

---

## Part 1: Deploy Python API to Railway

### Step 1: Setup Repository

```bash
# Initialize Git (if not done)
cd C:\ClaudeAgents\projects\discord-trading-bot
git init
git add .
git commit -m "Initial FastAPI trading bot implementation"

# Create GitHub repository
gh repo create discord-trading-bot --public --source=. --remote=origin --push
```

### Step 2: Deploy to Railway

#### Option A: Deploy via GitHub (Recommended)

1. Go to https://railway.app
2. Click "New Project" → "Deploy from GitHub repo"
3. Select `discord-trading-bot` repository
4. Railway will auto-detect Dockerfile
5. Click "Deploy Now"

#### Option B: Deploy via Railway CLI

```bash
# Install Railway CLI
npm i -g @railway/cli

# Login
railway login

# Initialize project
railway init

# Deploy
railway up
```

### Step 3: Configure Environment Variables

In Railway dashboard, go to **Variables** tab and add:

**Required**:
```
SCHWAB_API_KEY=your_actual_key
SCHWAB_API_SECRET=your_actual_secret
SCHWAB_REDIRECT_URI=https://localhost:8080/callback
ANTHROPIC_API_KEY=your_actual_key
LLM_MODEL=claude-3-5-sonnet-20241022
```

**Database** (Supabase - add after Step 4):
```
SUPABASE_URL=https://xxxxx.supabase.co
SUPABASE_KEY=your_anon_key
DATABASE_URL=postgresql://postgres:password@db.xxxxx.supabase.co:5432/postgres
```

**Optional**:
```
FINNHUB_API_KEY=your_key
NEWSAPI_KEY=your_key
ALPHA_VANTAGE_API_KEY=your_key
```

### Step 4: Get Railway URL

After deployment, Railway provides a URL like:
```
https://discord-trading-bot-production.up.railway.app
```

**Test it**:
```bash
curl https://your-app.railway.app/health
```

Expected response:
```json
{
  "status": "healthy",
  "timestamp": "2025-11-12T10:30:00Z",
  "version": "1.0.0",
  "services": {
    "schwab_api": true,
    "news_api": true,
    "database": false,
    "llm": true
  }
}
```

---

## Part 2: Setup Supabase Database

### Step 1: Create New Supabase Project

1. Go to https://supabase.com/dashboard
2. Click "New Project"
3. Name: `trading-bot`
4. Database Password: Generate strong password (save it!)
5. Region: Choose closest to you
6. Click "Create Project" (takes ~2 min)

### Step 2: Run Schema SQL

1. In Supabase dashboard, go to **SQL Editor**
2. Click "New Query"
3. Copy contents of `src/database/schema.sql`
4. Paste into SQL editor
5. Click "Run" (creates all tables, indexes, views)

### Step 3: Get Connection Details

In Supabase dashboard, go to **Settings** → **Database**:

**Copy these values**:
- **URL**: `https://xxxxx.supabase.co`
- **Anon Key**: `eyJhbGc...` (public, safe to expose)
- **Service Role Key**: `eyJhbGc...` (secret, use for server-side)
- **Connection String**: `postgresql://postgres:[password]@db.xxxxx.supabase.co:5432/postgres`

### Step 4: Update Railway Environment Variables

In Railway dashboard, add:
```
SUPABASE_URL=https://xxxxx.supabase.co
SUPABASE_KEY=your_anon_key
DATABASE_URL=postgresql://postgres:[YOUR_PASSWORD]@db.xxxxx.supabase.co:5432/postgres
```

### Step 5: Restart Railway Service

Railway will auto-restart after adding env vars. Check health:
```bash
curl https://your-app.railway.app/health
```

Now `database: true` should show in response.

---

## Part 3: Setup n8n Workflows

### Workflow 1: Discord Analysis Request

**Trigger**: Discord Webhook (when user types `!analyze TICKER`)

#### Step 1: Create Discord Webhook Trigger

1. In n8n, create new workflow: "Discord Trading Analysis"
2. Add node: **Webhook** (trigger)
3. Set Webhook URL: `https://your-n8n-instance.app.n8n.cloud/webhook/discord-analyze`
4. Method: POST
5. Save webhook URL (configure in Discord bot later)

#### Step 2: Parse Discord Message

Add node: **Code** (JavaScript)
```javascript
// Extract ticker from Discord message
const message = $input.item.json.content || "";
const match = message.match(/!analyze\s+([A-Z]{1,5})(?:\s+(day|swing|both))?/i);

if (!match) {
  return [{
    json: {
      error: "Invalid command. Use: !analyze TICKER [day|swing|both]"
    }
  }];
}

return [{
  json: {
    ticker: match[1].toUpperCase(),
    trade_type: match[2] ? match[2].toLowerCase() : "both",
    discord_user: $input.item.json.author.username,
    discord_channel: $input.item.json.channel_id
  }
}];
```

#### Step 3: Call Railway Python API

Add node: **HTTP Request**
- Method: POST
- URL: `https://your-app.railway.app/analyze`
- Headers:
  - `Content-Type`: `application/json`
- Body (JSON):
  ```json
  {
    "ticker": "{{ $json.ticker }}",
    "trade_type": "{{ $json.trade_type }}"
  }
  ```

#### Step 4: Save to Supabase

Add node: **Supabase** → **Insert**
- Table: `trade_ideas`
- Rows:
  ```json
  {
    "id": "{{ $json.plans[0].trade_id }}",
    "ticker": "{{ $json.plans[0].ticker }}",
    "trade_type": "{{ $json.plans[0].trade_type }}",
    "direction": "{{ $json.plans[0].direction }}",
    "entry": {{ $json.plans[0].entry }},
    "stop": {{ $json.plans[0].stop }},
    "target": {{ $json.plans[0].target }},
    "confidence": {{ $json.plans[0].confidence }},
    "rationale": "{{ $json.plans[0].rationale }}",
    "edges_applied": "{{ JSON.stringify($json.plans[0].edges) }}",
    "atr_value": {{ $json.plans[0].atr_value }},
    "market_volatility": "{{ $json.plans[0].market_volatility }}",
    "discord_user_id": "{{ $('Code').item.json.discord_user }}"
  }
  ```

#### Step 5: Format Discord Response

Add node: **Code** (JavaScript)
```javascript
const plan = $input.item.json.plans[0];

// Build confidence stars
const stars = '⭐'.repeat(plan.confidence);

// Build edges list
const edges = plan.edges
  .filter(e => e.applied)
  .map(e => `✅ ${e.name}`)
  .join('\n');

// Format message
const message = `
📊 **${plan.ticker} ${plan.trade_type.toUpperCase()} TRADE - ${plan.direction.toUpperCase()}**
Confidence: ${plan.confidence}/5 ${stars}

**Entry**: $${plan.entry.toFixed(2)}
**Stop**: $${plan.stop.toFixed(2)} (${plan.risk_pct.toFixed(1)}%)
**Target**: $${plan.target.toFixed(2)} (+${plan.reward_pct.toFixed(1)}%)
**R:R**: 1:${plan.risk_reward_ratio}

**Edges Applied**:
${edges}

**Rationale**: ${plan.rationale}

**Trade ID**: \`${plan.trade_id}\`
*Use \`!track ${plan.trade_id} win/loss P/L\` to log outcome*
`;

return [{
  json: {
    content: message,
    channel_id: $('Code').item.json.discord_channel
  }
}];
```

#### Step 6: Send Discord Message

Add node: **HTTP Request**
- Method: POST
- URL: `https://discord.com/api/v10/channels/{{ $json.channel_id }}/messages`
- Headers:
  - `Authorization`: `Bot YOUR_DISCORD_BOT_TOKEN`
  - `Content-Type`: `application/json`
- Body:
  ```json
  {
    "content": "{{ $json.content }}"
  }
  ```

#### Step 7: Activate Workflow

Click **Active** toggle in top right.

---

### Workflow 2: Trade Tracking (Cron Every 15 Min)

**Purpose**: Check if open trades hit stop/target

#### Step 1: Schedule Trigger

1. Create new workflow: "Trade Tracking Monitor"
2. Add node: **Schedule Trigger**
3. Interval: `*/15 * * * *` (every 15 minutes)
4. Only during market hours (optional):
   - Mon-Fri
   - 9:30 AM - 4:00 PM EST

#### Step 2: Fetch Open Trades

Add node: **Supabase** → **Select**
- Table: `trade_ideas`
- Where: `status = 'active'`

#### Step 3: Check Current Prices

Add node: **HTTP Request** (loop through each trade)
- Method: GET
- URL: `https://your-app.railway.app/quote/{{ $json.ticker }}`

#### Step 4: Check Stop/Target Hits

Add node: **Code**
```javascript
const trade = $input.item.json;
const currentPrice = $('HTTP Request').item.json.price;

let outcome = null;

if (trade.direction === 'long') {
  if (currentPrice <= trade.stop) {
    outcome = {
      status: 'stop_hit',
      actual_outcome: 'loss',
      profit_loss_pct: ((currentPrice - trade.entry) / trade.entry) * 100,
      close_price: currentPrice
    };
  } else if (currentPrice >= trade.target) {
    outcome = {
      status: 'target_hit',
      actual_outcome: 'win',
      profit_loss_pct: ((currentPrice - trade.entry) / trade.entry) * 100,
      close_price: currentPrice
    };
  }
}

// Similar logic for short trades...

return outcome ? [{ json: { ...trade, ...outcome } }] : [];
```

#### Step 5: Update Supabase

Add node: **Supabase** → **Insert** (outcomes table) + **Update** (trade_ideas status)

#### Step 6: Send Discord Notification

Similar to Workflow 1, send alert when trade closes.

---

### Workflow 3: Weekly Learning Loop (Cron Every Sunday)

**Purpose**: Analyze past week's trades, suggest improvements

#### Step 1: Schedule Trigger

1. Create new workflow: "Weekly Learning Loop"
2. Add node: **Schedule Trigger**
3. Interval: `0 0 * * 0` (Sunday midnight)

#### Step 2: Fetch Week's Closed Trades

Add node: **Supabase** → **Select**
```sql
WHERE status = 'closed'
AND close_timestamp >= NOW() - INTERVAL '7 days'
```

#### Step 3: Calculate Metrics

Add node: **Code**
```javascript
const trades = $input.all();

const wins = trades.filter(t => t.json.actual_outcome === 'win').length;
const total = trades.length;
const winRate = wins / total;

const avgPL = trades.reduce((sum, t) => sum + t.json.profit_loss_r, 0) / total;

const edgePerformance = {};
// Analyze which edges had best win rates...

return [{
  json: {
    week: new Date().toISOString().slice(0, 10),
    total_trades: total,
    win_rate: winRate,
    avg_r_multiple: avgPL,
    edge_performance: edgePerformance
  }
}];
```

#### Step 4: LLM Analysis

Add node: **HTTP Request** (to Claude/GPT)
```
Analyze these trading results and suggest parameter improvements:
- Win rate: 67%
- Avg R-multiple: +1.3R
- Slope Filter: 80% win rate
- Divergence Filter: 40% win rate

Suggest specific parameter changes.
```

#### Step 5: Store Suggestions

Add node: **Supabase** → **Insert** (modifications table)

#### Step 6: Discord Summary

Send weekly report to Discord channel.

---

## Part 4: Testing End-to-End

### Test 1: Health Check

```bash
curl https://your-app.railway.app/health
```

Expected: All services `true`

### Test 2: Direct API Call

```bash
curl -X POST https://your-app.railway.app/analyze \
  -H "Content-Type: application/json" \
  -d '{"ticker": "AAPL", "trade_type": "both"}'
```

Expected: JSON with 2 trade plans (day + swing)

### Test 3: n8n Workflow

1. Manually trigger "Discord Trading Analysis" workflow in n8n
2. Set test payload:
   ```json
   {
     "content": "!analyze AAPL both",
     "author": {"username": "test_user"},
     "channel_id": "123456789"
   }
   ```
3. Check execution log - should complete successfully
4. Check Supabase `trade_ideas` table - should have new row

### Test 4: Discord Bot

1. In Discord server, type: `!analyze TSLA day`
2. Wait ~5-10 seconds
3. Bot should respond with formatted trade analysis

---

## Monitoring & Maintenance

### Logs

**Railway Logs**:
- Dashboard → Deployments → Click deployment → View Logs

**n8n Execution Logs**:
- Workflows → Select workflow → Executions tab

**Supabase Logs**:
- Dashboard → Logs

### Alerts

Setup in Axiom (optional, using Axiom MCP):
- API errors > 5/min
- Database connection failures
- Schwab API quota exceeded

### Database Cleanup

Run weekly (can automate in n8n):
```sql
-- Delete old cache entries (>7 days)
DELETE FROM market_data_cache
WHERE created_at < NOW() - INTERVAL '7 days';

-- Archive old trades (>90 days)
-- (Move to archive table if needed)
```

---

## Costs Summary

**Monthly Recurring**:
- Railway Pro: $5-7/month (24/7 uptime)
- n8n Cloud: ~$20/month (already paying ✅)
- Supabase: ~$25/month (already paying ✅)
- LLM API: $1-2/month (Claude/GPT for rationale)

**Total NEW cost**: $6-9/month (vs $70+ if n8n was wasted)

---

## Troubleshooting

### "Schwab API authentication failed"

1. Check Schwab credentials in Railway env vars
2. Ensure OAuth flow completed (may need manual auth code)
3. Check token expiration - refresh token should auto-renew

### "Database connection failed"

1. Verify Supabase DATABASE_URL in Railway
2. Check Supabase project is running (not paused)
3. Test connection from Railway shell: `railway run python -c "import psycopg2; ..."`

### "n8n workflow timeout"

1. Railway API might be slow on first request (cold start)
2. Increase n8n HTTP request timeout to 60s
3. Consider Railway Pro plan for faster cold starts

### "Trade analysis returns low confidence"

1. Check if market is volatile (affects scoring)
2. Verify indicator calculations (test with known values)
3. Review edge filter thresholds (may need tuning)

---

## Next Steps After Deployment

1. **Paper Trading**: Track suggestions for 2 weeks, don't execute trades
2. **Parameter Tuning**: Adjust edge thresholds based on results
3. **Expand Tickers**: Add more stocks to watch list
4. **Custom Edges**: Add your own proprietary filters
5. **Mobile Alerts**: Setup Discord mobile notifications
6. **Dashboard**: Build Supabase dashboard for visual analytics

---

## Support & Resources

- **Railway Docs**: https://docs.railway.app
- **Supabase Docs**: https://supabase.com/docs
- **n8n Docs**: https://docs.n8n.io
- **FastAPI Docs**: https://fastapi.tiangolo.com
- **Discord Bot Setup**: https://discord.com/developers/docs

---

**Deployed by**: Claude Code (Donnie)
**Date**: 2025-11-12
**Status**: Ready for deployment! 🚀
