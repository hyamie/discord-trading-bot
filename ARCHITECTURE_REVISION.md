# Discord Trading Bot - Architecture Revision

**Date**: 2025-11-12
**Status**: CRITICAL UPDATE - Re-evaluation based on new constraints

---

## Executive Summary

**RECOMMENDATION CHANGE**: From Pure Python to **Hybrid (n8n Cloud + Railway Python Microservice)**

**Reason**: User is already paying for n8n Cloud (~$20/month) and Supabase (~$25/month). Original recommendation of Pure Python to Railway ($5-7/month) would WASTE the n8n subscription while adding a new cost. Better to use BOTH tools for the same incremental cost.

**New Incremental Cost**: $5-7/month (same as original, but uses existing subscriptions)

---

## Cost Analysis Revision

### Sunk Costs (Already Paying - Don't Count)
- n8n Cloud: ~$20/month
- Supabase: ~$25/month (has PostgreSQL, not SQLite-only)
- Docker Desktop: $0 (installed locally, free for personal use)

### Original Recommendation (Pure Python to Railway)
**Incremental Cost**: +$5-7/month for Railway hosting
**Wasted Resources**: n8n Cloud subscription unused

### Revised Recommendation (Hybrid: n8n + Railway Python)
**Incremental Cost**: +$5-7/month for Railway hosting (SAME as pure Python)
**Used Resources**: n8n Cloud + Supabase + Railway
**Benefit**: Leverages ALL existing subscriptions

### Alternative Options Considered

| Option | Incremental Cost | Complexity | Reliability | Uses n8n | Uses Supabase | Verdict |
|--------|-----------------|------------|-------------|----------|---------------|---------|
| **Hybrid (n8n + Railway Python)** | **$5-7/month** | **MEDIUM** | **HIGH** | ✅ Yes | ✅ Yes | ⭐⭐⭐⭐⭐ **BEST** |
| Pure Python (Railway) | $5-7/month | LOW | HIGH | ❌ No | ✅ Yes | ⭐⭐⭐ (wastes n8n) |
| n8n-only | $0 | LOW | HIGH | ✅ Yes | ✅ Yes | ⭐⭐ (TA logic awkward in JavaScript) |
| Pure Python (local Docker) | $0-10 | LOW | MEDIUM | ❌ No | ✅ Yes | ⭐⭐⭐ (PC must run 24/7) |
| Hybrid (n8n + local Docker) | $0-10 | HIGH | MEDIUM | ✅ Yes | ✅ Yes | ⭐⭐ (complexity not worth savings) |

---

## Revised Architecture: Hybrid (n8n Cloud + Railway Python Microservice)

### System Overview

```
Discord Webhook → n8n Cloud (Orchestration Layer)
                      ↓
                  [Business Logic]
                  - Parse Discord command
                  - Validate ticker symbol
                  - Check rate limits
                  - Determine timeframes needed
                      ↓
                  Call Railway Python API
                  POST /analyze {ticker, position_type, timeframes}
                      ↓
              Railway Python Microservice (Compute Layer)
                  - Fetch OHLCV data (Schwab/Alpha Vantage)
                  - Calculate MTF indicators (EMA/RSI/ATR)
                  - Apply signal logic (3-Tier alignment)
                  - Apply edge filters (slope/volume/divergence)
                  - Calculate confidence score (0-5)
                  - Generate trade plan JSON
                      ↓
                  Return analysis result to n8n
                      ↓
                  n8n Decision Logic
                  - If all 3 TFs aligned → Generate alert
                  - If confidence ≥ 3 → Send Discord message
                  - Write trade idea to Supabase
                  - Log event to Supabase
                      ↓
                  Discord Channel (Alert Sent)
```

### Separation of Concerns

#### n8n Cloud Responsibilities (Orchestration)
1. **Webhook Reception**: Receive Discord webhook (ticker, position type, timeframe)
2. **Input Validation**: Verify ticker format, validate parameters
3. **Rate Limiting**: Prevent API abuse (per-user, per-channel limits)
4. **Workflow Logic**: Conditional branching based on analysis results
5. **Database Writes**: Store trade ideas, outcomes, events in Supabase
6. **Notifications**: Send formatted Discord alerts
7. **Scheduling**: Cron jobs for tracking checks, weekly learning loop
8. **Error Handling**: Retry logic, fallback workflows, user-friendly error messages

