# Discord Trading Bot - Architecture Review & Optimization Plan

**Date**: 2025-11-12
**Reviewer**: Donnie (Meta-Orchestrator)
**Current Status**: 35% Complete (In Development)
**Critical Finding**: Project misconfigured as "ready-to-deploy" - needs correction

---

## Executive Summary

After comprehensive analysis using Sequential Thinking MCP, I recommend **continuing with pure Python implementation** rather than switching to n8n or hybrid architecture. The project has solid foundations (35%+ complete) and the complexity of the Trading Workflow V2 specification is better suited to Python than visual workflows.

**Key Recommendations**:
1. ✅ **Continue Pure Python** - Don't switch to n8n/hybrid
2. 🔧 **Fix Project Config** - Update status from "ready-to-deploy" to "in-development"
3. 🗄️ **Keep SQLite** - Sufficient for single-user bot, can scale later
4. 🚀 **Deploy to Railway.app** - Free tier, easy Docker deployment
5. 📊 **Leverage MCPs** - Memory for learning, Docker for deployment, Axiom for monitoring
6. ⏱️ **Timeline: 3-4 weeks to MVP**

---

## 1. Architecture Recommendation

### ✅ RECOMMENDED: Pure Python Implementation

**Rationale**:
- **35% already complete** with solid foundations:
  - ✅ Database schema (SQLite with trade_ideas, outcomes, modifications)
  - ✅ Database manager (full ORM-like interface)
  - ✅ Technical indicators (EMA, RSI, ATR, VWAP with slope/divergence detection)
  - ✅ Schwab API client (OAuth 2.0, rate limiting, token refresh)
  - ✅ News API integration (started)
  - ✅ Analysis engine (started)

- **Complex algorithms fit Python better**:
  - 3-Tier Multi-Timeframe analysis (Higher/Middle/Lower TF)
  - Edge detection (Slope Filter, Volume Confirmation, Divergence, Pullback)
  - Confidence scoring (0-5 scale with multiple factors)
  - LLM integration for trade rationale generation
  - Weekly self-improvement loop

- **Development velocity**:
  - Only 12-15 hours from current state to MVP
  - All hard parts already done (indicators, API client, database)
  - Missing parts are straightforward (Discord bot, testing)

- **Cost efficiency**:
  - Deployment: $0-7/month (Railway/Render free tier)
  - vs. n8n Cloud: $20/month + hosting for Python microservice

### ❌ NOT RECOMMENDED: n8n-Based Architecture

**Why Not**:
- Existing n8n workflow (`n8nworkflow.txt`) is too simplistic:
  - Uses Finnhub (not Schwab) - data source mismatch
  - Simple ATR calculation only - no 3-Tier MTF logic
  - No edge detection, no confidence scoring
  - No learning loop, no LLM integration
  - Would require **complete rewrite** to match Trading Workflow V2 spec

- Complex indicator calculations awkward in JavaScript function nodes
- Multi-agent orchestration becomes messy with many nodes
- Would waste 35% of Python work already completed

### ❌ NOT RECOMMENDED: Hybrid (n8n + Python Microservice)

**Why Not**:
- Adds unnecessary complexity for single-user bot
- Requires maintaining two systems (n8n workflows + Python service)
- Higher hosting costs ($20 n8n + $7 Python = $27/month)
- Network latency between n8n Cloud and Python service
- Overkill for current use case (one user, one Discord server)

**When Hybrid Makes Sense** (Future):
- Multi-user scaling (100+ concurrent users)
- Multiple integration points (Discord + Slack + Telegram + web dashboard)
- Non-technical users need to modify workflows
- Complex orchestration with many external services

---

## 2. Revised Implementation Plan

### Phase 1: Core Development (Current - 1-2 weeks)

**Remaining Components** (20 hours total):

#### 1.1 Discord Bot Integration (3-4 hours)
**Status**: Not started
**File**: `src/bot/discord_bot.py`
**Requirements**:
- Discord.py library integration
- Command parsing: `!analyze TICKER [day|swing|both]`
- Message validation and error handling
- Response formatting (Markdown with confidence scores)
- Error notifications to user

**Implementation**:
```python
import discord
from discord.ext import commands
from src.agents.analysis_engine import AnalysisEngine

bot = commands.Bot(command_prefix='!')

@bot.command()
async def analyze(ctx, ticker: str, trade_type: str = "both"):
    """Generate trade analysis for a ticker"""
    await ctx.send(f"🔍 Analyzing {ticker.upper()}...")

    engine = AnalysisEngine()
    result = await engine.analyze(ticker, trade_type)

    await ctx.send(format_trade_plan(result))

@bot.command()
async def track(ctx, trade_id: str, outcome: str, pl: float, exit_price: float):
    """Log trade outcome"""
    # Update database with outcome
    pass
```

