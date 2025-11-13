# Discord Trading Bot - Codebase Audit

**Date**: 2025-11-12
**Auditor**: Claude Code (Donnie)
**Purpose**: Assess existing Python implementation before FastAPI refactoring

---

## Executive Summary

**Total Lines of Code**: 2,236 lines across 7 Python files
**Completion Status**: ~50-60% (higher than reported 35%)
**Quality**: Professional-grade with proper type hints, logging, error handling
**Reusability**: 90%+ of code can be reused with minimal changes

**Key Finding**: Most core logic is ALREADY implemented! We mainly need:
1. Wrap existing code in FastAPI endpoints
2. Migrate SQLite → Supabase connection strings
3. Add Pydantic models for API requests/responses
4. Deploy to Railway

---

## File-by-File Analysis

### ✅ src/utils/indicators.py (371 lines) - COMPLETE & READY

**Status**: Production-ready, needs NO changes
**Quality**: Excellent - proper docstrings, type hints, error handling

**Implemented**:
- ✅ EMA calculation (any period)
- ✅ SMA calculation
- ✅ RSI calculation (14-period, proper EMA smoothing)
- ✅ ATR calculation (True Range formula)
- ✅ VWAP calculation (intraday reset support)
- ✅ Slope detection (EMA strength over N periods)
- ✅ Divergence detection (bullish/bearish patterns)
- ✅ 3-bar breakout validation
- ✅ Bulk indicator calculation (`calculate_all_indicators`)
- ✅ Signal summary generation (`get_signal_summary`)

**Example Method Signature**:
```python
def calculate_all_indicators(
    df: pd.DataFrame,
    timeframe: str = '1h'
) -> pd.DataFrame:
    """Calculate all indicators and add to DataFrame"""
```

**Reusability**: 100% - Can use as-is in FastAPI service

---

### ✅ src/utils/schwab_api.py (431 lines) - 95% COMPLETE

**Status**: Nearly production-ready, minor token persistence needed
**Quality**: Excellent - OAuth 2.0, rate limiting, token refresh

**Implemented**:
- ✅ OAuth 2.0 authorization flow
- ✅ Token refresh logic (auto-refresh before expiration)
- ✅ Rate limiting (120 calls/min with queue)
- ✅ Retry logic with exponential backoff
- ✅ Multi-timeframe batch fetching
- ✅ Quote endpoint (`get_quote`)
- ✅ Price history endpoint (`get_price_history`)
- ✅ Error handling and logging

**Needs**:
- ⏳ Token persistence (save refresh_token to env/database)
- ⏳ Initial OAuth setup helper script

**Example Method**:
```python
def get_multiple_timeframes(
    self,
    ticker: str,
    configs: List[Dict]
) -> Dict[str, pd.DataFrame]:
    """Fetch multiple timeframes in one call"""
```

**Reusability**: 95% - Add token persistence, then use as-is

**Bonus**: Includes `AlphaVantageClient` fallback (5 calls/min limit)

---

### ✅ src/utils/news_api.py (477 lines) - COMPLETE

**Status**: Production-ready
**Quality**: Excellent - dual news sources with aggregation

**Implemented**:
- ✅ Finnhub client (company news, sentiment)
- ✅ NewsAPI client (headlines, filtering)
- ✅ News aggregation (`NewsAggregator` class)
- ✅ Sentiment analysis
- ✅ News summarization
- ✅ Deduplication logic
- ✅ Rate limiting for both APIs

**Example Method**:
```python
def aggregate_news(
    self,
    ticker: str,
    max_articles: int = 5
) -> Dict:
    """Fetch and aggregate news from multiple sources"""
```

**Reusability**: 100% - Can use as-is

---

### ✅ src/agents/analysis_engine.py (589 lines) - 90% COMPLETE

**Status**: Core logic implemented, needs LLM integration
**Quality**: Excellent - full 3-Tier MTF analysis