**Why n8n is GOOD at this:**
- Visual workflow editor (easy to modify logic without code deployment)
- Built-in error handling, retries, and logging
- Native integrations (Discord, Supabase, HTTP requests)
- Conditional branching (if/else, switch nodes)
- Scheduling (cron triggers for weekly analysis)

#### Railway Python Microservice Responsibilities (Compute)
1. **Market Data Fetching**: Schwab API, Alpha Vantage (fallback)
2. **Technical Indicators**: EMA, RSI, ATR, VWAP calculations (pandas-ta)
3. **MTF Analysis**: 3-Tier signal logic (Higher/Middle/Lower TF alignment)
4. **Edge Filters**: Slope, volume, divergence, pullback confirmation
5. **Confidence Scoring**: 0-5 scale based on alignment + edges
6. **Trade Plan Generation**: Stop/target calculation, rationale text
7. **News Fetching**: Finnhub company news, sentiment analysis (optional)

**Why Python is GOOD at this:**
- Powerful TA libraries (pandas-ta, TA-Lib)
- DataFrame operations (pandas for time series)
- Easy unit testing (pytest)
- Version control friendly (Git)
- Stateless function (scales horizontally)

---

## Migration Plan from Current Pure Python Implementation

### Current State (35% Complete)
- ✅ Database schema (SQLite)
- ✅ Database manager (`db_manager.py`)
- ✅ Technical indicators (`indicators.py`)
- ✅ Schwab API client (`schwab_api.py`)
- ⏳ Analysis engine (not started)
- ⏳ Discord bot (not started)
- ⏳ News API (not started)

### Migration Steps

#### Phase 1: Convert Python to Stateless Microservice
**Goal**: Transform existing Python code into a Railway-deployable API

**Tasks:**
1. Create FastAPI application (`src/main.py`)
   ```python
   from fastapi import FastAPI

   app = FastAPI()

   @app.post("/analyze")
   async def analyze_ticker(request: AnalysisRequest):
       # Call existing indicators.py logic
       # Return JSON trade plan
       pass
   ```

2. Update database layer to use **Supabase PostgreSQL** (not SQLite)
   - Replace `sqlite3` with `psycopg2` or `asyncpg`
   - Update connection string to Supabase
   - Migrate schema from SQLite to PostgreSQL

3. Refactor `schwab_api.py` for stateless operation
   - Store OAuth tokens in Supabase (not local file)
   - Token refresh logic using database-stored refresh token

4. Create `/analyze` endpoint
   - Input: `{ticker: str, position_type: str, timeframes: [str]}`
   - Output: `{signal: str, confidence: int, trade_plan: {...}}`

5. Create `/health` endpoint for monitoring

6. Write `requirements.txt` for Railway

7. Create `Procfile` for Railway deployment
   ```
   web: uvicorn src.main:app --host 0.0.0.0 --port $PORT
   ```

**Estimated Time**: 4-6 hours

#### Phase 2: Build n8n Workflow
**Goal**: Create orchestration workflow in n8n Cloud

**n8n Workflow Structure:**

1. **Discord Webhook Trigger**
   - Endpoint: `https://hyamie.app.n8n.cloud/webhook/discord-trading`
   - Parse message for `!analyze TICKER [long|short]`

2. **Input Validation Node** (JavaScript Code)
   - Regex validation for ticker symbol
   - Validate position type (long/short/both)
   - Rate limit check (query Supabase for recent requests)

3. **HTTP Request Node** → Railway Python API
   - POST to `https://[railway-url].railway.app/analyze`
   - Body: `{ticker, position_type, timeframes: ["5m", "15m", "1h"]}`
   - Timeout: 30 seconds

4. **Switch Node** (Decision Logic)
   - If `confidence >= 3` → Proceed to alert
   - If `confidence < 3` → Log only (no alert)
   - If `error` → Error handling workflow