**Dependencies**:
- Discord bot token (user needs to create at discord.com/developers)
- Discord channel ID for posting

#### 1.2 Analysis Engine Completion (5-6 hours)
**Status**: Partially complete (`src/agents/analysis_engine.py` exists)
**Requirements**:
- Implement 3-Tier MTF signal logic
  - Higher TF: Trend bias (EMA20 vs EMA50, slope filter)
  - Middle TF: Momentum bias (RSI thresholds, pullback confirmation)
  - Lower TF: Entry triggers (3-bar breakout + EMA20 confirmation)
- Apply all edge filters:
  - Slope Filter: (EMA20_current - EMA20_5bars) / EMA20_5bars > 0.1%
  - Volume Confirmation: Current volume > 1.5x avg volume
  - Volatility Filter: Candle range > 1.25x ATR
  - Pullback Confirmation: Price > VWAP AND 45 < RSI < 65
  - Divergence Detection: Price vs RSI divergence
- Confidence scoring (0-5 scale)
- LLM integration for rationale generation (OpenAI or Anthropic)
- News sentiment incorporation (+1 confidence if aligned)
- Dynamic R:R adjustment (1.5R for counter-trend)

**LLM Prompt Template**:
```python
RATIONALE_PROMPT = """
Generate a 2-3 sentence trade rationale for this setup:

Ticker: {ticker}
Direction: {direction}
Timeframe: {trade_type}

Technical Setup:
- Trend Bias: {trend_bias} (EMA20={ema20}, EMA50={ema50})
- Momentum: RSI={rsi}
- Entry Trigger: {trigger_reason}

Edges Applied: {edges_list}

Recent News Sentiment: {news_sentiment}

Provide concise rationale explaining WHY this trade has conviction.
Address key risks to watch.
"""
```

#### 1.3 Data Fetcher Agent (2-3 hours)
**Status**: Components exist but not orchestrated
**File**: `src/agents/data_fetcher.py`
**Requirements**:
- Multi-timeframe batch fetching from Schwab API
  - Day Trade: 1h, 15m, 5m
  - Swing Trade: Weekly, Daily, 4h
- SPY market bias data (same timeframes)
- Cache integration (use existing db_manager.get_cached_data)
- Fallback to Alpha Vantage if Schwab rate limited
- Error recovery with retry logic

**Integration**:
```python
from src.utils.schwab_api import SchwabClient
from src.database.db_manager import DatabaseManager

class DataFetcherAgent:
    def __init__(self):
        self.schwab = SchwabClient()
        self.db = DatabaseManager()

    async def fetch_all_timeframes(self, ticker, trade_type):
        """Fetch all required timeframes with caching"""
        cache_key = f"{ticker}_{trade_type}_{datetime.now().date()}"
        cached = self.db.get_cached_data(cache_key)

        if cached:
            return cached

        # Fetch from Schwab
        timeframes = self.schwab.get_multiple_timeframes(ticker, configs)

        # Cache for 60 seconds
        self.db.cache_data(cache_key, timeframes, ttl=60)
        return timeframes
```

#### 1.4 Tracking System (3-4 hours)
**Status**: Database ready, agent not implemented
**File**: `src/agents/tracking_agent.py`
**Requirements**:
- Manual tracking command: `!track TRADE_ID win/loss P/L EXIT_PRICE NOTES`
- Automated price monitoring (15-min cron job)
  - Check if stop or target hit
  - Update outcomes table automatically
- P/L calculation and R-multiple tracking
- Discord notification when trade closes

**Implementation**:
```python
import schedule
import time

class TrackingAgent:
    def __init__(self, db_manager, schwab_client):
        self.db = db_manager
        self.schwab = schwab_client

    def check_open_trades(self):
        """Cron job - check if any trades hit stop/target"""
        open_trades = self.db.get_open_trades()

        for trade in open_trades:
            current_price = self.schwab.get_quote(trade['ticker'])['c']

            if trade['direction'] == 'long':
                if current_price <= trade['stop']:
                    self.close_trade(trade, 'stop_hit', current_price)
                elif current_price >= trade['target']:
                    self.close_trade(trade, 'target_hit', current_price)

# Schedule every 15 minutes during market hours
schedule.every(15).minutes.do(tracking_agent.check_open_trades)
```

#### 1.5 Main Application (2 hours)
**Status**: Not started
**File**: `src/main.py`
**Requirements**:
- Application initialization
- Discord bot startup
- Background tasks (caching cleanup, tracking checks)
- Error handling and logging setup
- Graceful shutdown