**Implemented**:
- ✅ `analyze_ticker()` - Main entry point
- ✅ `_analyze_day_trade()` - Day trade analysis
- ✅ `_analyze_swing_trade()` - Swing trade analysis
- ✅ `_analyze_timeframe()` - Per-TF signal logic
- ✅ `_calculate_trend_bias()` - EMA20 vs EMA50
- ✅ `_calculate_momentum_bias()` - RSI thresholds
- ✅ `_detect_entry_trigger()` - 3-bar breakout
- ✅ `_apply_edge_filters()` - All 5 edges implemented:
  - Slope Filter (EMA20 strength)
  - Volume Confirmation (1.5x avg)
  - Pullback Confirmation (VWAP + RSI)
  - Volatility Filter (candle range vs ATR)
  - Divergence Detection
- ✅ `_calculate_confidence()` - 0-5 scoring
- ✅ `_calculate_stop_target()` - ATR-based R:R
- ✅ `_format_trade_plan()` - Output structure

**Needs**:
- ⏳ LLM integration for rationale generation (currently placeholder)
- ⏳ SPY market bias logic (partial implementation)

**Example Output**:
```python
{
  'ticker': 'AAPL',
  'trade_type': 'day',
  'direction': 'long',
  'entry': 175.50,
  'stop': 174.25,
  'target': 178.00,
  'confidence': 4,
  'edges_applied': ['Slope Filter', 'Volume Confirmation', 'VWAP Alignment'],
  'rationale': 'Strong bullish momentum...',
  'risk_reward_ratio': 2.0
}
```

**Reusability**: 90% - Add LLM calls, then use as-is

---

### ✅ src/database/db_manager.py (349 lines) - COMPLETE

**Status**: Production-ready for SQLite, needs Supabase migration
**Quality**: Excellent - full ORM-like interface

**Implemented**:
- ✅ Database initialization
- ✅ Trade idea CRUD operations
- ✅ Outcome tracking (insert, update, query)
- ✅ Caching layer (60sec TTL)
- ✅ Performance metrics calculation
- ✅ API call logging
- ✅ System event logging
- ✅ Automatic cache expiration cleanup

**Key Methods**:
```python
insert_trade_idea(trade_data: Dict) -> str
insert_outcome(outcome_data: Dict) -> int
get_performance_metrics(start_date, end_date) -> Dict
get_cached_data(cache_key: str) -> Optional[Dict]
log_api_call(api_data: Dict)
```

**Needs**:
- ⏳ Migrate to Supabase connection (replace sqlite3 with psycopg2)
- ⏳ Update connection string to use Supabase credentials

**Reusability**: 85% - Update connection string, SQL queries stay same

---

### ✅ src/database/schema.sql (Complete)

**Status**: Ready for Supabase migration

**Tables**:
1. **trade_ideas** - Trade plans with confidence, edges, rationale
2. **outcomes** - Trade results with P/L, R-multiples
3. **modifications** - Weekly optimization suggestions
4. **market_data_cache** - 60-second TTL cache
5. **api_calls** - API usage tracking
6. **system_events** - System logging

**Features**:
- Indexes for performance
- Views for analytics
- Foreign key constraints

**Migration**: Simple copy-paste to Supabase SQL editor

---

## What's Missing (To Build)

### 1. FastAPI Wrapper (CRITICAL - Week 1)

**File**: `src/api/main.py` (NEW)

**Needs**:
```python
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from src.agents.analysis_engine import AnalysisEngine
from src.utils.schwab_api import SchwabAPIClient
from src.utils.news_api import NewsAggregator

app = FastAPI()

class AnalysisRequest(BaseModel):
    ticker: str
    trade_type: str  # 'day', 'swing', 'both'

@app.post("/analyze")
async def analyze_ticker(request: AnalysisRequest):
    """Main analysis endpoint called by n8n"""
    # 1. Fetch data from Schwab
    # 2. Get news from NewsAggregator
    # 3. Run AnalysisEngine
    # 4. Return trade plan(s)
    pass

@app.get("/health")
async def health_check():
    return {"status": "healthy"}
```

**Time**: 2-3 hours

---

### 2. Pydantic Models (Week 1)

**File**: `src/api/models.py` (NEW)

**Needs**:
```python
from pydantic import BaseModel
from typing import List, Optional

class AnalysisRequest(BaseModel):
    ticker: str
    trade_type: str = 'both'
    timeframes: Optional[List[str]] = None

class EdgeInfo(BaseModel):
    name: str
    applied: bool
    value: Optional[float]

class TradeAnalysis(BaseModel):
    ticker: str
    trade_type: str
    direction: str
    entry: float
    stop: float
    target: float
    confidence: int
    edges: List[EdgeInfo]
    rationale: str
    risk_reward_ratio: float
```