5. **Supabase Insert Node** (Write Trade Idea)
   - Table: `trade_ideas`
   - Fields: ticker, position_type, confidence, rationale, stop, target, timestamp

6. **Discord Message Node** (Send Alert)
   - Format trade plan as Markdown embed
   - Include: ticker, bias, confidence, entry, stop, target, rationale

7. **Error Handler Workflow**
   - Log error to Supabase `system_events`
   - Send error message to Discord (user-friendly)
   - Optional: Alert admin via email

**Estimated Time**: 3-4 hours

#### Phase 3: Cron Jobs for Tracking & Learning
**Goal**: Automate monitoring and weekly optimization

**n8n Cron Workflows:**

1. **Trade Tracking Cron** (Every 15 minutes)
   - Query Supabase for open trade ideas (outcome = NULL)
   - For each open trade, fetch current price
   - Check if stop/target hit
   - If hit → Update `outcomes` table, send Discord notification

2. **Weekly Learning Loop** (Every Sunday 8 PM)
   - Query Supabase for closed trades (past 7 days)
   - Calculate metrics: win rate, avg R-multiple, Sharpe ratio
   - Send metrics to LLM (Claude/GPT-4o) for analysis
   - LLM identifies patterns (what worked, what failed)
   - Store suggestions in `modifications` table
   - Send report to Discord channel

**Estimated Time**: 4-5 hours

---

## Technical Implementation Details

### Railway Python Microservice

#### Endpoint: POST /analyze

**Request Schema:**
```json
{
  "ticker": "AAPL",
  "position_type": "long",  // "long", "short", or "both"
  "timeframes": ["5m", "15m", "1h"]  // Day trading setup
}
```

**Response Schema (Success):**
```json
{
  "status": "success",
  "ticker": "AAPL",
  "analysis": {
    "higher_tf": {
      "timeframe": "1h",
      "trend_bias": "bullish",
      "momentum_bias": "bullish",
      "ema20": 150.5,
      "ema50": 148.2,
      "rsi": 58.3,
      "long_trigger": true
    },
    "middle_tf": { /* same structure */ },
    "lower_tf": { /* same structure */ },
    "alignment": "all_bullish",  // "all_bullish", "all_bearish", "mixed"
    "confidence": 4,  // 0-5 scale
    "edges_applied": ["slope_filter", "volume_confirmation"],
    "trade_plan": {
      "position_type": "long",
      "entry": 150.8,
      "stop": 148.3,
      "target": 155.8,
      "risk_reward": 2.0,
      "rationale": "All 3 timeframes aligned bullish. EMA20 > EMA50 with strong slope (+0.15%). RSI > 55 confirming momentum. Volume 1.8x average. 3-bar breakout confirmed."
    }
  },
  "timestamp": "2025-11-12T10:30:00Z"
}
```

**Response Schema (No Signal):**
```json
{
  "status": "no_signal",
  "ticker": "AAPL",
  "reason": "Mixed timeframe alignment. Higher TF bullish, Middle TF bearish. No clear setup.",
  "confidence": 1,
  "timestamp": "2025-11-12T10:30:00Z"
}
```

**Response Schema (Error):**
```json
{
  "status": "error",
  "ticker": "AAPL",
  "error": "Schwab API rate limit exceeded. Retry in 60 seconds.",
  "timestamp": "2025-11-12T10:30:00Z"
}
```

#### Deployment Configuration (Railway)

**Environment Variables:**
```env
# Supabase
SUPABASE_URL=https://[project].supabase.co
SUPABASE_KEY=eyJ...
SUPABASE_DB_URL=postgresql://postgres:[password]@db.[project].supabase.co:5432/postgres

# Schwab API
SCHWAB_API_KEY=your_key
SCHWAB_API_SECRET=your_secret
SCHWAB_REDIRECT_URI=https://localhost:8080/callback

# Alpha Vantage (Backup)
ALPHA_VANTAGE_API_KEY=your_key

# News APIs (Optional)
FINNHUB_API_KEY=your_key
NEWS_API_KEY=your_key

# LLM (Optional, for rationale generation)
OPENAI_API_KEY=sk-...
# OR
ANTHROPIC_API_KEY=sk-ant-...
```

