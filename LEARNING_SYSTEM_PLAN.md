# Trading Bot Learning & Strategy Testing System

## Current State
✅ **FULLY OPERATIONAL** (as of 2025-11-21)
- Day trade analysis generating plans with 5-timeframe analysis
- Swing trade analysis generating plans with weekly/daily/30m analysis
- Database logging working (trade_signals table)
- All Schwab API endpoints functional
- pgbouncer compatibility resolved

🔧 **LLM Rationale Generation** - Fixed
- Updated anthropic library from 0.7.8 → 0.40.0
- Updated openai library from 1.6.1 → 1.54.0
- System now generates AI-powered trade rationales

---

## Phase 1: Enhanced Trade Outcome Tracking (Week 1)

### Objective
Automate the collection of trade outcomes to build a performance database.

### Implementation

#### 1.1 Automated Trade Monitoring Service
**File**: `src/services/trade_monitor.py`

```python
# Features:
- Check pending trades every 5 minutes during market hours
- Compare current price vs entry/stop/target
- Auto-update trade outcomes when hit
- Handle partial fills (target1 vs target2)
- Mark expired trades at EOD
```

**Database Updates**:
- Use existing `update_trade_outcome()` method in TradeLogger
- Track: status (WIN/LOSS/EXPIRED), r_achieved, exit_price, exit_reason

#### 1.2 Manual Outcome Entry via Discord
**File**: `src/api/discord_commands.py`

```python
# Discord commands:
/update-trade SPY-20251121-001 WIN 2.5R "Hit target at $595"
/update-trade AAPL-20251121-002 LOSS -1R "Stopped out"
/mark-expired SPY-20251121-003
```

**Benefit**: Allows trader to manually override outcomes or add context

---

## Phase 2: Performance Analysis & Pattern Recognition (Week 2)

### Objective
Analyze historical performance to identify what's working and what isn't.

### Implementation

#### 2.1 Edge Performance Analyzer
**File**: `src/analytics/edge_analyzer.py`

```python
# Analyze by edge filter:
class EdgePerformanceAnalyzer:
    def analyze_edge_effectiveness(self) -> Dict:
        """
        For each edge (Slope Filter, Volume Confirmation, etc.):
        - Win rate when present vs absent
        - Avg R-multiple when present vs absent
        - Statistical significance (chi-square test)

        Returns:
            {
                'Slope Filter': {
                    'win_rate_with': 0.68,
                    'win_rate_without': 0.52,
                    'avg_r_with': 1.8,
                    'avg_r_without': 1.2,
                    'significance': 0.03,  # p-value
                    'recommendation': 'KEEP - significant edge'
                }
            }
        """
```

#### 2.2 Timeframe Analysis
**File**: `src/analytics/timeframe_analyzer.py`

```python
# Analyze performance by timeframe setup:
class TimeframeAnalyzer:
    def analyze_alignment_patterns(self) -> Dict:
        """
        Identify winning patterns:
        - All 3 TFs bullish: 72% win rate
        - Higher bullish, middle neutral, lower bullish: 58% win rate
        - Higher bearish, middle bullish, lower bullish: 41% win rate

        Returns patterns ranked by profitability
        """
```

#### 2.3 Market Condition Correlation
**File**: `src/analytics/market_context_analyzer.py`

```python
# Track performance vs market conditions:
- SPY trend (up/down/sideways)
- VIX level (low/medium/high volatility)
- Time of day (open/mid-day/close)
- Day of week

# Identify:
"Long trades in low VIX environment: 71% win rate"
"Short trades during SPY downtrend: 64% win rate"
"Day trades after 2pm: 39% win rate" <- AVOID
```

---

## Phase 3: LLM-Powered Weekly Analysis (Week 2-3)

### Objective
Generate actionable insights and parameter recommendations using Claude/GPT.

### Implementation

#### 3.1 Weekly Performance Report
**File**: `src/analytics/weekly_report.py`

