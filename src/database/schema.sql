-- Trading Bot Database Schema
-- SQLite Schema for tracking trades, outcomes, and modifications

-- Trade Ideas Table
CREATE TABLE IF NOT EXISTS trade_ideas (
    id TEXT PRIMARY KEY,              -- e.g., 'AAPL-20231001-001'
    ticker TEXT NOT NULL,
    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
    trade_type TEXT NOT NULL,         -- 'day' or 'swing'
    direction TEXT NOT NULL,          -- 'long' or 'short'
    entry REAL NOT NULL,
    stop REAL NOT NULL,
    target REAL NOT NULL,
    target2 REAL,                     -- Optional second target (1.5R or 2R)
    confidence INTEGER NOT NULL,      -- 0-5
    rationale TEXT,
    edges_applied TEXT,               -- JSON array e.g., '["Slope Filter", "Volume Confirmation"]'
    risk_notes TEXT,
    status TEXT DEFAULT 'pending',    -- 'pending', 'active', 'closed', 'cancelled'
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,

    -- Market context at time of generation
    spy_bias TEXT,                    -- 'bullish', 'bearish', 'neutral'
    atr_value REAL,
    market_volatility TEXT,           -- 'low', 'normal', 'high'

    -- Metadata
    session_id TEXT,
    discord_user_id TEXT,
    discord_message_id TEXT
);

-- Outcomes Table
CREATE TABLE IF NOT EXISTS outcomes (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    trade_id TEXT NOT NULL REFERENCES trade_ideas(id),
    actual_outcome TEXT NOT NULL,     -- 'win', 'loss', 'breakeven', 'partial'
    profit_loss_pct REAL,             -- Percentage gain/loss
    profit_loss_r REAL,               -- R-multiple (actual vs planned)
    close_price REAL,
    close_timestamp DATETIME,
    exit_reason TEXT,                 -- 'target_hit', 'stop_hit', 'time_exit', 'manual'
    notes TEXT,

    -- Performance metrics
    hold_duration_minutes INTEGER,
    slippage_pct REAL,

    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,

    FOREIGN KEY (trade_id) REFERENCES trade_ideas(id)
);

-- Weekly Modifications Table
CREATE TABLE IF NOT EXISTS modifications (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    week TEXT NOT NULL,               -- e.g., '2023-W40'
    start_date DATE,
    end_date DATE,

    -- Performance metrics for the week
    metrics TEXT NOT NULL,            -- JSON e.g., '{"win_rate": 0.6, "avg_pl": 1.2, "total_trades": 15}'

    -- Suggested changes
    suggested_changes TEXT NOT NULL,  -- JSON array of change objects

    -- Analysis
    patterns_identified TEXT,         -- LLM-generated pattern analysis
    strengths TEXT,
    weaknesses TEXT,

    -- Status
    status TEXT DEFAULT 'pending',    -- 'pending', 'reviewed', 'applied'
    applied_at DATETIME,

    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

-- Market Data Cache Table
CREATE TABLE IF NOT EXISTS market_data_cache (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    cache_key TEXT UNIQUE NOT NULL,   -- e.g., 'AAPL_5min_20231001'
    ticker TEXT NOT NULL,
    timeframe TEXT NOT NULL,
    data TEXT NOT NULL,               -- JSON OHLCV data
    expires_at DATETIME NOT NULL,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

-- API Call Log Table
CREATE TABLE IF NOT EXISTS api_calls (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    api_name TEXT NOT NULL,           -- 'schwab', 'alpha_vantage', 'finnhub', etc.
    endpoint TEXT,
    ticker TEXT,
    status_code INTEGER,
    success BOOLEAN,
    error_message TEXT,
    response_time_ms INTEGER,
    rate_limit_remaining INTEGER,
    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
);

-- System Events Log
CREATE TABLE IF NOT EXISTS system_events (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    event_type TEXT NOT NULL,         -- 'bot_start', 'bot_stop', 'error', 'warning', 'info'
    component TEXT,                   -- 'discord', 'schwab_api', 'analysis_engine', etc.
    message TEXT NOT NULL,
    details TEXT,                     -- JSON for additional context
    severity TEXT DEFAULT 'info',     -- 'debug', 'info', 'warning', 'error', 'critical'
    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
);

-- Create Indexes for Performance
CREATE INDEX IF NOT EXISTS idx_trade_ideas_ticker ON trade_ideas(ticker);
CREATE INDEX IF NOT EXISTS idx_trade_ideas_status ON trade_ideas(status);
CREATE INDEX IF NOT EXISTS idx_trade_ideas_timestamp ON trade_ideas(timestamp);
CREATE INDEX IF NOT EXISTS idx_outcomes_trade_id ON outcomes(trade_id);
CREATE INDEX IF NOT EXISTS idx_outcomes_timestamp ON outcomes(close_timestamp);
CREATE INDEX IF NOT EXISTS idx_cache_key ON market_data_cache(cache_key);
CREATE INDEX IF NOT EXISTS idx_cache_expires ON market_data_cache(expires_at);
CREATE INDEX IF NOT EXISTS idx_api_calls_timestamp ON api_calls(timestamp);
CREATE INDEX IF NOT EXISTS idx_system_events_timestamp ON system_events(timestamp);

-- Create Views for Common Queries

-- View: Recent Performance
CREATE VIEW IF NOT EXISTS v_recent_performance AS
SELECT
    t.ticker,
    t.trade_type,
    t.direction,
    t.confidence,
    o.actual_outcome,
    o.profit_loss_r,
    o.close_timestamp,
    t.timestamp as entry_timestamp
FROM trade_ideas t
LEFT JOIN outcomes o ON t.id = o.trade_id
WHERE t.status = 'closed'
ORDER BY o.close_timestamp DESC;

-- View: Win Rate by Ticker
CREATE VIEW IF NOT EXISTS v_win_rate_by_ticker AS
SELECT
    t.ticker,
    COUNT(*) as total_trades,
    SUM(CASE WHEN o.actual_outcome = 'win' THEN 1 ELSE 0 END) as wins,
    SUM(CASE WHEN o.actual_outcome = 'loss' THEN 1 ELSE 0 END) as losses,
    ROUND(100.0 * SUM(CASE WHEN o.actual_outcome = 'win' THEN 1 ELSE 0 END) / COUNT(*), 2) as win_rate_pct,
    ROUND(AVG(o.profit_loss_r), 2) as avg_r_multiple
FROM trade_ideas t
JOIN outcomes o ON t.id = o.trade_id
GROUP BY t.ticker
HAVING COUNT(*) >= 3;

-- View: API Health
CREATE VIEW IF NOT EXISTS v_api_health AS
SELECT
    api_name,
    COUNT(*) as total_calls,
    SUM(CASE WHEN success = 1 THEN 1 ELSE 0 END) as successful_calls,
    ROUND(100.0 * SUM(CASE WHEN success = 1 THEN 1 ELSE 0 END) / COUNT(*), 2) as success_rate,
    ROUND(AVG(response_time_ms), 2) as avg_response_ms
FROM api_calls
WHERE timestamp > datetime('now', '-24 hours')
GROUP BY api_name;