**Railway CLI Deployment:**
```bash
# Install Railway CLI
npm install -g @railway/cli

# Login
railway login

# Initialize project
cd discord-trading-bot
railway init

# Deploy
railway up

# Get service URL
railway domain
```

**Auto-deploy from GitHub:**
1. Connect Railway to GitHub repository
2. Configure build command: `pip install -r requirements.txt`
3. Configure start command: `uvicorn src.main:app --host 0.0.0.0 --port $PORT`
4. Every push to `main` branch → Auto-deploy

---

### Supabase Database Setup

#### Migration from SQLite to PostgreSQL

**Schema Differences:**
- SQLite: `AUTOINCREMENT` → PostgreSQL: `SERIAL` or `BIGSERIAL`
- SQLite: `DATETIME` → PostgreSQL: `TIMESTAMP WITH TIME ZONE`
- SQLite: `TEXT` → PostgreSQL: `TEXT` or `VARCHAR(n)`

**Migration SQL (run in Supabase SQL Editor):**

```sql
-- Enable UUID extension (for unique trade IDs)
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- Table: trade_ideas
CREATE TABLE trade_ideas (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    ticker VARCHAR(10) NOT NULL,
    position_type VARCHAR(10) NOT NULL,  -- 'long' or 'short'
    timeframe_set VARCHAR(50) NOT NULL,  -- e.g., '5m,15m,1h'
    confidence INTEGER NOT NULL CHECK (confidence BETWEEN 0 AND 5),
    entry_price DECIMAL(10, 2),
    stop_price DECIMAL(10, 2),
    target_price DECIMAL(10, 2),
    risk_reward DECIMAL(5, 2),
    rationale TEXT,
    edges_applied TEXT[],  -- Array of edge names
    higher_tf_data JSONB,  -- Store full TF analysis
    middle_tf_data JSONB,
    lower_tf_data JSONB,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    outcome_id UUID REFERENCES outcomes(id)
);

-- Table: outcomes
CREATE TABLE outcomes (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    trade_idea_id UUID REFERENCES trade_ideas(id),
    exit_price DECIMAL(10, 2),
    exit_reason VARCHAR(50),  -- 'target_hit', 'stop_hit', 'manual'
    pnl DECIMAL(10, 2),
    r_multiple DECIMAL(5, 2),
    closed_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Table: modifications (weekly learning loop suggestions)
CREATE TABLE modifications (
    id SERIAL PRIMARY KEY,
    week_start DATE NOT NULL,
    suggestion TEXT NOT NULL,
    reasoning TEXT,
    applied BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Table: market_data_cache
CREATE TABLE market_data_cache (
    cache_key VARCHAR(255) PRIMARY KEY,
    data JSONB NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    ttl_seconds INTEGER DEFAULT 60
);

-- Table: api_calls (for rate limit tracking)
CREATE TABLE api_calls (
    id SERIAL PRIMARY KEY,
    api_name VARCHAR(50) NOT NULL,
    endpoint VARCHAR(255),
    status_code INTEGER,
    response_time_ms INTEGER,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Table: system_events (logging)
CREATE TABLE system_events (
    id SERIAL PRIMARY KEY,
    event_type VARCHAR(50) NOT NULL,
    message TEXT,
    metadata JSONB,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Indexes
CREATE INDEX idx_trade_ideas_ticker ON trade_ideas(ticker);
CREATE INDEX idx_trade_ideas_created_at ON trade_ideas(created_at);
CREATE INDEX idx_outcomes_trade_idea_id ON outcomes(trade_idea_id);
CREATE INDEX idx_cache_created_at ON market_data_cache(created_at);
CREATE INDEX idx_api_calls_created_at ON api_calls(created_at);

-- Cleanup function (delete expired cache entries)
CREATE OR REPLACE FUNCTION cleanup_expired_cache()
RETURNS void AS $$
BEGIN
    DELETE FROM market_data_cache
    WHERE created_at + (ttl_seconds || ' seconds')::INTERVAL < NOW();
END;
$$ LANGUAGE plpgsql;
```