**Structure**:
```python
import asyncio
from src.bot.discord_bot import bot
from src.agents.tracking_agent import TrackingAgent
from src.database.db_manager import DatabaseManager

async def main():
    # Initialize database
    db = DatabaseManager()
    db.initialize()

    # Start background tasks
    asyncio.create_task(tracking_agent.monitor_loop())

    # Start Discord bot
    await bot.start(os.getenv('DISCORD_BOT_TOKEN'))

if __name__ == "__main__":
    asyncio.run(main())
```

---

### Phase 2: Testing (1 week)

#### 2.1 Unit Tests
**Framework**: pytest (already in requirements.txt)

**Test Coverage**:
- ✅ Technical indicators (src/utils/indicators.py)
  - EMA calculation accuracy
  - RSI calculation vs known values
  - ATR calculation
  - Slope detection
  - Divergence detection

- ✅ Database operations (src/database/db_manager.py)
  - Insert trade ideas
  - Update outcomes
  - Performance metrics calculation
  - Cache operations

- ✅ Schwab API client (src/utils/schwab_api.py)
  - Mock OAuth flow
  - Mock price history responses
  - Rate limiting behavior
  - Token refresh logic

**Example Test**:
```python
# tests/test_indicators.py
import pytest
from src.utils.indicators import calculate_ema, calculate_rsi

def test_ema_calculation():
    closes = [100, 102, 101, 103, 105, 104, 106, 108]
    ema20 = calculate_ema(closes, period=5)

    # Verify against known calculation
    assert len(ema20) == len(closes)
    assert ema20[-1] > closes[-5]  # EMA should be responsive

def test_rsi_overbought():
    # Rising prices should produce high RSI
    closes = [100 + i for i in range(20)]
    rsi = calculate_rsi(closes, period=14)

    assert rsi[-1] > 70  # Should be overbought
```

#### 2.2 Integration Tests
- End-to-end Discord command flow
- Mock Schwab API responses
- Verify trade plan generation
- Database persistence

#### 2.3 Paper Trading Validation
- Run bot in test mode for 1-2 weeks
- Compare signals to real market outcomes
- Validate confidence scoring accuracy
- Test learning loop

---

### Phase 3: Deployment (3-5 days)

#### 3.1 Containerization (1 day)
**Use Docker MCP** ✅

**Dockerfile**:
```dockerfile
FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY src/ ./src/
COPY .env .env

CMD ["python", "-m", "src.main"]
```

**Docker Compose** (optional for local dev):
```yaml
version: '3.8'
services:
  discord-bot:
    build: .
    env_file: .env
    volumes:
      - ./data:/app/data
    restart: unless-stopped
```

#### 3.2 Deployment Platform Selection

**Option A: Railway.app** ✅ RECOMMENDED
- Free tier: 500 hours/month (~16 hours/day)
- Easy Docker deployment
- PostgreSQL add-on available (if needed)
- Automatic HTTPS
- Simple CI/CD from GitHub
- Cost: $0 (free tier) or $5/month (Pro plan for 24/7)

**Setup**:
```bash
# Install Railway CLI
npm i -g @railway/cli

# Login and deploy
railway login
railway init
railway up
```

**Option B: Render.com**
- Free tier: 750 hours/month
- Docker support
- Automatic deploys from GitHub
- Cost: $0 (free tier) or $7/month (Starter)

**Option C: Fly.io**
- Free tier: 3 shared-cpu-1x VMs
- Global deployment
- Cost: $0 (free tier)

#### 3.3 Environment Configuration

**Required Secrets** (store in platform):
- `DISCORD_BOT_TOKEN` - Discord bot credentials
- `SCHWAB_API_KEY` - Schwab developer key
- `SCHWAB_API_SECRET` - Schwab secret
- `SCHWAB_REDIRECT_URI` - OAuth redirect URL
- `FINNHUB_API_KEY` - News source
- `NEWSAPI_KEY` - Secondary news source
- `OPENAI_API_KEY` or `ANTHROPIC_API_KEY` - LLM for rationale
- `DATABASE_PATH` - SQLite file location

#### 3.4 Monitoring Setup (Use Axiom MCP ✅)

**Axiom Integration**:
- Stream logs to Axiom for analysis
- Alert on API errors
- Track trade generation rate
- Monitor Schwab API quota usage

**Setup**:
```python
import axiom

logger = axiom.Logger(
    dataset="discord-trading-bot",
    token=os.getenv("AXIOM_TOKEN")
)

logger.info("Trade generated", extra={
    "ticker": ticker,
    "confidence": confidence,
    "trade_type": trade_type
})
```

---

### Phase 4: Learning Loop (Post-Deployment)

#### 4.1 Weekly Optimization (Use Memory MCP ✅)

**Schedule**: Every Sunday at 00:00 UTC

**Process**:
1. Query closed trades from past week
2. Calculate metrics:
   - Win rate (%)
   - Average R-multiple
   - Sharpe ratio (simplified)
   - Max drawdown
