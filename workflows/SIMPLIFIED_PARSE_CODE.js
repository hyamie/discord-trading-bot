// SIMPLIFIED Parse Ticker Code - Always returns 'both' trade type
// For n8n "Parse Ticker & Trade Type" node

// Get the message content
const content = $input.item.json.body.content || '';

// Ignore bot messages
if ($input.item.json.body.author?.bot) {
  return [];
}

// Extract ticker - support $SPY or !ticker SPY formats
let ticker = null;

if (content.startsWith('$')) {
  // Format: $SPY
  ticker = content.substring(1).toUpperCase().trim();
} else if (content.toLowerCase().startsWith('!ticker ')) {
  // Format: !ticker SPY
  ticker = content.substring(8).toUpperCase().trim();
}

// If no ticker found, stop processing
if (!ticker) {
  return [];
}

// Remove any extra text after the ticker (just get the symbol)
ticker = ticker.split(' ')[0];

// Validate ticker is 1-5 letters
if (!/^[A-Z]{1,5}$/.test(ticker)) {
  return [];
}

// ALWAYS return 'both' - no need to parse trade type
return [{
  json: {
    ticker: ticker,
    trade_type: 'both',
    channel_id: $input.item.json.body.channel_id,
    message_id: $input.item.json.body.id,
    author: $input.item.json.body.author?.username || 'Unknown'
  }
}];
