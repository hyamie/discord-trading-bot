# Autonomous Deployment Roadmap - Discord Trading Bot

**Date**: 2025-11-18
**Purpose**: Step-by-step plan for full autonomous operation
**Target**: Zero manual intervention after initial setup

---

## Quick Summary

**Current Status**: 98% code complete, learning system designed but not implemented
**Blocking**: 10 hours of learning agent code + n8n workflow creation
**User Setup Time**: 30 minutes (one-time credentials)
**Autonomous After**: 21 hours development + 1 week testing

---

## Phase 1: MCP Configuration (NOW - 10 minutes)

### Required MCP Additions

**Update `.project-mcp.json`**:

```json
{
  "requiredMcps": [
    "postgres",            // ← ADD (Supabase queries)
    "memory",              // ← ENABLE (learning insights)
    "n8n",                 // ← ADD (workflow automation)
    "github",              // KEEP
    "filesystem",          // KEEP
    "git",                 // KEEP
    "sequential-thinking"  // KEEP
  ]
}
```

**Action**:
1. Check if `postgres` MCP available: `mcp list | grep postgres`
2. If not available, use Bash + Python scripts (fallback)
3. Confirm `memory` MCP active
4. Add `n8n` MCP to configuration

---

## Phase 2: Learning System Implementation (FULLY AUTONOMOUS - 10 hours)

### Component 1: Learning Agent (6 hours)

**File**: `src/agents/learning_agent.py`

**Key Functions**:
```python
class LearningAgent:
    def query_outcomes_for_week(self, week_start, week_end):
        """Query closed trades from Supabase"""
        # Use postgres MCP or Bash + psql

    def calculate_metrics(self, outcomes):
        """Calculate win rate, avg R, Sharpe, drawdown"""
        return {
            "win_rate": 0.6,
            "avg_r_multiple": 1.8,
            "max_drawdown": -5.2,
            "sharpe_ratio": 1.1,
            "total_trades": 15
        }

    def analyze_with_llm(self, outcomes, metrics):
        """Send to Claude/GPT for pattern analysis"""
        prompt = OPTIMIZATION_PROMPT.format(
            outcomes_json=json.dumps(outcomes),
            win_rate=metrics["win_rate"],
            # ...
        )
        return llm_client.analyze(prompt)

    def store_suggestions(self, week, metrics, suggestions):
        """Save to modifications table + Memory MCP"""
        # Database insert
        db.insert_modification(week, metrics, suggestions)

        # Memory MCP
        mcp__memory__create_memory({
            "messages": [{
                "role": "user",
                "content": f"Week {week}: {suggestions}"
            }]
        })

    def update_framework_params(self, suggestions):
        """Apply approved modifications to framework"""
        # Update config files
        # Git commit changes
        # Deploy to Railway
```

**Donnie Executes**:
```bash
# Day 1: Create agent
Write: src/agents/learning_agent.py (6 hours)

# Test locally
python -c "from src.agents.learning_agent import LearningAgent; agent = LearningAgent(); print(agent.test_metrics())"
```

### Component 2: Query Scripts (2 hours)

**File**: `scripts/query_outcomes.py`

```python
#!/usr/bin/env python3
"""Query outcomes from Supabase for learning analysis"""
import os
import asyncpg
from datetime import datetime, timedelta

async def query_outcomes(days=7):
    """Get all closed trades from last N days"""
    db_url = os.getenv("DATABASE_URL")
    conn = await asyncpg.connect(db_url)

    await conn.execute("SET search_path TO discord_trading, public")

    query = """
        SELECT
            t.ticker,
            t.trade_type,
            t.direction,
            t.confidence,
            t.edges_applied,
            o.actual_outcome,
            o.profit_loss_r,
            o.exit_reason,
            o.close_timestamp
        FROM trade_ideas t
        JOIN outcomes o ON t.id = o.trade_id
        WHERE o.close_timestamp > $1
        ORDER BY o.close_timestamp DESC
    """

    since = datetime.now() - timedelta(days=days)
    results = await conn.fetch(query, since)

    await conn.close()
    return [dict(r) for r in results]

if __name__ == "__main__":
    import asyncio
    outcomes = asyncio.run(query_outcomes(7))
    print(json.dumps(outcomes, indent=2, default=str))
```