3. Feed to LLM for pattern analysis
4. Store insights in Memory MCP
5. Suggest framework modifications

**LLM Prompt**:
```python
OPTIMIZATION_PROMPT = """
Analyze these trading outcomes from the past week:

{outcomes_json}

Metrics:
- Win Rate: {win_rate}%
- Avg R-Multiple: {avg_r}
- Max Drawdown: {max_dd}%
- Sharpe Ratio: {sharpe}

Identify patterns:
1. Which edges had highest win rate?
2. Which timeframe setups performed best?
3. What conditions led to losses?

Suggest 1-3 specific framework modifications with expected impact.
Example: "Increase RSI bullish threshold from 55 to 60 for Middle TF - Expected +5% win rate"

Output JSON: {
  "patterns": ["pattern1", "pattern2"],
  "suggested_changes": ["change1", "change2"]
}
"""
```

**Memory Storage**:
```python
# Store weekly insights in Memory MCP
mcp__memory__create_memory({
  "messages": [{
    "role": "user",
    "content": f"Week {week_number} optimization: Win rate {win_rate}%, identified pattern: {pattern}"
  }]
})

# Later retrieve for context
memories = mcp__memory__search_memory({
  "query": "high win rate patterns"
})
```

#### 4.2 Framework Version Control (Use GitHub MCP ✅)

**Process**:
1. Weekly learning loop suggests changes
2. Update framework parameters in code
3. Create Git commit with rationale
4. Tag with version (e.g., `v1.2.0-opt-week42`)

**Automated Commits** (via GitHub MCP):
```python
# After optimization
mcp__github__create_or_update_file({
  "owner": "yourusername",
  "repo": "discord-trading-bot",
  "path": "src/config/framework_params.json",
  "content": json.dumps(updated_params, indent=2),
  "message": f"chore(optimization): Week {week} - RSI threshold 55→60 (+5% WR)",
  "branch": "main"
})
```

---

## 3. MCP Profile Strategy

### Current Status - NEEDS FIXING ❌

**Problem**:
- `.project-mcp.json` says `status: "ready-to-deploy"` but project is only 35% complete
- `currentPhase: "deployment"` is incorrect - should be "development"
- `defaultProfile: "webapp"` but project is Python-based, not n8n-based

### Corrected Configuration

```json
{
  "project": {
    "name": "Discord Trading Bot",
    "type": "algorithmic-trading",
    "description": "Python-based 3-Tier MTF trading signals bot for Discord",
    "techStack": ["Python", "Discord.py", "Schwab API", "SQLite", "OpenAI/Anthropic"],
    "repository": null,
    "status": "in-development"
  },
  "mcp": {
    "defaultProfile": "donnie",
    "requiredMcps": [
      "git",
      "github",
      "filesystem",
      "memory",
      "sequential-thinking",
      "docker",
      "axiom"
    ],
    "phaseProfiles": {
      "planning": {
        "profile": "core",
        "mcps": ["filesystem", "git", "github"],
        "reason": "Lightweight profile for architecture planning"
      },
      "development": {
        "profile": "donnie",
        "mcps": ["git", "github", "filesystem", "memory", "sequential-thinking"],
        "reason": "Python development with learning support"
      },
      "testing": {
        "profile": "donnie",
        "mcps": ["git", "github", "filesystem"],
        "reason": "Unit and integration testing"
      },
      "deployment": {
        "profile": "donnie",
        "mcps": ["docker", "github", "axiom", "git"],
        "reason": "Containerization and monitoring setup"
      }
    }
  },
  "context": {
    "workingDirectory": "C:\\claudeagents\\projects\\discord-trading-bot",
    "keyFiles": [
      "src/database/db_manager.py",
      "src/utils/indicators.py",
      "src/utils/schwab_api.py",
      "Trading Workflow V2.md",
      "requirements.txt"
    ],
    "currentPhase": "development"
  }
}
```

### MCP Usage per Phase

#### Phase 1: Development (Current)
**Profile**: donnie ✅ (already loaded)

**MCPs**:
- `git` / `github` - Version control
- `filesystem` - File operations
- `memory` - Store design decisions, patterns
- `sequential-thinking` - Algorithm debugging, trade confidence scoring

**Example Memory Usage**:
```javascript
// Store architecture decision
mcp__memory__create_memory({
  messages: [{
    role: "user",
    content: "Discord Trading Bot: Decided on pure Python architecture over hybrid n8n. Reason: Complex 3-Tier MTF logic better suited to code. Cost: $0-7/month vs $27/month hybrid."
  }]
})
```

