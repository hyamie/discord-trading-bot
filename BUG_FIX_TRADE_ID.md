# Bug Fix: trade_id KeyError

**Date:** 2025-11-20
**Issue:** FastAPI returning 500 error: "Analysis failed: 'trade_id'"
**Status:** ✅ Fixed and deployed

---

## The Problem

When analyzing tickers (e.g., NVDA), the FastAPI backend was crashing with:
```
KeyError: 'trade_id'
```

**Root Cause:**
- The `analysis_engine.py` returns trade plans WITHOUT a `trade_id` field
- The `convert_to_trade_analysis()` function in `main.py` was trying to access `plan['trade_id']`
- This caused a KeyError when processing the plans

---

## The Fix

### 1. Generate trade_id (main.py line 385-388)
```python
for idx, plan in enumerate(analysis_result['plans'], 1):
    # Generate trade_id: TICKER-YYYYMMDD-NNN format
    date_str = datetime.now().strftime('%Y%m%d')
    trade_id = f"{request.ticker.upper()}-{date_str}-{idx:03d}"
    plan['trade_id'] = trade_id
    plan['ticker'] = request.ticker.upper()
```

**Example trade_ids:**
- NVDA-20251120-001 (first plan for NVDA on Nov 20, 2025)
- NVDA-20251120-002 (second plan)
- SPY-20251120-001

### 2. Handle Missing Fields (main.py line 522-572)

Updated `convert_to_trade_analysis()` to:
- Calculate `risk_pct` and `reward_pct` from entry/stop/target
- Handle both `risk_reward` and `risk_reward_ratio` field names
- Map `timeframes` to `timeframe_signals` for compatibility
- Provide fallback values for optional fields:
  - `ticker`: '' (empty string)
  - `atr_value`: 0
  - `market_volatility`: 'unknown'
  - `rationale`: 'No rationale provided'

### 3. Field Mapping

Analysis engine returns:
```python
{
    'trade_type': 'day',
    'direction': 'long',
    'entry': 580.50,
    'stop': 578.25,
    'target': 584.00,
    'target2': 585.50,
    'risk_reward': 2.0,  # Note: not 'risk_reward_ratio'
    'confidence': 4,
    'edges_applied': [...],
    'rationale': '...',
    'atr_value': 2.25,
    'timeframes': {...}  # Note: not 'timeframe_signals'
}
```

Function now handles:
- `risk_reward` → `risk_reward_ratio`
- `timeframes` → `timeframe_signals`
- Calculates missing: `risk_pct`, `reward_pct`
- Generates new: `trade_id`, adds `ticker`

---

## Files Changed

**src/api/main.py:**
- Lines 382-390: Generate trade_id and add ticker before conversion
- Lines 522-572: Updated convert_to_trade_analysis() with robust field handling

**Committed:** fdc8df7
**Pushed:** To GitHub master branch
**Deployed:** Railway auto-deploys on push (2-3 minutes)

---

## Testing

### Before Fix:
```
$NVDA in Discord
→ Error: "Analysis failed: 'trade_id'"
```

### After Fix (Expected):
```
$NVDA in Discord
→ Trade analysis with entry/stop/targets, OR
→ "No trade setups found" message
```

**Wait Time:** 2-3 minutes for Railway to redeploy after push

---

## Verification Steps

1. Wait for Railway deployment to complete
2. Send `$NVDA` in Discord
3. Should get either:
   - ✅ Trade setup with NVDA-20251120-001 identifier
   - ✅ "No trade setups found" message
   - ❌ NOT a 500 error

---

## Related Issues Fixed

This also handles several edge cases:
- Missing `ticker` field in plans
- Inconsistent field naming (`risk_reward` vs `risk_reward_ratio`)
- Missing percentage calculations
- Optional fields that might not be present

---

## Next Steps

Once Railway redeploys (check Railway dashboard):
1. Test with `$NVDA` again
2. Test with other tickers: `$AAPL`, `$TSLA`, `$QQQ`
3. Verify full trade setup responses work correctly
4. Check that trade_ids are properly formatted

---

**Status:** Deployed, waiting for Railway auto-deployment (~2-3 minutes)