**Automated Cleanup (Supabase Edge Function or n8n Cron):**
```sql
-- Run daily at midnight
SELECT cleanup_expired_cache();
```

---

### n8n Workflow JSON Export

**Workflow Name**: `Discord Trading Bot - Main`

**Key Nodes:**

1. **Webhook Trigger**
   ```json
   {
     "name": "Discord Webhook",
     "type": "n8n-nodes-base.webhook",
     "parameters": {
       "path": "discord-trading",
       "responseMode": "responseNode",
       "options": {}
     }
   }
   ```

2. **Parse Command** (Code Node)
   ```javascript
   // Extract ticker and position type from Discord message
   const message = $input.item.json.content;
   const match = message.match(/!analyze ([A-Z]{1,5})(?:\s+(long|short))?/i);

   if (!match) {
     return { error: "Invalid command. Use: !analyze TICKER [long|short]" };
   }

   return {
     ticker: match[1].toUpperCase(),
     position_type: match[2] || 'both',
     timeframes: ['5m', '15m', '1h']  // Day trading setup
   };
   ```

3. **Rate Limit Check** (Supabase Query)
   ```json
   {
     "name": "Check Rate Limit",
     "type": "n8n-nodes-base.supabase",
     "parameters": {
       "operation": "get",
       "tableId": "api_calls",
       "filters": {
         "conditions": [
           {
             "keyName": "api_name",
             "condition": "equals",
             "value": "discord_command"
           },
           {
             "keyName": "created_at",
             "condition": "greater",
             "value": "={{ $now.minus({ minutes: 1 }).toISO() }}"
           }
         ]
       }
     }
   }
   ```

4. **Call Python API** (HTTP Request)
   ```json
   {
     "name": "MTF Analysis",
     "type": "n8n-nodes-base.httpRequest",
     "parameters": {
       "url": "https://[your-railway-url].railway.app/analyze",
       "method": "POST",
       "body": {
         "ticker": "={{ $json.ticker }}",
         "position_type": "={{ $json.position_type }}",
         "timeframes": "={{ $json.timeframes }}"
       },
       "timeout": 30000
     }
   }
   ```

5. **Save to Supabase** (Supabase Insert)
   ```json
   {
     "name": "Save Trade Idea",
     "type": "n8n-nodes-base.supabase",
     "parameters": {
       "operation": "insert",
       "tableId": "trade_ideas",
       "fieldsUi": {
         "ticker": "={{ $json.analysis.ticker }}",
         "position_type": "={{ $json.analysis.trade_plan.position_type }}",
         "confidence": "={{ $json.analysis.confidence }}",
         "entry_price": "={{ $json.analysis.trade_plan.entry }}",
         "stop_price": "={{ $json.analysis.trade_plan.stop }}",
         "target_price": "={{ $json.analysis.trade_plan.target }}",
         "rationale": "={{ $json.analysis.trade_plan.rationale }}"
       }
     }
   }
   ```

6. **Send Discord Alert** (Discord Message)
   ```javascript
   // Format trade plan as Discord embed
   return {
     embeds: [{
       title: `🎯 Trade Signal: ${$json.ticker}`,
       color: $json.trade_plan.position_type === 'long' ? 0x00ff00 : 0xff0000,
       fields: [
         { name: "Position", value: $json.trade_plan.position_type.toUpperCase(), inline: true },
         { name: "Confidence", value: `${$json.confidence}/5`, inline: true },
         { name: "Entry", value: `$${$json.trade_plan.entry}`, inline: true },
         { name: "Stop", value: `$${$json.trade_plan.stop}`, inline: true },
         { name: "Target", value: `$${$json.trade_plan.target}`, inline: true },
         { name: "R:R", value: `1:${$json.trade_plan.risk_reward}`, inline: true },
         { name: "Rationale", value: $json.trade_plan.rationale }
       ],
       timestamp: new Date().toISOString()
     }]
   };
   ```

---

## Comparison to Original Pure Python Plan