**Example Sequential Thinking Usage**:
```javascript
// Debug confidence scoring logic
mcp__sequential-thinking__sequentialthinking({
  thought: "Analyzing why AAPL trade got confidence 3 instead of expected 4. Checking: Trend Bias (✓ Bullish), Momentum (✓ RSI 58), Entry Trigger (✓ 3-bar breakout), Slope Filter (✗ 0.08% < 0.1% threshold). Found issue: Slope filter too strict for low volatility stocks.",
  thoughtNumber: 1,
  totalThoughts: 3,
  nextThoughtNeeded: true
})
```

#### Phase 2: Testing
**Profile**: donnie (no change needed)

**MCPs**:
- `git` / `github` - Track test results
- `filesystem` - Read test files
- Standard Python testing tools (pytest)

#### Phase 3: Deployment
**Profile**: donnie ✅ (has Docker and Axiom)

**MCPs**:
- `docker` - Containerization
- `github` - CI/CD pipeline
- `axiom` - Monitoring and logging
- `git` - Deployment version tagging

**Docker MCP Usage**:
```javascript
// Build and push container
mcp__docker__run_command({
  command: "docker build -t discord-trading-bot:v1.0.0 .",
  service: "discord-bot"
})

mcp__docker__run_command({
  command: "docker push registry.railway.app/discord-trading-bot:v1.0.0"
})
```

**Axiom MCP Usage**:
(Note: Axiom MCP integration would be via Python SDK in application code)

---

## 4. Component Delegation Plan

### Decision Matrix

Per §0B Delegation Decision Matrix:

| Component | Complexity | Delegate? | Agent | Rationale |
|-----------|------------|-----------|-------|-----------|
| Discord Bot | Simple | ❌ No | Execute directly | discord.py well-documented, straightforward |
| Analysis Engine | Complex | ❌ No | Execute directly | Already 35% done, core algorithm work |
| Data Fetcher | Simple | ❌ No | Execute directly | API calls + caching, standard pattern |
| Tracking Agent | Simple | ❌ No | Execute directly | Cron job + database updates |
| Testing Strategy | Medium | ⚠️ Optional | general-purpose | Could delegate if comprehensive test plan needed |
| Deployment Research | Medium | ⚠️ Optional | webapp-dev | Could delegate for detailed platform comparison |

### Delegation Recommendations

**Minimal Delegation Approach** ✅ RECOMMENDED:
- Execute all core components directly
- Only delegate if user wants deep research on specific topics
- Faster delivery (avoid coordination overhead)

**If Delegation Desired**:

**Option 1: Deployment Strategy Research**
```
Delegate to: webapp-dev
Task: "Research deployment platforms for Python Discord bots with these requirements:
- 24/7 uptime needed
- Docker support
- Budget: $0-10/month
- Easy CI/CD from GitHub
- SQLite file persistence

Compare: Railway.app vs Render.com vs Fly.io vs AWS Lambda

Create deployment plan in doc/research/deployment-strategy.md"
```

**Option 2: Testing Strategy Plan**
```
Delegate to: general-purpose
Task: "Research testing strategies for algorithmic trading bots with these components:
- Technical indicator calculations (EMA, RSI, ATR)
- Multi-timeframe signal logic
- API mocking (Schwab, Discord)
- Database operations (SQLite)
- LLM integration testing

Create comprehensive test plan with pytest examples in doc/research/testing-strategy.md"
```

---

## 5. Database Strategy

### ✅ KEEP SQLite (Recommended)

**Rationale**:
- Already implemented with complete schema
- Perfect for single-user bot (not multi-tenant)
- Portable (single file, easy backups)
- Zero hosting cost
- Sufficient performance (<1000 trades/month)
- Can migrate to PostgreSQL later if needed

**When to Migrate to PostgreSQL**:
- Multi-user deployment (10+ users)
- >10,000 trades/month
- Need for complex analytics queries
- Concurrent write requirements

**SQLite Optimizations**:
```python
# Enable WAL mode for better concurrency
db.execute("PRAGMA journal_mode=WAL")

# Increase cache size
db.execute("PRAGMA cache_size=-64000")  # 64MB

# Enable foreign keys
db.execute("PRAGMA foreign_keys=ON")
```

### Database Backup Strategy

**Automated Backups** (via cron):
```python
import shutil
import datetime

def backup_database():
    """Daily backup at 00:00 UTC"""
    timestamp = datetime.datetime.now().strftime("%Y%m%d")
    src = "data/trading_bot.db"
    dst = f"backups/trading_bot_{timestamp}.db"
    shutil.copy2(src, dst)

    # Keep only last 30 days
    cleanup_old_backups(days=30)

# Schedule
schedule.every().day.at("00:00").do(backup_database)
```

**Cloud Backup** (optional):
- Upload daily backups to GitHub releases
- Or use GitHub MCP to commit to backup branch

---

## 6. Timeline & Milestones

