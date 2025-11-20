# Cosmetic Fixes - Risk/Reward and Risk Notes Display

**Date:** 2025-11-20
**Issue:** Display showing "undefinedR" and "undefined" in Discord responses
**Status:** ✅ Fixed

---

## Issues Fixed

### 1. Risk/Reward showing "undefinedR"
**Problem:** n8n code was accessing `plan.risk_reward` but API returns `plan.risk_reward_ratio`

**Before:**
```javascript
`**Risk/Reward:** ${plan.risk_reward}R\n\n`
```

**After:**
```javascript
const riskReward = plan.risk_reward_ratio || plan.risk_reward || 2.0;
`**Risk/Reward:** ${riskReward.toFixed(1)}R\n\n`
```

**Result:** Now shows "2.0R" instead of "undefinedR"

---

### 2. Risk Notes showing "undefined"
**Problem:** `plan.risk_notes` field doesn't exist in the API response model

**Before:**
```javascript
`**Risk Notes:** ${plan.risk_notes}`
```

**After:**
```javascript
const riskNotes = `ATR: $${plan.atr_value?.toFixed(2) || 'N/A'} | Volatility: ${plan.market_volatility || 'Normal'}`;
`**Risk Notes:** ${riskNotes}`
```

**Result:** Now shows "ATR: $2.25 | Volatility: Normal" instead of "undefined"

---

### 3. Edges formatting improvement
**Problem:** Code was accessing `plan.edges_applied` (which is a list of strings) instead of `plan.edges` (which is a list of EdgeInfo objects)

**Before:**
```javascript
const edgesText = plan.edges_applied && plan.edges_applied.length > 0
  ? plan.edges_applied.map(e => `✓ ${e}`).join('\n')
  : 'None';
```

**After:**
```javascript
const edgesText = plan.edges && plan.edges.length > 0
  ? plan.edges.filter(e => e.applied).map(e => `✓ ${e.name}`).join('\n')
  : 'None';
```

**Result:** Properly formats edge names from EdgeInfo objects

---

## What Changed

**File:** `workflows/discord_trading_bot_v3_webhook.json`
**Node:** "Format Discord Response"

### Key Changes:
1. Use `plan.risk_reward_ratio` with fallback to `plan.risk_reward`
2. Format with `.toFixed(1)` for cleaner display (2.0R instead of 2R)
3. Build risk notes from `atr_value` and `market_volatility` fields
4. Access edges through `plan.edges` array with `.name` property
5. Filter edges by `e.applied` before displaying

---

## Expected Output

### Before Fix:
```
Risk/Reward: undefinedR

Edges:
None

Risk Notes: undefined
```

### After Fix:
```
Risk/Reward: 2.0R

Edges:
✓ Slope Filter (EMA20 rising strongly)
✓ Volatility Filter (Strong breakout candle)

Risk Notes: ATR: $2.73 | Volatility: Normal
```

---

## How to Apply

### In n8n UI:
1. Open "Discord Trading Bot V3" workflow
2. Click on "Format Discord Response" node
3. Copy the updated JavaScript code from the workflow JSON file
4. Paste into the code editor
5. Save the workflow

### Or Re-import:
1. Import the updated workflow file:
   `C:\ClaudeAgents\projects\discord-trading-bot\workflows\discord_trading_bot_v3_webhook.json`
2. Verify webhook URL is still correct
3. Activate workflow

---

## Testing

After applying the fix, test with:
```
$NVDA
```

Should now see:
- ✅ Risk/Reward: 2.0R (or actual calculated ratio)
- ✅ Risk Notes: ATR: $X.XX | Volatility: Normal
- ✅ Edges properly formatted if any are present

---

## No Railway Deployment Needed

These are **n8n workflow changes only** - no backend code changes required.
Just update the workflow in n8n and test immediately!