**Time**: 1 hour

---

### 3. Supabase Migration (Week 2)

**File**: `src/database/supabase_manager.py` (NEW)

**Needs**:
```python
import os
from supabase import create_client, Client
from typing import Dict, List, Optional

class SupabaseManager:
    def __init__(self):
        url = os.getenv('SUPABASE_URL')
        key = os.getenv('SUPABASE_KEY')
        self.client: Client = create_client(url, key)

    def insert_trade_idea(self, trade_data: Dict):
        return self.client.table('trade_ideas').insert(trade_data).execute()

    # ... mirror db_manager.py methods using Supabase client
```

**Alternative**: Keep using SQL queries with `psycopg2` (PostgreSQL driver)

**Time**: 3-4 hours

---

### 4. LLM Integration (Week 1-2)

**File**: `src/utils/llm_client.py` (NEW)

**Needs**:
```python
import anthropic
from typing import Dict

class LLMClient:
    def __init__(self, api_key: str):
        self.client = anthropic.Anthropic(api_key=api_key)

    def generate_rationale(
        self,
        ticker: str,
        signals: Dict,
        news: Dict
    ) -> str:
        """Generate 2-3 sentence trade rationale"""
        prompt = f"""
        Given this trade setup for {ticker}:
        - Trend: {signals['trend_bias']}
        - Momentum: {signals['momentum_bias']}
        - Edges: {signals['edges_applied']}
        - News: {news['summary']}

        Write a 2-3 sentence rationale explaining why this is a good/bad trade.
        """

        message = self.client.messages.create(
            model="claude-3-5-sonnet-20241022",
            max_tokens=150,
            messages=[{"role": "user", "content": prompt}]
        )

        return message.content[0].text
```

**Time**: 2 hours

---

### 5. Deployment Files (Week 1)

**Dockerfile**:
```dockerfile
FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY src/ ./src/
COPY .env .env

CMD ["uvicorn", "src.api.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

**railway.json** (optional):
```json
{
  "$schema": "https://railway.app/railway.schema.json",
  "build": {
    "builder": "DOCKERFILE"
  },
  "deploy": {
    "startCommand": "uvicorn src.api.main:app --host 0.0.0.0 --port $PORT",
    "restartPolicyType": "ON_FAILURE",
    "restartPolicyMaxRetries": 10
  }
}
```

**Time**: 1 hour

---

## Requirements.txt Updates Needed

**Current**: discord.py, asyncio (not needed for API)
**Add**: FastAPI, uvicorn, psycopg2-binary (Supabase), supabase-py

**Updated requirements.txt**:
```txt
# Web Framework
fastapi==0.109.0
uvicorn[standard]==0.27.0
pydantic==2.5.3

# HTTP and API
requests==2.31.0
aiohttp==3.9.1

# Data Processing
pandas==2.1.4
numpy==1.26.2

# Technical Analysis
TA-Lib==0.4.28

# Database
psycopg2-binary==2.9.9  # PostgreSQL driver for Supabase
supabase==2.3.0  # Supabase Python client (alternative to raw psycopg2)

# LLM Integration
anthropic==0.7.8
# openai==1.6.1  # Optional if using GPT instead

# OAuth and Authentication
oauthlib==3.2.2
requests-oauthlib==1.3.1

# Environment and Configuration
python-dotenv==1.0.0

# Logging
loguru==0.7.2

# Utilities
python-dateutil==2.8.2
pytz==2023.3