### Realistic Timeline: 3-4 Weeks to MVP

#### Week 1: Core Development Part 1
**Days 1-3** (10 hours):
- ✅ Complete Discord bot integration (3-4 hours)
- ✅ Complete data fetcher agent (2-3 hours)
- ✅ Complete tracking system foundation (3-4 hours)

**Days 4-7** (10 hours):
- ✅ Complete analysis engine (5-6 hours)
- ✅ Build main.py orchestrator (2 hours)
- ✅ Integration testing (3 hours)

**Milestone**: Can analyze tickers end-to-end via Discord

#### Week 2: Testing & Refinement
**Days 8-10** (8 hours):
- ✅ Write unit tests (4 hours)
- ✅ Mock API integration tests (2 hours)
- ✅ Fix bugs discovered (2 hours)

**Days 11-14** (8 hours):
- ✅ Paper trading validation (4 hours)
- ✅ Confidence scoring tuning (2 hours)
- ✅ Documentation updates (2 hours)

**Milestone**: Test suite passing, paper trades running

#### Week 3: Deployment
**Days 15-17** (6 hours):
- ✅ Dockerization (2 hours)
- ✅ Railway.app deployment (2 hours)
- ✅ Environment configuration (1 hour)
- ✅ Monitoring setup (Axiom MCP) (1 hour)

**Days 18-21** (4 hours):
- ✅ Production testing (2 hours)
- ✅ Bug fixes (2 hours)

**Milestone**: Bot live on Discord, generating signals

#### Week 4: Learning Loop & Optimization
**Days 22-24** (4 hours):
- ✅ Implement weekly cron job (2 hours)
- ✅ Memory MCP integration (1 hour)
- ✅ Test optimization flow (1 hour)

**Days 25-28** (2 hours):
- ✅ First optimization cycle (manual)
- ✅ Documentation finalization

**Milestone**: Self-improving bot fully operational

### Total Development Time
- **Core development**: 20 hours
- **Testing**: 16 hours
- **Deployment**: 10 hours
- **Learning loop**: 6 hours
- **Total**: ~52 hours over 3-4 weeks

---

## 7. Critical Fixes Required

### Fix 1: Update .project-mcp.json ❌ CRITICAL

**Current (Incorrect)**:
```json
{
  "status": "ready-to-deploy",
  "currentPhase": "deployment",
  "defaultProfile": "webapp",
  "type": "workflow-automation"
}
```

**Corrected**:
```json
{
  "status": "in-development",
  "currentPhase": "development",
  "defaultProfile": "donnie",
  "type": "algorithmic-trading"
}
```

### Fix 2: Create doc/task/context.md ❌ CRITICAL

Per §0A Context Management Protocol, this file is **MANDATORY** and missing.

**Create**:
```markdown
# Discord Trading Bot - Project Context

**Last Updated**: 2025-11-12
**Status**: In Development (35% Complete)
**Current Goal**: Complete core components to MVP (20 hours remaining)

## Architecture Overview
- **Type**: Python-based algorithmic trading bot
- **Deployment**: Railway.app (free tier → $5/month)
- **Database**: SQLite (single-user sufficient)
- **APIs**: Schwab (market data), Finnhub/NewsAPI (news), OpenAI/Anthropic (LLM)

## Recent Changes
**2025-11-12**: Architecture review completed
- Decision: Pure Python (not n8n/hybrid)
- Rationale: 35% complete, complex algorithms fit Python better
- Next: Complete Discord bot integration (3-4 hours)

**2025-11-09**: Initial implementation
- Created database schema (trade_ideas, outcomes, modifications)
- Built technical indicators module (EMA, RSI, ATR, VWAP)
- Implemented Schwab API client with OAuth 2.0

## Current State
**✅ Completed (35%)**:
- Database layer (schema + manager)
- Technical indicators (with slope/divergence detection)
- Schwab API client (OAuth, rate limiting)
- News API integration (started)
- Analysis engine (started)

**🚧 In Progress**:
- Analysis engine (3-Tier MTF logic)

**📋 Pending (65%)**:
- Discord bot integration
- Data fetcher agent
- Tracking system
- Main orchestrator
- Testing suite
- Deployment

## Known Issues
- .project-mcp.json status incorrect ("ready-to-deploy" should be "in-development")
- No doc/task/context.md (this file fixes that)
- Schwab OAuth flow not tested (requires user to generate auth code)

## Next Steps
1. Fix .project-mcp.json configuration
2. Complete Discord bot integration (3-4 hours)
3. Complete analysis engine (5-6 hours)
4. Build data fetcher agent (2-3 hours)
5. Implement tracking system (3-4 hours)
6. Create main.py orchestrator (2 hours)

## Key Decisions
**Decision**: Pure Python architecture
**When**: 2025-11-12
**Why**: 35% complete with solid foundation, complex 3-Tier MTF logic better in code
**Alternatives Considered**: n8n-based (too simple), hybrid (unnecessary complexity)
**Impact**: Faster to MVP (12-15 hours vs weeks), lower cost ($0-7 vs $27/month)

**Decision**: SQLite database
**When**: 2025-11-09
**Why**: Single-user bot, portable, zero cost
**Alternatives Considered**: PostgreSQL (overkill for now)
**Impact**: Can migrate later if multi-user scaling needed

## Team Preferences
- Prefer code over visual workflows for complex logic
- Type hints and docstrings for all functions
- pytest for testing
- Docker for deployment
- Conventional commits

## Dependencies
**APIs Required**:
- Discord bot token (user needs to create)
- Schwab API key + secret (user has approved access ✅)
- Finnhub API key
- NewsAPI key
- OpenAI or Anthropic API key

**Python Packages**:
See requirements.txt (discord.py, pandas, TA-Lib, openai, anthropic, etc.)

## Notes for Agents
- This is NOT a simple quote bot - it's a sophisticated algorithmic trading system
- Trading Workflow V2.md is the authoritative spec (31KB, very detailed)
- Focus on accuracy over speed (trading signals need precision)
- User has Schwab API approval (not in sandbox mode)
- Single-user deployment (not multi-tenant)
```

