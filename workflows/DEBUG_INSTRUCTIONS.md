# Debug Instructions - Parse Ticker Node Still Returning No Output

## What I Changed
Simplified the code to:
1. Remove complex regex matching
2. Always return `trade_type: 'both'`
3. Use simple string operations only
4. Better validation

## The New Code
Located in: `SIMPLIFIED_PARSE_CODE.js` and updated in the workflow JSON.

Key changes:
- Removed regex: `content.toUpperCase().match(/(?:^|\\s)(?:\\$|!ticker\\s+)?([A-Z]{1,5})(?:\\s|$)/)`
- Now uses simple: `content.startsWith('$')` and `content.substring(1)`
- Always returns `'both'` for trade_type

## Next Steps to Debug in n8n

### Step 1: Check the Webhook Input
1. Go to n8n → "Discord Trading Bot V3" workflow
2. Click on the **Webhook** node (first node)
3. Look at the OUTPUT from the last execution
4. Verify you see: `"body": { "content": "$SPY", "author": { ... } }`

**If you DON'T see this**: The Discord bot isn't sending data correctly.

### Step 2: Test the Parse Node Directly
1. Click on the **"Parse Ticker & Trade Type"** node
2. Click the **"Execute step"** button (top right, red button with play icon)
3. Look at what it outputs

**Expected output**:
```json
{
  "ticker": "SPY",
  "trade_type": "both",
  "channel_id": "...",
  "message_id": "...",
  "author": "..."
}
```

**If you see "No output"**: There's a code issue we need to debug further.

### Step 3: Add Debug Logging
Replace the code in the Parse Ticker node with this DEBUG version:

```javascript
// DEBUG VERSION - Logs everything
const content = $input.item.json.body.content || '';

console.log('=== DEBUG START ===');
console.log('Content:', content);
console.log('Full input:', JSON.stringify($input.item.json, null, 2));
console.log('Author bot?', $input.item.json.body.author?.bot);

// Ignore bot messages
if ($input.item.json.body.author?.bot) {
  console.log('Skipping: is bot');
  return [];
}

// Extract ticker
let ticker = null;

if (content.startsWith('$')) {
  ticker = content.substring(1).toUpperCase().trim();
  console.log('Extracted ticker from $:', ticker);
} else if (content.toLowerCase().startsWith('!ticker ')) {
  ticker = content.substring(8).toUpperCase().trim();
  console.log('Extracted ticker from !ticker:', ticker);
} else {
  console.log('Content does not match expected format');
}

if (!ticker) {
  console.log('No ticker found, returning empty');
  return [];
}

// Clean ticker
ticker = ticker.split(' ')[0];
console.log('Cleaned ticker:', ticker);

// Validate
if (!/^[A-Z]{1,5}$/.test(ticker)) {
  console.log('Ticker validation failed:', ticker);
  return [];
}

const result = [{
  json: {
    ticker: ticker,
    trade_type: 'both',
    channel_id: $input.item.json.body.channel_id,
    message_id: $input.item.json.body.id,
    author: $input.item.json.body.author?.username || 'Unknown'
  }
}];

console.log('Returning:', JSON.stringify(result, null, 2));
console.log('=== DEBUG END ===');

return result;
```

### Step 4: Check n8n Execution Logs
After running with debug code:
1. Click "Executions" tab in n8n
2. Find the latest execution
3. Click on it to see details
4. Look for console.log output
5. Share what you see

## Alternative: Test with Curl

Test the webhook directly without Discord:

```bash
curl -X POST https://hyamie.app.n8n.cloud/webhook/7c5a5975-6273-4a10-bf2b-c43b830b0975 \
  -H "Content-Type: application/json" \
  -d '{"body": {"content": "$SPY", "author": {"bot": false, "username": "TestUser"}, "channel_id": "123456", "id": "789"}}'
```

This should trigger the workflow. Check:
1. Does the webhook receive it?
2. Does the Parse node output data?
3. Does it call the FastAPI?

## Possible Issues

### Issue 1: Data Structure Mismatch
The Discord bot sends: `{ body: { content: "$SPY" } }`
The node expects: `$input.item.json.body.content`

If this is mismatched, the node won't find the data.

### Issue 2: n8n Code Node Settings
Check the node settings:
- **Mode**: Should be "Run Once for All Items"
- **Language**: JavaScript
- **Code**: Should match the simplified version

### Issue 3: Workflow Not Activated
Make sure the workflow toggle in n8n is ON (blue/green).

## Import the Updated Workflow

The updated workflow is at:
`C:\ClaudeAgents\projects\discord-trading-bot\workflows\discord_trading_bot_v3_webhook.json`

Re-import it:
1. Export your current workflow as backup
2. Delete the current workflow
3. Import the new JSON file
4. Verify webhook URL is correct
5. Activate

## What to Share
If still stuck, share:
1. Screenshot of the Webhook node OUTPUT
2. Screenshot of the Parse Ticker node INPUT and OUTPUT
3. Any console.log messages from execution logs
4. The error message you see in Discord