**File**: `scripts/calculate_metrics.py`

```python
#!/usr/bin/env python3
"""Calculate performance metrics from outcomes"""
import statistics

def calculate_metrics(outcomes):
    """Compute win rate, avg R, Sharpe, drawdown"""
    if not outcomes:
        return {}

    wins = [o for o in outcomes if o["actual_outcome"] == "win"]
    losses = [o for o in outcomes if o["actual_outcome"] == "loss"]

    r_multiples = [o["profit_loss_r"] for o in outcomes if o["profit_loss_r"]]

    return {
        "total_trades": len(outcomes),
        "wins": len(wins),
        "losses": len(losses),
        "win_rate": len(wins) / len(outcomes) if outcomes else 0,
        "avg_r_multiple": statistics.mean(r_multiples) if r_multiples else 0,
        "max_drawdown": calculate_drawdown(outcomes),
        "sharpe_ratio": calculate_sharpe(r_multiples)
    }

def calculate_drawdown(outcomes):
    """Calculate maximum drawdown percentage"""
    # Implementation here
    pass

def calculate_sharpe(r_multiples):
    """Simplified Sharpe ratio"""
    if not r_multiples or len(r_multiples) < 2:
        return 0

    mean_return = statistics.mean(r_multiples)
    std_dev = statistics.stdev(r_multiples)

    if std_dev == 0:
        return 0

    # Simplified: assume risk-free rate = 0
    return mean_return / std_dev
```

### Component 3: Memory MCP Integration (2 hours)

**Modify**: `src/agents/learning_agent.py`

```python
def store_insights_in_memory(self, week, metrics, suggestions):
    """Store weekly insights in Memory MCP for long-term recall"""

    memory_content = f"""
    Week {week} Trading Performance Analysis

    Metrics:
    - Win Rate: {metrics['win_rate'] * 100:.1f}%
    - Avg R-Multiple: {metrics['avg_r_multiple']:.2f}
    - Max Drawdown: {metrics['max_drawdown']:.1f}%
    - Sharpe Ratio: {metrics['sharpe_ratio']:.2f}
    - Total Trades: {metrics['total_trades']}

    Patterns Identified:
    {suggestions['patterns']}

    Suggested Framework Modifications:
    {chr(10).join(f"- {s}" for s in suggestions['suggested_changes'])}

    Expected Impact:
    {suggestions['expected_impact']}
    """

    # Store in Memory MCP
    from tools import mcp__memory__create_memory

    mcp__memory__create_memory({
        "messages": [{
            "role": "user",
            "content": memory_content
        }]
    })
```

### Component 4: Weekly Cron Job (1 hour)

**Option A: Railway Cron** (recommended)

Create `Procfile`:
```
web: uvicorn src.api.main:app --host 0.0.0.0 --port $PORT
worker: python scripts/weekly_learning_loop.py
```

Create `scripts/weekly_learning_loop.py`:
```python
#!/usr/bin/env python3
"""Weekly learning loop - runs every Sunday"""
import schedule
import time
from src.agents.learning_agent import LearningAgent

def run_weekly_analysis():
    """Execute weekly learning loop"""
    agent = LearningAgent()

    # Query outcomes
    outcomes = agent.query_outcomes_for_week()

    # Calculate metrics
    metrics = agent.calculate_metrics(outcomes)

    # LLM analysis
    suggestions = agent.analyze_with_llm(outcomes, metrics)

    # Store results
    agent.store_suggestions(metrics, suggestions)
    agent.store_insights_in_memory(metrics, suggestions)

    print(f"[LEARNING LOOP] Week complete. Win rate: {metrics['win_rate']}")

# Schedule for Sunday 00:00 UTC
schedule.every().sunday.at("00:00").do(run_weekly_analysis)

if __name__ == "__main__":
    print("[LEARNING LOOP] Starting scheduler...")
    while True:
        schedule.run_pending()
        time.sleep(3600)  # Check every hour
```

