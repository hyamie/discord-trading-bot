# FIXED: Double Body Nesting Issue

## The Real Problem
The Discord bot sends data with **double nesting**:
```json
{
  "body": {
    "body": {
      "content": "$spy",
      "author": {...}
    }
  }
}
```

The code was looking at:
- `$input.item.json.body.content` ❌ (doesn't exist)

But should look at:
- `$input.item.json.body.body.content` ✅ (correct path)

## The Fix
Changed the first line to handle both cases:
```javascript
const data = $input.item.json.body.body || $input.item.json.body;
const content = data.content || '';
```

This tries `body.body` first, then falls back to just `body` if it doesn't exist.

All references changed from:
- `$input.item.json.body.content` → `data.content`
- `$input.item.json.body.author` → `data.author`
- `$input.item.json.body.channel_id` → `data.channel_id`
- etc.

## How to Apply

### In n8n (Quick Fix):
1. Open "Parse Ticker & Trade Type" node
2. Replace the **first two lines** with:
   ```javascript
   const data = $input.item.json.body.body || $input.item.json.body;
   const content = data.content || '';
   ```
3. Replace all instances of `$input.item.json.body.` with just `data.`
4. Save and test

### Or Re-import:
1. Import the updated workflow from:
   `C:\ClaudeAgents\projects\discord-trading-bot\workflows\discord_trading_bot_v3_webhook.json`
2. Test with `$SPY` in Discord

## Test Command
Send in Discord: `$SPY`

Expected output in Parse Ticker node:
```json
{
  "ticker": "SPY",
  "trade_type": "both",
  "channel_id": "1435346210801061899",
  "message_id": "...",
  "author": "hyamie"
}
```

## Why This Happened
The Discord bot code wraps the message in a `body` object:
```python
payload = {
    'body': {  # <-- First body (for n8n compatibility)
        'content': message.content,
        'author': {...},
        ...
    }
}
```

But n8n's webhook automatically wraps incoming data in another `body`:
```json
{
  "body": {  # <-- Second body (added by n8n webhook)
    "body": {  # <-- First body (from Discord bot)
      "content": "$spy"
    }
  }
}
```

This is why we see `body.body` in the data structure!