### Fix 3: Update IMPLEMENTATION_PROGRESS.md

**Add to "Completed Components" section**:
```markdown
#### 7. News API Integration (Partial) ✓
`src/utils/news_api.py` - Started implementation:
- Finnhub client structure
- NewsAPI client structure
- News aggregation logic

#### 8. Analysis Engine (Partial) ✓
`src/agents/analysis_engine.py` - Started implementation:
- 3-Tier MTF framework structure
- Edge detection placeholders
- Confidence scoring logic
```

---

## 8. Risk Assessment & Mitigation

### Risk 1: Schwab API OAuth Complexity
**Risk Level**: Medium
**Impact**: Bot can't fetch market data without valid tokens

**Mitigation**:
1. Create helper script for initial OAuth flow
2. Store refresh tokens securely in SQLite or environment
3. Implement token auto-refresh 5 minutes before expiration
4. Add fallback to Alpha Vantage if Schwab unavailable

**Helper Script** (`scripts/schwab_oauth.py`):
```python
from src.utils.schwab_api import SchwabClient

client = SchwabClient()

print("1. Go to this URL:")
print(client.get_authorization_url())

auth_code = input("\n2. Paste authorization code: ")

if client.authenticate(auth_code):
    print("✅ Authenticated! Refresh token saved.")
else:
    print("❌ Authentication failed.")
```

### Risk 2: LLM API Costs
**Risk Level**: Low
**Impact**: Unexpected OpenAI/Anthropic bills

**Mitigation**:
1. Set API rate limits (e.g., max 100 requests/day)
2. Cache LLM responses for identical inputs
3. Use cheaper models for non-critical tasks (gpt-3.5-turbo for news summarization)
4. Monitor costs with Axiom (alert if >$10/day)

**Cost Estimation**:
- Per analysis: ~2000 tokens (input) + 500 tokens (output) = 2500 tokens
- GPT-4o: $0.0025 per 1K input tokens, $0.010 per 1K output tokens
- Per analysis cost: (2 × $0.0025) + (0.5 × $0.010) = $0.01
- 50 analyses/day × 30 days = 1500 × $0.01 = **$15/month**

### Risk 3: Discord Rate Limits
**Risk Level**: Low
**Impact**: Bot gets throttled or banned

**Mitigation**:
1. Respect Discord rate limits (50 requests/second per server)
2. Queue messages if multiple users request simultaneously
3. Use message editing instead of multiple posts
4. Add cooldown (e.g., 1 analysis per user per 60 seconds)

### Risk 4: Data Quality Issues
**Risk Level**: Medium
**Impact**: Wrong trade signals due to bad data

**Mitigation**:
1. Validate all API responses (check for null/empty values)
2. Cross-validate with multiple data sources (Schwab + Alpha Vantage)
3. Add data quality checks in DataFetcherAgent
4. Alert user if insufficient data for analysis

---

## 9. Success Metrics

### Phase 1: MVP Launch (Week 3)
- ✅ Bot responds to `!analyze TICKER` commands
- ✅ Generates trade plans with 0-5 confidence scores
- ✅ Includes news sentiment in analysis
- ✅ Stores trade ideas in database
- ✅ Deploys successfully to Railway.app

### Phase 2: Production Validation (Week 4-6)
- ✅ 50+ trade analyses generated
- ✅ Zero critical bugs
- ✅ <5 second average response time
- ✅ >90% uptime
- ✅ Users can track outcomes with `!track` command

