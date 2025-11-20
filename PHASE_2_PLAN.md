# Phase II: Performance Tracking & Optimization System

**Start Date:** 2025-11-20
**Goal:** Build feedback loop for continuous algorithm improvement

---

## Implementation Order (Recommended)

### Step 1: Database Foundation ⚡ START HERE
**Why First:** Everything else depends on data storage
**Timeline:** 30 minutes

**Tasks:**
1. Design schema for trade tracking tables
2. Create Supabase migration SQL
3. Run migration on existing Supabase instance
4. Test table creation

**Tables to Create:**
- `trade_signals` - Every signal the bot generates
- `trade_outcomes` - Results of each trade (W/L/Expired)
- `edge_performance` - Track which edges work best
- `weekly_reports` - Store generated analysis reports

---

### Step 2: Auto-Logging in FastAPI ⚡
**Why Second:** Start collecting data immediately
**Timeline:** 45 minutes

**Tasks:**
1. Update `/analyze` endpoint to log signals to database
2. Store full trade details (entry, stop, targets, edges, confidence)
3. Set initial status as "PENDING"
4. Return trade_id to Discord (for manual tracking if needed)

**Integration Point:**
```python
# After generating analysis, before returning response
db.insert_trade_signal({
    'trade_id': trade_id,
    'ticker': ticker,
    'trade_type': trade_type,
    'direction': direction,
    'entry': entry,
    'stop': stop,
    'target': target,
    'confidence': confidence,
    'edges': edges,
    'status': 'PENDING',
    'created_at': datetime.now()
})
```

---

### Step 3: Outcome Tracking Background Job ⚡
**Why Third:** Need to monitor what happens to trades
**Timeline:** 1-2 hours

**Tasks:**
1. Create background worker script (runs every hour)
2. Query all PENDING trades from database
3. Check current price against entry/stop/target using Schwab API
4. Update status: WIN (hit target), LOSS (hit stop), or still PENDING
5. Calculate actual R-multiple achieved
6. Set expiry (7 days if not triggered)

**Logic:**
```python
for trade in pending_trades:
    current_price = get_current_price(trade.ticker)

    if direction == 'long':
        if current_price >= target:
            status = 'WIN'
            r_achieved = calculate_r(entry, target, stop)
        elif current_price <= stop:
            status = 'LOSS'
            r_achieved = -1.0

    db.update_trade_outcome(trade_id, status, r_achieved)
```

**Deployment:**
- Run as Railway cron job or GitHub Actions workflow
- Runs every hour during market hours (9:30 AM - 4:00 PM ET)

---

### Step 4: Next.js Analytics Dashboard 🎨
**Why Fourth:** Visualize the data we've collected
**Timeline:** 2-3 hours

**Features:**
1. **Overview Page**
   - Total trades: X
   - Win rate: XX%
   - Average R-multiple: X.XR
   - Best performing edge
   - Charts: Win rate over time, R-multiple distribution

2. **Trade History Table**
   - Filterable by: date range, ticker, trade_type, status, confidence
   - Columns: Ticker, Type, Direction, Entry, Stop, Target, Confidence, Edges, Status, R-Achieved, Date
   - Click to see full details

3. **Edge Analysis**
   - Table showing each edge filter
   - Columns: Edge Name, Times Appeared, Win Rate, Avg R-Multiple
   - Sort by win rate to see best performers

4. **Confidence Analysis**
   - Win rate by confidence level (1-5 stars)
   - Shows if higher confidence = better performance

5. **Time-Based Filters**
   - Toggle: Day / Week / Month / Year
   - Compare periods

**Tech Stack:**
- Next.js 14 (App Router)
- Supabase Client for data fetching
- Recharts for visualizations
- Tailwind CSS for styling
- Deploy to Vercel

---

### Step 5: Weekly Analysis Report Generator 📊
**Why Fifth:** Automated insights for improvement
**Timeline:** 1-2 hours

**Features:**
1. **Auto-Generate Every Sunday at 8 PM CT**
2. **Report Contents:**
   - Week's performance summary (total trades, win rate, avg R)
   - Best performing edges this week
   - Worst performing edges this week
   - Confidence level analysis
   - Day trade vs Swing trade comparison
   - Suggested parameter adjustments
   - Top 3 trades (highest R-multiple)
   - Bottom 3 trades (losses or misses)

3. **Storage:**
   - Save to `weekly_reports` table
   - Viewable in dashboard under "Reports" tab

4. **Delivery Options:**
   - Discord message with summary + link to full report
   - Email (optional)
   - Always available in dashboard

**Analysis Logic:**
```python
def generate_weekly_report():
    trades = get_trades_for_week()

    # Calculate metrics
    win_rate = calculate_win_rate(trades)
    avg_r = calculate_average_r(trades)

    # Edge analysis
    edge_performance = analyze_edges(trades)
    best_edges = edge_performance.sort_by('win_rate').head(3)
    worst_edges = edge_performance.sort_by('win_rate').tail(3)

    # Confidence analysis
    confidence_breakdown = group_by_confidence(trades)

    # Generate recommendations
    recommendations = []
    if worst_edges.win_rate < 40%:
        recommendations.append(f"Consider removing {worst_edge.name}")
    if confidence_5_win_rate < confidence_3_win_rate:
        recommendations.append("Review confidence scoring algorithm")

    return report
```

---

### Step 6: Manual Override & Notes (Optional Enhancement)
**Why Last:** Nice to have, not critical
**Timeline:** 1 hour

**Features:**
- Button in dashboard to manually update trade outcome
- Add notes field for each trade
- Flag trades for review
- Useful if you took trade differently than bot suggested

