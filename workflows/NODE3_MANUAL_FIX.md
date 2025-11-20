# Node 3 Manual Fix - n8n UI Instructions

## The Error
"JSON parameter needs to be valid JSON"

## Quick Fix in n8n UI (2 minutes)

### Step 1: Open the Node
1. Go to n8n workflow "Discord Trading Bot V3"
2. Click on **"Call FastAPI /analyze"** node

### Step 2: Configure the Request

**Method:** POST

**URL:**
```
https://discord-trading-bot-production-f596.up.railway.app/analyze
```

**Authentication:** None

### Step 3: Set Body Parameters

Scroll down to find these settings:

**Send Body:** Toggle ON (green)

**Body Content Type:** Select **"Form-Data Multipart"** OR **"Form URLEncoded"**
(Try "Form URLEncoded" first)

**Body Parameters:**
Click "Add Parameter" twice and fill in:

| Name | Value |
|------|-------|
| `ticker` | `={{ $json.ticker }}` |
| `trade_type` | `={{ $json.trade_type }}` |

### Step 4: Remove Headers (if present)
- Remove any manual Content-Type headers (n8n will auto-add)

### Step 5: Set Options
**Timeout:** 30000 (30 seconds)

### Step 6: Test
1. Click "Test step" or "Execute node"
2. Should send request to FastAPI
3. Check output for trade analysis data

---

## Alternative: Use JSON Body Type

If the above doesn't work, try this:

**Body Content Type:** JSON

**Specify Body:** Using JSON

**JSON:** Paste this exact expression:
```
={{ { "ticker": $json.ticker, "trade_type": $json.trade_type } }}
```

Make sure to include the `=` at the start!

---

## What the Request Should Look Like

When working correctly, n8n will send:
```http
POST /analyze HTTP/1.1
Host: discord-trading-bot-production-f596.up.railway.app
Content-Type: application/json

{
  "ticker": "SPY",
  "trade_type": "both"
}
```

---

## Verify It's Working

The OUTPUT from this node should show:
```json
{
  "ticker": "SPY",
  "plans": [
    {
      "trade_type": "day",
      "direction": "long",
      "entry": 580.50,
      ...
    }
  ],
  "analysis_timestamp": "..."
}
```

If you see this, Node 3 is working! ✅

---

## Still Getting Errors?

### Test FastAPI Directly
Open a terminal and run:
```bash
curl -X POST https://discord-trading-bot-production-f596.up.railway.app/analyze \
  -H "Content-Type: application/json" \
  -d '{"ticker": "SPY", "trade_type": "both"}'
```

If this works but n8n doesn't:
- The issue is with n8n configuration
- Try the alternative JSON body method above

If curl also fails:
- Check Railway logs for FastAPI service
- The backend might be down or have Schwab API issues