# Testing
pytest==7.4.3
pytest-asyncio==0.21.1
pytest-cov==4.1.0
```

---

## Reusability Summary

| Component | Lines | Status | Reusable | Changes Needed |
|-----------|-------|--------|----------|----------------|
| **indicators.py** | 371 | ✅ Complete | 100% | None |
| **news_api.py** | 477 | ✅ Complete | 100% | None |
| **schwab_api.py** | 431 | ✅ 95% | 95% | Token persistence |
| **analysis_engine.py** | 589 | ✅ 90% | 90% | LLM integration |
| **db_manager.py** | 349 | ✅ Complete | 85% | Supabase connection |
| **schema.sql** | N/A | ✅ Complete | 100% | Copy to Supabase |
| **FastAPI wrapper** | 0 | ❌ TODO | N/A | Create new |
| **Pydantic models** | 0 | ❌ TODO | N/A | Create new |
| **LLM client** | 0 | ❌ TODO | N/A | Create new |
| **Deployment** | 0 | ❌ TODO | N/A | Create new |

**Overall**: ~90% of core trading logic is done!

---

## Recommended Approach

### Phase 1: Minimal FastAPI Wrapper (Week 1 - Days 1-3)

**Goal**: Get existing code running as API

1. Create `src/api/main.py` with `/analyze` endpoint (3 hours)
2. Create `src/api/models.py` with Pydantic schemas (1 hour)
3. Add LLM integration to `analysis_engine.py` (2 hours)
4. Update `requirements.txt` (15 min)
5. Create Dockerfile (1 hour)
6. Local testing with mock n8n requests (2 hours)

**Total**: 1-2 days

### Phase 2: Deployment (Week 1 - Days 4-5)

1. Setup Railway account (30 min)
2. Deploy Python API to Railway (1 hour)
3. Configure environment variables (30 min)
4. Test `/analyze` endpoint via Postman/curl (1 hour)
5. Setup Axiom logging (1 hour)

**Total**: 1 day

### Phase 3: Database Migration (Week 2 - Days 1-2)

1. Create Supabase database (30 min)
2. Run `schema.sql` in Supabase SQL editor (15 min)
3. Create `supabase_manager.py` OR update `db_manager.py` (3 hours)
4. Update connection strings (30 min)
5. Test CRUD operations (1 hour)

**Total**: 1 day

### Phase 4: n8n Integration (Week 2 - Days 3-5)

1. Build Discord webhook → Railway workflow (2 hours)
2. Build Supabase write nodes (1 hour)
3. Build Discord alert formatting (1 hour)
4. Create tracking cron job (15min checks) (2 hours)
5. Test end-to-end flow (2 hours)

**Total**: 2 days

### Phase 5: Learning Loop (Week 3 - Days 1-2)

1. Create weekly cron in n8n (30 min)
2. Build LLM analysis workflow (2 hours)
3. Test with historical data (1 hour)

**Total**: 1 day

### Phase 6: Testing & Polish (Week 3 - Days 3-5)

1. Unit tests for indicators (2 hours)
2. API endpoint tests (2 hours)
3. Integration tests (2 hours)
4. Documentation (2 hours)
5. User acceptance testing (2 hours)

**Total**: 2 days

---

## Risk Assessment

### Low Risk
- ✅ Indicators module (already working)
- ✅ News API (already working)
- ✅ Database schema (already designed)

### Medium Risk
- ⚠️ Schwab OAuth setup (user needs to generate auth code manually)
- ⚠️ Railway deployment (new platform, may have gotchas)
- ⚠️ n8n → Railway integration (network/CORS issues possible)

### High Risk
- 🔴 Supabase migration (SQL → PostgreSQL syntax differences possible)
- 🔴 LLM costs (rationale generation per trade = API calls)
- 🔴 Rate limiting coordination (Schwab 120/min, need to manage across requests)

---

## Conclusion

**The codebase is in EXCELLENT shape!**

- ~60% complete (not 35% as originally stated)
- Professional quality with proper architecture
- 90%+ of code can be reused as-is
- Main work is "glue code" (FastAPI wrapper, Supabase connection, n8n workflows)

**Recommended Timeline**: 2-3 weeks to fully functional bot (not 3-4)

**Next Steps**:
1. ✅ Audit complete (this document)
2. ⏳ Create FastAPI wrapper (next task)
3. ⏳ Deploy to Railway for testing
4. ⏳ Build n8n workflows
5. ⏳ Migrate to Supabase
6. ⏳ Launch & iterate

**Confidence**: HIGH - Core logic is solid, just need to wire it up!

---

**Audited by**: Claude Code (Donnie)
**Date**: 2025-11-12
**Next Review**: After FastAPI implementation