---

## Database Schema Design

### Table: `trade_signals`
```sql
CREATE TABLE trade_signals (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    trade_id VARCHAR(50) UNIQUE NOT NULL,  -- e.g. NVDA-20251120-001
    ticker VARCHAR(10) NOT NULL,
    trade_type VARCHAR(10) NOT NULL,  -- 'day' or 'swing'
    direction VARCHAR(10) NOT NULL,   -- 'long' or 'short'

    -- Price levels
    entry DECIMAL(10,2) NOT NULL,
    stop DECIMAL(10,2) NOT NULL,
    target DECIMAL(10,2) NOT NULL,
    target2 DECIMAL(10,2),

    -- Analysis details
    confidence INTEGER NOT NULL CHECK (confidence >= 0 AND confidence <= 5),
    edges JSONB,  -- Array of edge objects
    edges_count INTEGER,
    rationale TEXT,

    -- Market context
    atr_value DECIMAL(10,2),
    market_volatility VARCHAR(20),
    spy_bias VARCHAR(20),

    -- Status tracking
    status VARCHAR(20) DEFAULT 'PENDING',  -- PENDING, WIN, LOSS, EXPIRED
    r_achieved DECIMAL(5,2),  -- Actual R-multiple if closed

    -- Timestamps
    created_at TIMESTAMP DEFAULT NOW(),
    triggered_at TIMESTAMP,
    closed_at TIMESTAMP,
    expires_at TIMESTAMP,  -- 7 days after creation

    -- Metadata
    sent_to_discord BOOLEAN DEFAULT TRUE,
    user_notes TEXT,
    flagged_for_review BOOLEAN DEFAULT FALSE
);

CREATE INDEX idx_trade_signals_ticker ON trade_signals(ticker);
CREATE INDEX idx_trade_signals_status ON trade_signals(status);
CREATE INDEX idx_trade_signals_created_at ON trade_signals(created_at);
CREATE INDEX idx_trade_signals_confidence ON trade_signals(confidence);
```

### Table: `edge_performance` (Materialized View - Updated Weekly)
```sql
CREATE MATERIALIZED VIEW edge_performance AS
SELECT
    edge->>'name' as edge_name,
    COUNT(*) as total_appearances,
    SUM(CASE WHEN status = 'WIN' THEN 1 ELSE 0 END) as wins,
    SUM(CASE WHEN status = 'LOSS' THEN 1 ELSE 0 END) as losses,
    ROUND(
        (SUM(CASE WHEN status = 'WIN' THEN 1 ELSE 0 END)::DECIMAL /
         NULLIF(SUM(CASE WHEN status IN ('WIN','LOSS') THEN 1 ELSE 0 END), 0)) * 100,
        2
    ) as win_rate_pct,
    ROUND(AVG(r_achieved), 2) as avg_r_multiple
FROM trade_signals,
LATERAL jsonb_array_elements(edges) as edge
WHERE status IN ('WIN', 'LOSS')
GROUP BY edge->>'name'
ORDER BY win_rate_pct DESC;

CREATE UNIQUE INDEX idx_edge_performance_name ON edge_performance(edge_name);
```

### Table: `weekly_reports`
```sql
CREATE TABLE weekly_reports (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    week_start DATE NOT NULL,
    week_end DATE NOT NULL,

    -- Summary metrics
    total_trades INTEGER,
    total_wins INTEGER,
    total_losses INTEGER,
    total_expired INTEGER,
    win_rate DECIMAL(5,2),
    avg_r_multiple DECIMAL(5,2),

    -- Best/Worst
    best_edges JSONB,
    worst_edges JSONB,
    confidence_breakdown JSONB,

    -- Recommendations
    recommendations TEXT[],

    -- Full report
    report_json JSONB,
    report_html TEXT,

    created_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX idx_weekly_reports_week_start ON weekly_reports(week_start);
```

---

## Tech Stack Summary

### Backend:
- **FastAPI** - Existing API, add logging middleware
- **Python Script** - Background outcome tracker (runs hourly)
- **Supabase** - PostgreSQL database (existing instance)
- **Schwab API** - Price data for outcome tracking

### Frontend:
- **Next.js 14** - Dashboard framework
- **Supabase JS Client** - Database queries
- **Recharts** - Data visualization
- **Tailwind CSS** - Styling
- **Vercel** - Deployment

### Automation:
- **GitHub Actions** or **Railway Cron** - Run outcome tracker hourly
- **n8n** (optional) - Trigger weekly report generation

---

## Success Metrics

After 1 week of Phase II:
- ✅ All trades auto-logged to database
- ✅ Outcome tracking running smoothly
- ✅ Dashboard shows real data
- ✅ First weekly report generated

After 1 month:
- 📊 Clear picture of which edges work best
- 📊 Data-driven tweaks to confidence scoring
- 📊 Improved win rate through optimization

---

## Files to Create

1. `database/phase2_migration.sql` - New tables
2. `src/database/trade_logger.py` - Trade logging functions
3. `scripts/outcome_tracker.py` - Background monitoring job
4. `scripts/weekly_report_generator.py` - Analysis report creator
5. `dashboard/` - Next.js app (new directory)
   - `app/page.tsx` - Overview
   - `app/trades/page.tsx` - Trade history
   - `app/edges/page.tsx` - Edge analysis
   - `app/reports/page.tsx` - Weekly reports
   - `lib/supabase.ts` - Database client
   - `components/` - Reusable UI components

---

## Let's Start!

**Ready to begin with Step 1: Database Schema?**

I'll create the migration SQL and we can run it on your Supabase instance right now.