**Option B: n8n Cron** (via n8n-mcp agent)

Delegate to n8n-mcp to create cron workflow.

**Deploy to Railway**:
```bash
git add Procfile scripts/weekly_learning_loop.py
git commit -m "feat(learning): Add weekly learning loop cron"
git push origin main
railway up
```

---

## Phase 3: n8n Workflow Creation (DELEGATE TO n8n-mcp - 8 hours)

### Task for n8n-mcp Agent

```python
Task(
  subagent_type: "n8n-mcp",
  prompt: """
  Create 3 n8n workflows in n8n Cloud (hyamie.app.n8n.cloud):

  AVAILABLE MCPs:
  - n8n: Create/modify workflows
  - postgres: Query Supabase (discord_trading schema)
  - github: Save workflow JSONs

  IMPORTANT: Use n8n MCP to create workflows automatically, not manual.

  === WORKFLOW 1: Main Trading Analysis ===

  Trigger: Webhook (/webhook/discord-trading)

  Nodes:
  1. Webhook (Discord → n8n)
  2. Parse Command (Function node):
     - Extract ticker, trade_type from message
     - Validate format

  3. Rate Limit Check (Supabase query):
     - Query: SELECT COUNT(*) FROM discord_trading.api_calls
              WHERE api_name='discord_command' AND timestamp > NOW() - INTERVAL '1 minute'
     - If count > 5: Return "Rate limit exceeded"

  4. Call Railway API (HTTP Request):
     - Method: POST
     - URL: https://discord-trading-bot-production-f596.up.railway.app/analyze
     - Body: {ticker, trade_type}
     - Timeout: 30s

  5. Confidence Filter (Switch node):
     - If confidence >= 3: Continue to alert
     - If confidence < 3: Log only (no Discord message)

  6. Save Trade Idea (Supabase insert):
     - Table: discord_trading.trade_ideas
     - Fields: ticker, trade_type, direction, confidence, entry, stop, target, rationale, edges_applied

  7. Send Discord Alert (Discord node):
     - Format: Markdown embed
     - Include: Ticker, confidence, entry/stop/target, rationale, edges

  8. Error Handler (Error workflow):
     - Log to: discord_trading.system_events
     - Notify: Discord (user-friendly error message)

  === WORKFLOW 2: Trade Tracking Cron ===

  Trigger: Schedule (*/15 * * * * - every 15 minutes)

  Nodes:
  1. Query Open Trades (Supabase):
     - Query: SELECT * FROM discord_trading.trade_ideas WHERE status='active'

  2. Loop Through Trades (Loop node):
     - For each trade:
       a. Get current price (HTTP to Railway /quote endpoint)
       b. Check if stop/target hit
       c. If closed:
          - Update outcomes table
          - Update trade_ideas.status = 'closed'
          - Send Discord notification

  3. Update Database (Supabase):
     - Table: discord_trading.outcomes
     - Fields: trade_id, actual_outcome, profit_loss_r, exit_reason, close_price

  === WORKFLOW 3: Weekly Learning Loop Cron ===

  Trigger: Schedule (0 0 * * 0 - Sunday midnight UTC)

  Nodes:
  1. Query Last Week Outcomes (Supabase):
     - Query: SELECT * FROM discord_trading.outcomes
              WHERE close_timestamp > NOW() - INTERVAL '7 days'

  2. Calculate Metrics (Function node):
     - Win rate, avg R-multiple, Sharpe ratio, max drawdown

  3. LLM Analysis (HTTP to Railway):
     - Endpoint: POST /optimize (create this endpoint)
     - Body: {outcomes, metrics}
     - Response: {patterns, suggested_changes}

  4. Save Modifications (Supabase insert):
     - Table: discord_trading.modifications
     - Fields: week, metrics, suggested_changes, patterns_identified

  5. Send Weekly Report (Discord):
     - Channel: #trading-insights
     - Content: Metrics summary, patterns, suggestions

  OUTPUT:
  - Save workflow JSONs to: workflows/main-trading.json, workflows/tracking-cron.json, workflows/learning-loop.json
  - Test each workflow before completion
  - Document any issues encountered
  """
)
```