### What We KEEP from Original Implementation
✅ Technical indicators module (`indicators.py`)
✅ Schwab API client (`schwab_api.py`) - Just update token storage
✅ Database schema (migrate to PostgreSQL)
✅ 3-Tier MTF analysis logic
✅ Edge filters (slope, volume, divergence)
✅ Confidence scoring system

### What We CHANGE
❌ Discord bot (`discord_bot.py`) → Replaced by n8n Discord webhook
❌ SQLite database → Supabase PostgreSQL
❌ Local file token storage → Supabase table for OAuth tokens
❌ Monolithic app → Stateless FastAPI microservice
❌ Standalone Python app → n8n orchestration + Python compute

### What We ADD
✅ n8n workflow for orchestration
✅ Railway deployment configuration
✅ Supabase integration
✅ Webhook-based architecture (not polling)
✅ Visual workflow editor (easier for non-technical modifications)
✅ Separation of concerns (orchestration vs compute)

---

## Advantages of Hybrid Architecture

### 1. Cost Efficiency
- **Same incremental cost** as pure Python ($5-7/month)
- **Uses existing subscriptions** (n8n $20/month, Supabase $25/month)
- **Total cost**: $50-57/month (vs $70-77 with pure Python + wasted n8n)

### 2. Maintainability
- **n8n GUI**: Easy to modify workflow logic without code deployment
- **Python API**: Clean, testable compute logic
- **Version control**: n8n workflow JSON export + Python code in Git

### 3. Reliability
- **Railway**: ~99.9% uptime SLA
- **n8n Cloud**: Managed service, no server maintenance
- **Supabase**: Managed PostgreSQL, automatic backups

### 4. Scalability
- **Stateless Python API**: Horizontal scaling (Railway auto-scales)
- **n8n**: Handles 1000s of webhooks/day on Starter plan
- **Supabase**: Generous free tier, scales to millions of rows

### 5. Debugging
- **n8n execution logs**: Visual workflow debugging
- **Railway logs**: Real-time Python logs
- **Supabase**: SQL query console for data inspection

### 6. Flexibility
- **Easy to add new features**:
  - New Discord commands → Add n8n workflow branch
  - New indicators → Update Python `indicators.py`
  - New data sources → Add fallback API in Python
  - New notifications → Add n8n Discord/email node

---

## Disadvantages & Mitigation

### Disadvantage 1: Increased Complexity
**Problem**: Two systems to manage (n8n + Railway)

**Mitigation**:
- Clear separation of concerns (document in KB)
- Standardized API contract (OpenAPI spec for `/analyze` endpoint)
- Health checks in both systems (n8n cron → Railway `/health`)

### Disadvantage 2: Network Latency
**Problem**: n8n → Railway API call adds network round-trip (~100-200ms)

**Mitigation**:
- Not critical for trading signals (analysis takes seconds anyway)
- Timeout set to 30 seconds (plenty of buffer)
- Railway deploys to US region (same as n8n Cloud)

### Disadvantage 3: Dual Deployment
**Problem**: Must deploy changes to both n8n and Railway

**Mitigation**:
- Railway auto-deploys from GitHub (push to main → deploy)
- n8n workflow exported to Git (version controlled)
- Changes are usually in ONE system (either workflow OR compute)

---

## Implementation Timeline

### Phase 1: Railway Microservice (Week 1)
- Day 1-2: Refactor Python to FastAPI, Supabase integration
- Day 3: Deploy to Railway, test `/analyze` endpoint
- Day 4: Schwab OAuth token storage in Supabase
- Day 5: Add news API integration (optional)

### Phase 2: n8n Workflow (Week 2)
- Day 1: Build main workflow (Discord webhook → Python API → Supabase)
- Day 2: Add error handling, rate limiting
- Day 3: Tracking cron (15-min checks for stop/target hits)
- Day 4: Weekly learning loop cron
- Day 5: Testing end-to-end

### Phase 3: Refinement & Testing (Week 3)
- Day 1-2: Edge filter validation (test with historical data)
- Day 3: Confidence scoring calibration
- Day 4-5: Paper trading mode (simulated trades for 1 week)

**Total**: 3 weeks to production-ready system

---

## Migration from Current Code

