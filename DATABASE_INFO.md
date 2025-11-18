# Discord Trading Bot - Database Configuration
**Last Updated**: 2025-11-17

## Current Setup

**Supabase Project**: apps-hub (formerly discord-trading-bot)
**Schema**: `discord_trading`
**Compute**: MICRO (shared with other apps)
**Connection**: Via Railway environment variable

---

## Important Notes

⚠️ **This project now uses a SCHEMA, not the public schema!**

All tables are in: `discord_trading.*`

Example:
- ✅ `discord_trading.trade_ideas`
- ✅ `discord_trading.outcomes`
- ❌ ~~`public.trade_ideas`~~ (old, don't use)

---

## Database Schema

**Schema Name**: `discord_trading`

**Tables**:
1. `trade_ideas` - Primary trading ideas and analysis
2. `outcomes` - Trade performance tracking
3. `modifications` - Weekly learning loop adjustments
4. `market_data_cache` - Cached API responses
5. `api_calls` - API usage logging
6. `system_events` - Application event logging

**Views**:
- `v_recent_performance` - Recent trading results
- `v_win_rate_by_ticker` - Win rate statistics per ticker
- `v_api_health` - API health metrics (last 24h)

**Functions**:
- `update_updated_at_column()` - Auto-updates updated_at timestamp

---

## Connection Configuration

### Railway Environment Variables

**Required**:
```bash
DATABASE_URL=postgresql://[from-supabase]
POSTGRES_SCHEMA=discord_trading
```

The `POSTGRES_SCHEMA` variable tells the app to use the `discord_trading` schema.

---

## Python Code Configuration

**File**: `src/database/db_manager.py`

The database manager automatically uses the schema from environment:

```python
import os
import asyncpg

class DatabaseManager:
    def __init__(self):
        self.database_url = os.getenv("DATABASE_URL")
        self.schema = os.getenv("POSTGRES_SCHEMA", "discord_trading")

    async def get_connection(self):
        conn = await asyncpg.connect(self.database_url)
        # Set search path to use our schema
        await conn.execute(f"SET search_path TO {self.schema}, public")
        return conn
```

**Important**: Every database connection must set the search path!

---

## Schema Migration Details

**Date**: 2025-11-17
**Reason**: Consolidated multiple apps into one Supabase project to save costs

**Changes Made**:
1. Renamed project: `discord-trading-bot` → `apps-hub`
2. Created `discord_trading` schema
3. Moved all tables from `public` to `discord_trading`
4. Updated Railway env: added `POSTGRES_SCHEMA=discord_trading`
5. No code changes needed (handled by env var)

**Migration Script**: `migration/create_discord_trading_schema.sql`

---

## Shared Project Note

⚠️ **apps-hub is now a multi-tenant project**

Other applications in the same Supabase project:
- `deal_tracker` schema - Deal Tracker app
- (future apps added as new schemas)

**Why this matters**:
- All apps share the same MICRO compute ($10/month total)
- Each schema is isolated (can't access other schemas' tables)
- Cost-effective for multiple small apps

---

## Troubleshooting

### "Relation 'trade_ideas' does not exist"

**Cause**: Not using schema in query
**Fix**: Ensure search_path is set:
```python
await conn.execute("SET search_path TO discord_trading, public")
```

Or use fully qualified names:
```sql
SELECT * FROM discord_trading.trade_ideas;
```

---

### Connection Issues After Migration

1. Check Railway env var: `POSTGRES_SCHEMA=discord_trading`
2. Verify DATABASE_URL is correct
3. Check Railway logs for connection errors
4. Verify schema exists in Supabase:
   ```sql
   SELECT schema_name FROM information_schema.schemata
   WHERE schema_name = 'discord_trading';
   ```

---

## Related Documentation

- Main schema documentation: `C:/ClaudeAgents/kb/topics/apps-hub-supabase-project.md`
- Migration plan: `C:/ClaudeAgents/TRADING_BOT_RESTRUCTURE_PLAN.md`
- Original schema: `src/database/schema_postgres.sql`

---

**Status**: ✅ Production
**Last Verified**: 2025-11-17
