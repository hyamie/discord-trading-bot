# Project Context - Discord Trading Bot

**Project:** Automated Trading Signals Discord Bot
**Last Updated:** 2025-11-12
**Status:** APPROVED - Starting Implementation (Hybrid Architecture)

---

## Current Goal

Re-evaluate Discord Trading Bot architecture based on NEW constraints:
- User already paying for n8n Cloud (~$20/month) - SUNK COST
- User already paying for Supabase (~$25/month) - SUNK COST
- Docker Desktop installed locally (free)

**Recommendation:** HYBRID ARCHITECTURE (n8n Cloud + Railway Python Microservice)

---

## Architecture Overview

### RECOMMENDED: Hybrid (n8n Cloud + Railway Python Microservice)

**Separation of Concerns:**
- **n8n Cloud:** Orchestration (webhooks, workflow logic, DB writes, notifications)
- **Railway Python API:** Compute (MTF analysis, technical indicators, trade plans)
- **Supabase PostgreSQL:** Data layer (trade ideas, outcomes, cache)

**Data Flow:**
```
Discord webhook → n8n Cloud → Railway /analyze API
                           ↓
                    Return analysis JSON
                           ↓
              n8n logic (confidence >= 3?)
                           ↓
              Supabase write + Discord alert
```

**Incremental Cost:** $5-7/month (Railway hosting)
**Uses Existing:** n8n Cloud + Supabase (NOT wasted)

### PREVIOUS: Pure Python (Rejected)

**Why Rejected:** Would waste $20/month n8n subscription while paying $5-7/month for Railway anyway. Better to use BOTH for same price.

---

## Recent Changes

### 2025-11-12: CRITICAL - Architecture Revision
- **What:** Re-analyzed architecture with new cost constraints (n8n + Supabase already paid)
- **Why:** Original Pure Python recommendation would WASTE n8n subscription
- **Decision:** Hybrid (n8n + Railway) uses ALL subscriptions for same $5-7/month cost
- **Outcome:** Created `ARCHITECTURE_REVISION.md` (comprehensive analysis)
- **Next:** Awaiting user approval before proceeding

### 2025-11-09: Pure Python Implementation Started (35% Complete)
- **What:** Started building Pure Python bot (SQLite, discord.py, standalone)
- **Status:** Database schema, indicators, Schwab API client completed
- **Issue:** Need to REFACTOR to hybrid if approved (SQLite → Supabase, monolith → FastAPI)
- **Outcome:** Reusable code (indicators.py can be kept as-is)

---

## Current State

**What's Working:**
- ✅ Architecture re-analysis complete (Sequential Thinking MCP used)
- ✅ Comprehensive revision document created (`ARCHITECTURE_REVISION.md`)
- ✅ Migration path documented (SQLite → Supabase, monolith → FastAPI)
- ✅ Existing code can be reused (indicators.py, schwab_api.py with minor updates)

**Known Issues:**
- ⚠️ Original implementation used SQLite (need Supabase migration)
- ⚠️ Original implementation is monolithic (need FastAPI refactor)
- ⚠️ No deployment config yet (need Railway Procfile, env vars)
- ⏳ Awaiting user approval for hybrid architecture

**Next Steps (IF APPROVED):**
1. Refactor to FastAPI microservice (`src/main.py` with `/analyze` endpoint)
2. Migrate database from SQLite to Supabase PostgreSQL
3. Deploy Python API to Railway
4. Build n8n workflow (Discord webhook → Railway → Supabase → Discord alert)
5. Create cron jobs (trade tracking every 15min, weekly learning loop)

---

## Key Decisions

### CRITICAL: Hybrid Architecture (2025-11-12)
**Question:** Which architecture given sunk costs (n8n, Supabase already paid)?

**Options Evaluated:**
1. Pure Python (Railway) - $5-7/month, WASTES n8n
2. n8n-only - $0/month, but TA logic awkward in JavaScript
3. **Hybrid (n8n + Railway)** - $5-7/month, uses ALL subscriptions ⭐ RECOMMENDED
4. Hybrid (n8n + local Docker) - $0-10/month, PC must run 24/7
5. Pure Python (local Docker) - $0-10/month, WASTES n8n, PC dependency

**Decision:** Hybrid (n8n Cloud + Railway Python microservice)

**Reasoning:**
- Same incremental cost as pure Python ($5-7/month)
- Uses existing n8n subscription (not wasted)
- Cloud reliability (Railway ~99.9% uptime vs local PC ~95-98%)
- Clean separation of concerns (orchestration vs compute)
- Visual workflow modifications in n8n GUI
- Testable Python TA logic with proper libraries

**Alternatives Rejected:**
- Local Docker: Reliability concerns for trading signals (PC downtime risk)
- n8n-only: Complex MTF analysis better in Python with pandas-ta

### Supabase over SQLite (2025-11-12)
**Decision:** Use Supabase PostgreSQL (not SQLite)

**Reasoning:**
- Already paying for Supabase (~$25/month)
- PostgreSQL better for analytics (window functions, CTEs)
- Managed backups, point-in-time recovery
- n8n native integration (Supabase node)

---

## Team Preferences

- Python for complex TA logic (pandas-ta, TA-Lib)
- n8n for orchestration (visual workflows, easy modifications)
- Managed services over self-hosted (Railway, Supabase)
- Cloud hosting over local 24/7 PC (reliability)
- Git version control (GitHub auto-deploy to Railway)

---

## Dependencies

**Existing (Sunk Costs - Already Paid):**
- n8n Cloud: ~$20/month
- Supabase: ~$25/month (PostgreSQL available)
- Docker Desktop: $0 (free for personal use, installed locally)

**New (To Add):**
- Railway: $5-7/month (Python microservice hosting)

**API Keys Needed:**
- Discord Bot Token (free)
- Schwab API Key + Secret (approved, free)
- Finnhub API Key (free tier, optional)
- NewsAPI Key (free tier, optional)
- OpenAI or Anthropic API Key (for LLM rationale generation, optional)

**Tech Stack:**
- Backend: Python 3.11+, FastAPI, pandas, pandas-ta
- Database: Supabase PostgreSQL
- Orchestration: n8n Cloud
- Hosting: Railway (Python API)
- Version Control: GitHub

---

## Notes for Agents

**CRITICAL - Read Before Proceeding:**
1. **Check `ARCHITECTURE_REVISION.md` first** (comprehensive analysis, decision matrix, migration path)
2. **Wait for user approval** before refactoring (hybrid architecture not yet confirmed)
3. **Migration documented** in ARCHITECTURE_REVISION.md (SQLite → Supabase, monolith → FastAPI)
4. **Reusable code:** `indicators.py` (keep as-is), `schwab_api.py` (update token storage)

**Important Files:**
- **ARCHITECTURE_REVISION.md** - THIS SESSION, comprehensive analysis
- **IMPLEMENTATION_PROGRESS.md** - Original pure Python status (35% complete)
- **Trading Workflow V2.md** - Framework design (3-Tier MTF)
- **doc/task/context.md** - THIS FILE (single source of truth)

**Open Questions for User:**
1. Approve hybrid architecture? (Or prefer alternative?)
2. What Supabase plan? (Confirm PostgreSQL access)
3. What n8n plan? (Starter has webhook limits)
4. Is PC already running 24/7? (Affects cost analysis)