### Phase 3: Learning Loop (Week 6-8)
- ✅ First weekly optimization cycle completes
- ✅ Metrics calculated correctly (win rate, R-multiple, Sharpe)
- ✅ LLM suggests meaningful framework modifications
- ✅ Modifications tracked in Memory MCP

### Long-Term (3+ months)
- ✅ 500+ trades tracked
- ✅ Win rate >50% (for confidence 4-5 signals)
- ✅ Average R-multiple >1.5
- ✅ Max drawdown <20%
- ✅ Framework has evolved through 10+ optimization cycles

---

## 10. Comparison: Original Plan vs Optimized Plan

| Aspect | Original Plan | Optimized Plan | Impact |
|--------|---------------|----------------|--------|
| **Architecture** | Unclear (n8n or Python?) | Pure Python ✅ | Faster development |
| **Development Time** | 25-35 hours | 20 hours | 20% faster |
| **Deployment Cost** | $20-27/month (n8n Cloud) | $0-7/month (Railway) | 70% cheaper |
| **Database** | Not specified | SQLite ✅ | Zero cost, portable |
| **MCP Usage** | Not leveraged | Memory + Docker + Axiom ✅ | Automated optimization |
| **Testing** | 4-5 hours | 16 hours (comprehensive) | Higher quality |
| **Learning Loop** | Manual | Semi-automated with Memory MCP ✅ | Continuous improvement |
| **Timeline to MVP** | Unclear | 3-4 weeks ✅ | Clear milestones |
| **Delegation** | Not specified | Minimal (execute directly) ✅ | Faster delivery |

---

## 11. Final Recommendations

### Immediate Actions (This Week)

1. **Fix Configuration Files** ❌ CRITICAL
   - Update `.project-mcp.json` with corrected status/phase
   - Create `doc/task/context.md` (use template above)
   - Update `IMPLEMENTATION_PROGRESS.md` with latest component status

2. **Complete Discord Bot** (3-4 hours)
   - Implement command parsing
   - Format trade plan output
   - Test with mock data

3. **Finish Analysis Engine** (5-6 hours)
   - Implement 3-Tier MTF logic
   - Add all edge filters
   - Integrate LLM for rationale

### Week 2-3: Complete Core + Deploy

4. **Build Remaining Components** (7-9 hours)
   - Data fetcher agent
   - Tracking system
   - Main orchestrator

5. **Testing** (16 hours)
   - Unit tests
   - Integration tests
   - Paper trading validation

6. **Deploy to Railway.app** (10 hours)
   - Dockerize
   - Configure environment
   - Set up monitoring (Axiom MCP)

### Week 4+: Optimize

7. **Implement Learning Loop** (6 hours)
   - Weekly cron job
   - Memory MCP integration
   - Framework versioning (GitHub MCP)

8. **First Optimization Cycle**
   - Run for 1-2 weeks
   - Collect outcomes
   - Generate first optimization suggestions

### Long-Term Enhancements (Future)

- **Multi-User Support**: If demand grows, migrate to PostgreSQL + API authentication
- **Web Dashboard**: Add web interface for visualizing performance metrics
- **Additional Integrations**: Slack, Telegram, webhooks
- **Advanced Backtesting**: Historical validation against past market data
- **Portfolio Management**: Track multiple positions, correlations, total exposure

---

## Conclusion

**The path forward is clear: Continue with pure Python implementation.**

The project has solid foundations (35% complete) and the complexity of the Trading Workflow V2 specification naturally fits a Python architecture. Switching to n8n or hybrid would waste existing work and add unnecessary complexity.

**Key Strengths**:
- ✅ Database schema designed for all requirements
- ✅ Technical indicators professionally implemented
- ✅ Schwab API client with OAuth and rate limiting
- ✅ Clear spec to follow (Trading Workflow V2.md)
- ✅ Only 20 hours from MVP

**Critical Path**:
1. Fix configuration files (1 hour)
2. Complete core components (20 hours)
3. Test thoroughly (16 hours)
4. Deploy with Docker + Axiom monitoring (10 hours)
5. Implement learning loop with Memory MCP (6 hours)

**Total: 3-4 weeks to production-ready bot**

**Cost**: $0-7/month (vs $20-27/month for hybrid)

**MCP Leverage**: Memory (learning), Docker (deployment), Axiom (monitoring), GitHub (versioning)

This plan maximizes the value of work already completed while providing a clear, achievable path to MVP and beyond.

---

**Next Steps**: Would you like me to:
1. Fix the configuration files (.project-mcp.json, create context.md)?
2. Begin implementation of Discord bot integration?
3. Delegate deployment research to webapp-dev sub-agent?
4. Something else?
