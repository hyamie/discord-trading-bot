# Phase II Database Migration Instructions

**Date**: 2025-11-20
**Database**: Supabase (isjvcytbwanionrtvplq)
**Schema**: discord_trading

## Quick Migration Steps

### Option 1: Supabase SQL Editor (Recommended - 2 minutes)

1. **Open Supabase Dashboard**
   - Go to: https://app.supabase.com/project/isjvcytbwanionrtvplq
   - Navigate to: SQL Editor (left sidebar)

2. **Run Migration**
   - Click "New Query"
   - Copy contents of `database/phase2_migration_direct.sql`
   - Paste into editor
   - Click "Run" (or press Ctrl+Enter)

3. **Verify Success**
   - You should see "Success. No rows returned" message
   - Check Tables section - you should see:
     - `trade_signals`
     - `weekly_reports`
     - `edge_performance` (materialized view)
   - Check Views section - you should see:
     - `v_recent_signals`
     - `v_pending_trades`
     - `v_performance_summary`
     - `v_confidence_performance`
     - `v_ticker_performance`

### Option 2: Python Script (If connected to internet)

```bash
cd C:\ClaudeAgents\projects\discord-trading-bot
python scripts/run_phase2_migration.py
```

## What Was Created

### Tables

1. **trade_signals**
   - Primary table for logging all trade signals
   - Tracks: entry, stop, target, confidence, edges, status
   - Auto-expires based on trade type (7 days for day, 30 for swing)

2. **weekly_reports**
   - Stores generated weekly analysis reports
   - Includes: metrics, best/worst edges, recommendations

### Materialized View

1. **edge_performance**
   - Aggregated performance stats by edge
   - Shows: win rate, avg R-multiple, total appearances
   - Needs manual refresh: `SELECT refresh_edge_performance();`

### Helper Views

1. **v_recent_signals** - Last 30 days of signals
2. **v_pending_trades** - Trades awaiting outcome
3. **v_performance_summary** - All-time performance metrics
4. **v_confidence_performance** - Win rate by confidence level
5. **v_ticker_performance** - Performance by ticker (3+ trades)

### Functions

1. **mark_expired_trades()** - Auto-expires pending trades past expiry date
2. **calculate_r_multiple()** - Calculate R-multiple for trade outcome
3. **refresh_edge_performance()** - Refresh materialized view
4. **set_trade_expiry()** - Trigger: Auto-set expiry date on insert

## Verification Queries

After migration, run these to verify:

```sql
-- Check tables exist
SELECT table_name
FROM information_schema.tables
WHERE table_schema = 'discord_trading'
AND table_name IN ('trade_signals', 'weekly_reports')
ORDER BY table_name;

-- Check materialized view
SELECT matviewname
FROM pg_matviews
WHERE schemaname = 'discord_trading';

-- Check helper views
SELECT table_name
FROM information_schema.views
WHERE table_schema = 'discord_trading'
AND table_name LIKE 'v_%'
ORDER BY table_name;

-- Check functions
SELECT routine_name
FROM information_schema.routines
WHERE routine_schema = 'discord_trading'
AND routine_type = 'FUNCTION';
```

## Next Steps After Migration

1. Test trade signal logging:
   ```python
   python scripts/test_trade_logger.py
   ```

2. Run the FastAPI with new logging:
   ```bash
   python src/api/main.py
   ```

3. Test /analyze endpoint:
   ```bash
   curl -X POST http://localhost:8000/analyze \
     -H "Content-Type: application/json" \
     -d '{"ticker": "AAPL", "trade_type": "day"}'
   ```

4. Verify trade was logged:
   ```sql
   SELECT * FROM discord_trading.trade_signals
   ORDER BY created_at DESC
   LIMIT 1;
   ```

## Troubleshooting

### Error: "schema discord_trading does not exist"

**Fix**: Create schema first:
```sql
CREATE SCHEMA IF NOT EXISTS discord_trading;
```

### Error: "permission denied for schema"

**Fix**: Grant permissions:
```sql
GRANT USAGE ON SCHEMA discord_trading TO authenticated;
GRANT ALL ON ALL TABLES IN SCHEMA discord_trading TO authenticated;
```

### Error: "relation already exists"

**Solution**: Tables already created, migration successful!

## Rollback (If Needed)

To remove Phase II tables:

```sql
DROP TABLE IF EXISTS discord_trading.trade_signals CASCADE;
DROP TABLE IF EXISTS discord_trading.weekly_reports CASCADE;
DROP MATERIALIZED VIEW IF EXISTS discord_trading.edge_performance CASCADE;
DROP FUNCTION IF EXISTS discord_trading.mark_expired_trades();
DROP FUNCTION IF EXISTS discord_trading.calculate_r_multiple(VARCHAR, DECIMAL, DECIMAL, DECIMAL);
DROP FUNCTION IF EXISTS discord_trading.refresh_edge_performance();
DROP FUNCTION IF EXISTS discord_trading.set_trade_expiry();
```

## Migration Status

- [x] Migration SQL created
- [ ] Migration executed (Run Option 1 or 2 above)
- [ ] Verified tables exist
- [ ] Tested trade logging
- [ ] FastAPI updated

**When complete, proceed to**: Step 2 - Create trade_logger.py module