**Donnie Reviews**:
1. Read generated workflow JSONs
2. Verify Supabase schema references (discord_trading.*)
3. Confirm Railway API URLs correct
4. Approve for deployment

**n8n-mcp Deploys**:
- Import workflows to n8n Cloud
- Configure credentials (Supabase, Railway, Discord)
- Test each workflow individually

---

## Phase 4: Discord Bot Setup (SEMI-AUTONOMOUS - 3 hours)

### Prerequisite: User Provides Discord Bot Token

**User Action** (5 minutes):
1. Go to https://discord.com/developers/applications
2. Create new application → "Trading Bot"
3. Add bot → Copy token
4. Invite bot to server (Administrator permissions)
5. Provide token to Donnie

### Donnie Creates Discord Bot

**File**: `discord_bot/bot.py`

```python
#!/usr/bin/env python3
"""Discord bot for trading signals"""
import os
import discord
from discord.ext import commands
import requests

# Create bot
intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix='!', intents=intents)

RAILWAY_API_URL = os.getenv(
    "RAILWAY_API_URL",
    "https://discord-trading-bot-production-f596.up.railway.app"
)

@bot.event
async def on_ready():
    print(f'[BOT] Logged in as {bot.user}')

@bot.command()
async def analyze(ctx, ticker: str, trade_type: str = "day"):
    """Analyze a ticker for trade signals"""
    await ctx.send(f"🔍 Analyzing {ticker.upper()} ({trade_type} trade)...")

    try:
        # Call Railway API
        response = requests.post(
            f"{RAILWAY_API_URL}/analyze",
            json={"ticker": ticker.upper(), "trade_type": trade_type},
            timeout=30
        )

        if response.status_code == 200:
            data = response.json()

            # Format trade plan
            embed = discord.Embed(
                title=f"Trade Analysis: {ticker.upper()}",
                description=f"Confidence: {data['confidence']}/5",
                color=0x00ff00 if data['signal'] == 'long' else 0xff0000
            )

            embed.add_field(name="Direction", value=data['signal'], inline=True)
            embed.add_field(name="Entry", value=f"${data['entry']}", inline=True)
            embed.add_field(name="Stop", value=f"${data['stop']}", inline=True)
            embed.add_field(name="Target", value=f"${data['target']}", inline=True)
            embed.add_field(name="R:R", value=f"1:{data['risk_reward']}", inline=True)
            embed.add_field(name="Edges Applied", value=", ".join(data['edges_applied']), inline=False)
            embed.add_field(name="Rationale", value=data['rationale'], inline=False)

            await ctx.send(embed=embed)
        else:
            await ctx.send(f"❌ Error: {response.text}")

    except Exception as e:
        await ctx.send(f"❌ Error analyzing {ticker}: {str(e)}")

@bot.command()
async def track(ctx, trade_id: str, outcome: str, exit_price: float):
    """Log trade outcome"""
    # Implementation here
    pass

# Run bot
if __name__ == "__main__":
    token = os.getenv("DISCORD_BOT_TOKEN")
    if not token:
        raise ValueError("DISCORD_BOT_TOKEN not set!")

    bot.run(token)
```

**File**: `discord_bot/requirements.txt`