```python
# Generated every Sunday at 9pm
class WeeklyReportGenerator:
    def generate_report(self) -> str:
        """
        Uses LLM to analyze:
        1. Overall metrics (win rate, R-multiple, total R)
        2. Best/worst performing edges
        3. Market condition correlations
        4. Individual trade reviews (wins AND losses)

        LLM Output:
        - Pattern identification: "Notice all 3 losses had RSI > 70 at entry"
        - Specific recommendations: "Increase volume threshold from 1.5x to 1.8x"
        - Edge adjustments: "Disable Pullback Confirmation in high VIX (>25)"
        """
```

**Delivery**:
- Post to Discord #weekly-analysis channel
- Store in `trade_insights` table for historical reference

#### 3.2 Trade-by-Trade Learning
**File**: `src/analytics/trade_reviewer.py`

```python
# After each closed trade, LLM analyzes:
class TradeReviewer:
    def review_completed_trade(self, trade_id: str) -> Dict:
        """
        LLM reviews:
        - Was the setup truly aligned? (timeframe signals)
        - Were the edges actually present? (backtesting edge accuracy)
        - Did news/events impact outcome?
        - What could have been different?

        Returns:
            {
                'grade': 'A',  # Trade execution quality
                'notes': "Good entry timing, but RSI was extended",
                'learning': "Avoid entries with RSI > 75 even with alignment",
                'suggested_rule': "Add RSI < 75 filter to long entries"
            }
        """
```

---

## Phase 4: Strategy Parameter Optimization (Week 3-4)

### Objective
Test new parameters and strategies in a safe, controlled manner.

### Implementation

#### 4.1 Strategy Configuration System
**File**: `config/strategies/`

```yaml
# base_strategy.yaml (current production strategy)
name: "Base Strategy v1.0"
edges:
  slope_filter:
    enabled: true
    threshold: 0.1
  volume_confirmation:
    enabled: true
    threshold_multiplier: 1.5
  pullback_confirmation:
    enabled: true
    rsi_range: [45, 65]
  volatility_filter:
    enabled: true
    atr_multiplier: 1.25

confidence:
  min_score: 3
  min_edges: 1

---

# test_strategy_v2.yaml (proposed modifications)
name: "Test Strategy v2 - Stricter Volume"
parent: "base_strategy.yaml"
changes:
  edges:
    volume_confirmation:
      threshold_multiplier: 1.8  # INCREASED from 1.5
    pullback_confirmation:
      rsi_range: [50, 70]  # TIGHTENED from [45, 65]

test_config:
  mode: "shadow"  # Generate signals but don't send to Discord
  duration_days: 14
  min_signals: 20
```

#### 4.2 Shadow Testing Framework
**File**: `src/testing/strategy_tester.py`

```python
class StrategyTester:
    def run_shadow_test(self, strategy_config: Dict) -> None:
        """
        Runs new strategy in parallel with production:
        - Generates signals using new parameters
        - Logs to separate table: strategy_test_signals
        - Tracks outcomes just like production
        - NO DISCORD ALERTS (shadow mode)

        After test period:
        - Compare metrics: win_rate, avg_r, total_signals
        - LLM analyzes: "New strategy generated 12% more signals
          with 3% higher win rate - RECOMMEND DEPLOYMENT"
        """
```

#### 4.3 A/B Testing for Edge Filters
**File**: `src/testing/edge_ab_test.py`

```python
# Test one edge modification at a time
class EdgeABTest:
    def test_edge_modification(
        self,
        edge_name: str,
        old_params: Dict,
        new_params: Dict,
        duration_days: int = 14
    ) -> Dict:
        """
        Example:
        Test "Volume Confirmation" with threshold 1.8x vs 1.5x

        Results after 14 days:
        - Old (1.5x): 28 signals, 61% win rate, 1.4 avg R
        - New (1.8x): 18 signals, 71% win rate, 1.9 avg R

        Conclusion: "Stricter volume filter reduces signals by 36%
        but improves quality significantly. RECOMMEND DEPLOYMENT."
        """
```

---

## Phase 5: Continuous Learning Loop (Week 4+)

### Objective
Create a self-improving system that evolves based on performance data.