### Step 1: Database Migration
```bash
# Export current SQLite schema
sqlite3 database.db .schema > schema_sqlite.sql

# Convert to PostgreSQL (manual adjustments)
# Run migration SQL in Supabase SQL Editor
```

### Step 2: Refactor Database Manager
```python
# Before (SQLite)
import sqlite3
conn = sqlite3.connect('database.db')

# After (Supabase PostgreSQL)
import psycopg2
conn = psycopg2.connect(os.getenv('SUPABASE_DB_URL'))
```

### Step 3: Create FastAPI App
```python
# src/main.py
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from src.utils.indicators import calculate_mtf_analysis

app = FastAPI(title="Discord Trading Bot API")

class AnalysisRequest(BaseModel):
    ticker: str
    position_type: str
    timeframes: list[str]

@app.post("/analyze")
async def analyze(request: AnalysisRequest):
    try:
        result = calculate_mtf_analysis(
            ticker=request.ticker,
            position_type=request.position_type,
            timeframes=request.timeframes
        )
        return {"status": "success", "analysis": result}
    except Exception as e:
        return {"status": "error", "error": str(e)}

@app.get("/health")
async def health():
    return {"status": "ok", "timestamp": datetime.now().isoformat()}
```

### Step 4: Deploy to Railway
```bash
# Install Railway CLI
npm install -g @railway/cli

# Login and init
railway login
railway init

# Set environment variables
railway variables set SUPABASE_URL=...
railway variables set SCHWAB_API_KEY=...

# Deploy
railway up

# Get URL
railway domain
# Example: https://discord-trading-bot.railway.app
```

### Step 5: Build n8n Workflow
1. Import workflow JSON (provided above)
2. Update Railway URL in HTTP Request node
3. Configure Supabase connection (credentials from Supabase dashboard)
4. Configure Discord webhook URL
5. Test workflow execution

---

## Next Steps (Immediate Actions)

### 1. Confirm Architecture Approval
**Question for user**: Do you approve the hybrid architecture (n8n + Railway Python)?

**If YES**:
- Proceed with refactoring to FastAPI
- Set up Railway account
- Migrate database to Supabase

**If NO**:
- Clarify concerns (cost, complexity, etc.)
- Provide alternative recommendations

### 2. Gather Missing Information
- **Supabase project URL**: (e.g., `https://abc123.supabase.co`)
- **Supabase API key**: (from Supabase dashboard → Settings → API)
- **n8n Cloud URL**: Confirmed as `https://hyamie.app.n8n.cloud/`
- **Discord Bot Token**: (from Discord Developer Portal)
- **Schwab API credentials**: Already approved, need keys

### 3. Create Railway Account
- Sign up at railway.app
- Connect GitHub account (for auto-deploy)
- Estimate cost: $5-7/month for hobby plan

### 4. Update Project Documentation
- Update `README.md` with hybrid architecture
- Create deployment guide (`DEPLOYMENT.md`)
- Document API contract (`API_SPEC.md`)

---

## Questions for User

1. **Cost Approval**: Are you comfortable with $5-7/month for Railway? (Same as original recommendation)

2. **Supabase Plan**: What Supabase plan are you on? (Need to confirm PostgreSQL access)

3. **n8n Plan**: What n8n plan are you on? (Starter $20/month has webhook limits)

4. **PC 24/7 Status**: Is your PC already running 24/7 for other reasons? (Affects local Docker cost analysis)

5. **Priority**: Do you want to proceed with hybrid architecture, or prefer original pure Python?

6. **Timeline**: How urgent is deployment? (Affects whether we do phased migration or full rewrite)

---

## Conclusion

The hybrid architecture (n8n Cloud + Railway Python) is the BEST option given the constraints:

✅ **Same incremental cost** as pure Python ($5-7/month)
✅ **Uses existing subscriptions** (n8n + Supabase)
✅ **Cloud reliability** (no local PC dependencies)
✅ **Clean separation** (orchestration vs compute)
✅ **Easier maintenance** (visual workflow + testable Python)

**Recommendation**: Approve hybrid architecture and proceed with Phase 1 (Railway microservice).