```
discord.py==2.3.2
requests==2.31.0
```

**Deploy to Railway**:

```bash
# Add environment variable
railway variables set DISCORD_BOT_TOKEN=<user-provided-token>

# Add to Procfile
echo "discord_bot: python discord_bot/bot.py" >> Procfile

# Deploy
git add discord_bot/ Procfile
git commit -m "feat(discord): Add Discord bot integration"
git push origin main
railway up
```

**Test**:
```bash
# In Discord:
!analyze SPY
!analyze AAPL swing
```

---

## Phase 5: Full Integration Testing (AUTONOMOUS - 3 days monitoring)

### Day 1: Component Testing

**Donnie Executes**:
```bash
# Test learning agent
python scripts/test_learning_agent.py

# Test n8n workflows (via webhook)
curl -X POST https://hyamie.app.n8n.cloud/webhook/discord-trading \
  -H "Content-Type: application/json" \
  -d '{"content": "!analyze SPY"}'

# Test Discord bot
# (User sends: !analyze SPY in Discord)

# Verify database writes
psql $DATABASE_URL -c "SELECT * FROM discord_trading.trade_ideas ORDER BY created_at DESC LIMIT 5"
```

### Day 2-3: Live Market Testing

**Monitoring Checklist**:
- [ ] Schwab API: No rate limit errors
- [ ] Analysis Engine: Confidence scores accurate
- [ ] Discord Bot: Messages formatted correctly
- [ ] Trade Tracking: Open trades monitored
- [ ] Weekly Loop: Executed on schedule (Sunday 00:00 UTC)
- [ ] Memory MCP: Insights stored
- [ ] Database: No write errors

---

## Autonomous Operation Checklist

### One-Time Setup (User)
- [ ] Schwab OAuth: Run `python scripts/schwab_oauth_helper.py` (15 min)
- [ ] Discord Bot Token: Create at discord.com/developers (5 min)
- [ ] n8n API Key: Get from n8n Cloud settings (2 min)

### Autonomous Components (Donnie)
- [ ] Learning agent code (6 hours)
- [ ] Query/metrics scripts (2 hours)
- [ ] Memory MCP integration (2 hours)
- [ ] Weekly cron job (1 hour)
- [ ] Discord bot code (2 hours)
- [ ] Deployment automation (1 hour)

### Semi-Autonomous Components (n8n-mcp)
- [ ] Main trading workflow (2 hours)
- [ ] Trade tracking cron (2 hours)
- [ ] Weekly learning cron (2 hours)
- [ ] Testing and verification (2 hours)

---

## Success Metrics

### After 1 Week
- ✅ Learning loop executed without errors
- ✅ Weekly insights stored in Memory MCP
- ✅ Discord bot responsive (<2s latency)
- ✅ Trade tracking automated (15-min checks)
- ✅ Database writes successful (100% rate)

### After 1 Month
- ✅ 4 weekly optimization cycles completed
- ✅ Framework parameters adjusted based on learnings
- ✅ Win rate tracking accurate
- ✅ No manual interventions required (except Schwab token refresh)

---

## Total Timeline

| Phase | Duration | Autonomous | User Input |
|-------|----------|------------|------------|
| **Phase 1: MCP Config** | 10 min | ✅ Full | None |
| **Phase 2: Learning System** | 10 hours | ✅ Full | None |
| **Phase 3: n8n Workflows** | 8 hours | 🟡 Semi | n8n API key |
| **Phase 4: Discord Bot** | 3 hours | 🟡 Semi | Discord token |
| **Phase 5: Testing** | 3 days | ✅ Full | None |
| **TOTAL** | 21 hours + 3 days | 90% | 22 min one-time |

---

**Ready to Execute**: Awaiting user approval to begin Phase 2
**Next Action**: Implement learning agent (fully autonomous)
**Confidence**: VERY HIGH (clear path, no blockers)