### Implementation

#### 5.1 Monthly Strategy Review
**Schedule**: First Sunday of each month

```python
class MonthlyReviewSystem:
    def conduct_monthly_review(self) -> None:
        """
        LLM analyzes 30 days of data:
        1. Overall performance vs goals
        2. Edge effectiveness trends (improving/degrading)
        3. Market regime changes (is strategy still suitable?)
        4. Proposed parameter adjustments (2-3 specific changes)

        Outputs:
        - Executive summary report
        - Recommended strategy config for next month
        - Edges to test/modify/disable
        - New edge ideas (from pattern analysis)
        """
```

#### 5.2 Adaptive Confidence Scoring
**File**: `src/agents/adaptive_confidence.py`

```python
# Adjust confidence weights based on historical performance
class AdaptiveConfidenceScorer:
    def adjust_weights(self, performance_data: Dict) -> Dict:
        """
        Currently: Base confidence (0-3) + Edges (0-2) = 0-5

        Adaptive: Weight edges by actual performance
        - Slope Filter: 71% win rate → weight 1.5x
        - Volume Confirmation: 68% win rate → weight 1.3x
        - Pullback Confirmation: 52% win rate → weight 0.8x

        New confidence = Base + (edge1_weight + edge2_weight + ...)

        Result: Higher confidence scores for historically successful setups
        """
```

#### 5.3 New Edge Discovery
**File**: `src/research/edge_discovery.py`

```python
# LLM analyzes winning trades to suggest new edges
class EdgeDiscovery:
    def propose_new_edges(self, winning_trades: List[Dict]) -> List[Dict]:
        """
        LLM reviews top 20 winning trades and identifies commonalities:

        Example findings:
        - "80% of 2R+ winners had price < VWAP at entry for longs"
          → Propose: "Fade Entry" edge (contrarian entry)

        - "75% of swing winners had ADX > 25 on daily TF"
          → Propose: "Trend Strength" edge (ADX filter)

        - "70% of day winners occurred in first 2 hours of trading"
          → Propose: "Time Window" edge (limit to 9:30-11:30 ET)

        Returns list of proposed edges with:
        - Name, description, implementation logic
        - Backtest instructions
        - Expected win rate improvement
        """
```

---

## Phase 6: Dashboard & Monitoring (Week 5)

### Objective
Visualize performance and system health in real-time.

### Implementation

#### 6.1 Performance Dashboard
**Tool**: Streamlit or Grafana

**Metrics**:
- Daily/weekly/monthly win rate
- R-multiple distribution (histogram)
- Equity curve (cumulative R)
- Edge effectiveness heatmap
- Win rate by market condition
- Signal volume by day/hour

#### 6.2 Alert System
**File**: `src/monitoring/alerts.py`

```python
# Alert on anomalies:
- Win rate drops below 50% for 3+ consecutive days
- No signals generated for 2+ days (system issue?)
- New edge underperforming (<40% win rate after 10 trades)
- LLM API failures (fallback to template rationales)
```

---

## Database Schema Extensions

### New Tables

