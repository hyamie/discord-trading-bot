# Node 3 Fix - Call FastAPI /analyze

## The Problem
The HTTP Request node was using old n8n expression syntax that doesn't properly send the JSON body:
```json
"jsonBody": "={\n  \"ticker\": \"{{ $json.ticker }}\",\n  \"trade_type\": \"{{ $json.trade_type }}\"\n}"
```

This was causing the FastAPI to return: **"Field required"** error.

## The Fix
Changed to use n8n's proper JSON Parameters format:

**OLD (broken):**
```json
"sendBody": true,
"contentType": "json",
"jsonBody": "={\n  \"ticker\": \"{{ $json.ticker }}\",\n  \"trade_type\": \"{{ $json.trade_type }}\"\n}"
```

**NEW (fixed):**
```json
"sendBody": true,
"specifyBody": "json",
"jsonParameters": {
  "parameters": [
    {
      "name": "ticker",
      "value": "={{ $json.ticker }}"
    },
    {
      "name": "trade_type",
      "value": "={{ $json.trade_type }}"
    }
  ]
}
```

## How to Apply in n8n

### Option 1: Re-import Workflow (Easiest)
1. Import the updated workflow:
   `C:\ClaudeAgents\projects\discord-trading-bot\workflows\discord_trading_bot_v3_webhook.json`
2. Test with `$SPY` in Discord

### Option 2: Manual Fix in n8n UI
1. Click on "Call FastAPI /analyze" node
2. Scroll down to **"Specify Body"** section
3. Change from "Using Fields Below" or "JSON" to **"Using Fields Below"**
4. Under **Body Parameters**, add:
   - **Name**: `ticker`, **Value**: `={{ $json.ticker }}`
   - **Name**: `trade_type`, **Value**: `={{ $json.trade_type }}`
5. Make sure "Send Body" is enabled
6. Save

## What This Sends to FastAPI
The corrected configuration will send:
```json
POST https://discord-trading-bot-production-f596.up.railway.app/analyze
Content-Type: application/json

{
  "ticker": "SPY",
  "trade_type": "both"
}
```

## Expected Response
If FastAPI is working, it should return trade analysis with:
```json
{
  "ticker": "SPY",
  "plans": [
    {
      "trade_type": "day",
      "direction": "long",
      "entry": 580.50,
      "stop": 578.25,
      ...
    },
    {
      "trade_type": "swing",
      ...
    }
  ],
  "analysis_timestamp": "2025-11-20T..."
}
```

## Troubleshooting

### If FastAPI still returns error:
1. Test FastAPI directly with curl:
   ```bash
   curl -X POST https://discord-trading-bot-production-f596.up.railway.app/analyze \
     -H "Content-Type: application/json" \
     -d '{"ticker": "SPY", "trade_type": "both"}'
   ```

2. Check Railway logs for the FastAPI service to see what error it's receiving

### If FastAPI timeout (30 seconds):
- This is normal for first request (cold start)
- The analysis can take 15-20 seconds for complex calculations
- Consider increasing timeout to 60 seconds in node options

## Progress
✅ Node 1: Webhook - Working
✅ Node 2: Parse Ticker - Fixed (double body nesting)
✅ Node 3: Call FastAPI - Fixed (JSON parameters)
⏳ Node 4: Format Discord Response - Next to test
⏳ Node 5: Respond to Webhook - Next to test