```sql
-- Strategy test results
CREATE TABLE strategy_test_signals (
    id SERIAL PRIMARY KEY,
    strategy_name TEXT NOT NULL,
    strategy_version TEXT NOT NULL,
    trade_id TEXT NOT NULL,
    -- Same columns as trade_signals
    ...
    test_start_date TIMESTAMP,
    test_end_date TIMESTAMP
);

-- Trade reviews (LLM analysis)
CREATE TABLE trade_reviews (
    id SERIAL PRIMARY KEY,
    trade_id TEXT REFERENCES trade_signals(trade_id),
    review_date TIMESTAMP DEFAULT NOW(),
    execution_grade CHAR(1), -- A, B, C, D, F
    llm_notes TEXT,
    suggested_improvement TEXT,
    proposed_rule TEXT
);

-- Edge performance tracking
CREATE TABLE edge_performance_history (
    id SERIAL PRIMARY KEY,
    edge_name TEXT NOT NULL,
    week_start DATE NOT NULL,
    total_trades INT,
    wins INT,
    losses INT,
    avg_r_multiple DECIMAL(5,2),
    win_rate DECIMAL(5,4),
    recommendation TEXT -- KEEP, MODIFY, DISABLE
);

-- Strategy configurations
CREATE TABLE strategy_configs (
    id SERIAL PRIMARY KEY,
    name TEXT NOT NULL,
    version TEXT NOT NULL,
    config JSONB NOT NULL,
    status TEXT CHECK (status IN ('active', 'testing', 'archived')),
    deployed_at TIMESTAMP,
    retired_at TIMESTAMP
);

-- Weekly insights
CREATE TABLE weekly_insights (
    id SERIAL PRIMARY KEY,
    week_start DATE NOT NULL,
    week_end DATE NOT NULL,
    total_trades INT,
    win_rate DECIMAL(5,4),
    avg_r_multiple DECIMAL(5,2),
    llm_analysis TEXT,
    recommended_changes JSONB,
    created_at TIMESTAMP DEFAULT NOW()
);
```

---

## Deployment Plan

### Week 1: Foundation
1. ✅ Fix LLM library versions (anthropic 0.40.0, openai 1.54.0)
2. ✅ Deploy to Railway
3. Create trade_monitor service (automated outcome tracking)
4. Add Discord commands for manual outcome entry
5. Test LLM rationale generation in production

### Week 2: Analytics
1. Build edge_analyzer.py
2. Build timeframe_analyzer.py
3. Build market_context_analyzer.py
4. Create weekly_report generator
5. Add new database tables
6. Run first weekly analysis

### Week 3: Testing Framework
1. Implement strategy config system (YAML)
2. Build shadow testing framework
3. Create first test strategy (stricter volume threshold)
4. Run 14-day shadow test
5. LLM analyzes shadow test results

### Week 4: Learning Loop
1. Implement adaptive confidence scoring
2. Build edge discovery system
3. Create monthly review system
4. Set up automated alerts
5. Deploy dashboard (Streamlit)

### Week 5+: Continuous Improvement
1. Review monthly performance
2. Deploy winning strategy modifications
3. Test new edges discovered by LLM
4. Refine and iterate

---

## Success Metrics

### Short-term (1 month)
- ✅ LLM generating rationales for 100% of trades
- ✅ Trade outcomes tracked automatically (>90% accuracy)
- 📊 Weekly analysis reports generated and reviewed
- 📊 At least 1 edge modification tested

### Medium-term (3 months)
- 📈 Win rate improvement: Current baseline → +5% (e.g., 55% → 60%)
- 📈 Avg R-multiple improvement: Current baseline → +0.3R
- 🧪 3+ strategy variants tested via shadow mode
- 🧪 1+ new edge discovered and deployed

### Long-term (6 months)
- 🎯 Achieve 65%+ win rate with 1.5R+ avg R-multiple
- 🎯 Self-optimizing system requires minimal manual intervention
- 🎯 Proven track record of 100+ closed trades
- 🎯 Strategy adapts to different market regimes automatically

---

## Next Steps (Immediate)

1. **Fix LLM libraries** - Update requirements.txt and deploy ✅ (IN PROGRESS)
2. **Have Donnie review** - Meta-orchestrator analysis of working system
3. **Have helper review** - Additional specialized agent perspective
4. **Design first test strategy** - Identify 1-2 parameter changes to test
5. **Implement trade monitor** - Start collecting outcome data automatically

---

## Questions for User

1. **Testing Approach**: Should we start with shadow testing (no risk) or go straight to production testing (real signals)?
2. **Risk Tolerance**: How many signals per day are acceptable during testing? (More data = faster learning, but more noise)
3. **Priority**: Which phase is most important to you?
   - [ ] Outcome tracking (Phase 1)
   - [ ] Performance analysis (Phase 2)
   - [ ] Strategy testing (Phase 4)
   - [ ] All equally important
4. **Human Oversight**: Do you want to approve all strategy changes, or should the system auto-deploy if confidence is high?

