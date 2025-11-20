-- Phase II Migration for discord_trading schema
-- Simplified version for Supabase SQL Editor

-- Set schema
SET search_path TO discord_trading, public;

-- Table: trade_signals
CREATE TABLE IF NOT EXISTS trade_signals (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    trade_id VARCHAR(50) UNIQUE NOT NULL,
    ticker VARCHAR(10) NOT NULL,
    trade_type VARCHAR(10) NOT NULL CHECK (trade_type IN ('day', 'swing')),
    direction VARCHAR(10) NOT NULL CHECK (direction IN ('long', 'short')),
    entry DECIMAL(10,2) NOT NULL,
    stop DECIMAL(10,2) NOT NULL,
    target DECIMAL(10,2) NOT NULL,
    target2 DECIMAL(10,2),
    confidence INTEGER NOT NULL CHECK (confidence >= 0 AND confidence <= 5),
    edges JSONB,
    edges_count INTEGER DEFAULT 0,
    rationale TEXT,
    timeframe_signals JSONB,
    atr_value DECIMAL(10,2),
    market_volatility VARCHAR(20),
    spy_bias VARCHAR(20),
    status VARCHAR(20) DEFAULT 'PENDING' CHECK (status IN ('PENDING', 'WIN', 'LOSS', 'EXPIRED', 'CANCELLED')),
    r_achieved DECIMAL(5,2),
    created_at TIMESTAMPTZ DEFAULT NOW(),
    triggered_at TIMESTAMPTZ,
    closed_at TIMESTAMPTZ,
    expires_at TIMESTAMPTZ,
    sent_to_discord BOOLEAN DEFAULT TRUE,
    user_notes TEXT,
    flagged_for_review BOOLEAN DEFAULT FALSE,
    news_summary JSONB
);

CREATE INDEX IF NOT EXISTS idx_trade_signals_ticker ON trade_signals(ticker);
CREATE INDEX IF NOT EXISTS idx_trade_signals_status ON trade_signals(status);
CREATE INDEX IF NOT EXISTS idx_trade_signals_created_at ON trade_signals(created_at DESC);
CREATE INDEX IF NOT EXISTS idx_trade_signals_confidence ON trade_signals(confidence);
CREATE INDEX IF NOT EXISTS idx_trade_signals_trade_type ON trade_signals(trade_type);
CREATE INDEX IF NOT EXISTS idx_trade_signals_expires_at ON trade_signals(expires_at) WHERE status = 'PENDING';

-- Trigger for expiry date
CREATE OR REPLACE FUNCTION set_trade_expiry()
RETURNS TRIGGER AS $$
BEGIN
    IF NEW.expires_at IS NULL THEN
        IF NEW.trade_type = 'day' THEN
            NEW.expires_at = NEW.created_at + INTERVAL '7 days';
        ELSE
            NEW.expires_at = NEW.created_at + INTERVAL '30 days';
        END IF;
    END IF;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trade_signals_set_expiry
    BEFORE INSERT ON trade_signals
    FOR EACH ROW
    EXECUTE FUNCTION set_trade_expiry();

-- Table: weekly_reports
CREATE TABLE IF NOT EXISTS weekly_reports (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    week_start DATE NOT NULL,
    week_end DATE NOT NULL,
    week_number VARCHAR(10) NOT NULL,
    total_trades INTEGER DEFAULT 0,
    total_wins INTEGER DEFAULT 0,
    total_losses INTEGER DEFAULT 0,
    total_expired INTEGER DEFAULT 0,
    total_pending INTEGER DEFAULT 0,
    win_rate DECIMAL(5,2),
    avg_r_multiple DECIMAL(5,2),
    total_r_achieved DECIMAL(7,2),
    best_edges JSONB,
    worst_edges JSONB,
    day_trade_stats JSONB,
    swing_trade_stats JSONB,
    confidence_breakdown JSONB,
    recommendations TEXT[],
    report_json JSONB,
    report_html TEXT,
    report_markdown TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    generated_by VARCHAR(50) DEFAULT 'automated',
    CONSTRAINT unique_week_report UNIQUE (week_start, week_end)
);

CREATE INDEX IF NOT EXISTS idx_weekly_reports_week_start ON weekly_reports(week_start DESC);
CREATE INDEX IF NOT EXISTS idx_weekly_reports_created_at ON weekly_reports(created_at DESC);

-- Materialized View: edge_performance
CREATE MATERIALIZED VIEW IF NOT EXISTS edge_performance AS
SELECT
    edge->>'name' as edge_name,
    COUNT(*) as total_appearances,
    SUM(CASE WHEN status = 'WIN' THEN 1 ELSE 0 END) as wins,
    SUM(CASE WHEN status = 'LOSS' THEN 1 ELSE 0 END) as losses,
    SUM(CASE WHEN status = 'EXPIRED' THEN 1 ELSE 0 END) as expired,
    ROUND(
        (SUM(CASE WHEN status = 'WIN' THEN 1 ELSE 0 END)::DECIMAL /
         NULLIF(SUM(CASE WHEN status IN ('WIN','LOSS') THEN 1 ELSE 0 END), 0)) * 100,
        2
    ) as win_rate_pct,
    ROUND(AVG(CASE WHEN status IN ('WIN', 'LOSS') THEN r_achieved END)::numeric, 2) as avg_r_multiple,
    ROUND(MAX(CASE WHEN status IN ('WIN', 'LOSS') THEN r_achieved END)::numeric, 2) as max_r_multiple,
    ROUND(MIN(CASE WHEN status IN ('WIN', 'LOSS') THEN r_achieved END)::numeric, 2) as min_r_multiple,
    ROUND(AVG(CASE WHEN status IN ('WIN', 'LOSS') THEN confidence END)::numeric, 2) as avg_confidence,
    NOW() as last_updated
FROM trade_signals,
LATERAL jsonb_array_elements(edges) as edge
WHERE status IN ('WIN', 'LOSS', 'EXPIRED')
GROUP BY edge->>'name'
ORDER BY win_rate_pct DESC NULLS LAST, total_appearances DESC;

CREATE UNIQUE INDEX IF NOT EXISTS idx_edge_performance_name ON edge_performance(edge_name);

-- Helper Views
CREATE OR REPLACE VIEW v_recent_signals AS
SELECT
    trade_id,
    ticker,
    trade_type,
    direction,
    entry,
    stop,
    target,
    confidence,
    edges_count,
    status,
    r_achieved,
    created_at,
    closed_at,
    EXTRACT(EPOCH FROM (COALESCE(closed_at, NOW()) - created_at))/3600 as hours_duration
FROM trade_signals
WHERE created_at > NOW() - INTERVAL '30 days'
ORDER BY created_at DESC;

CREATE OR REPLACE VIEW v_pending_trades AS
SELECT
    trade_id,
    ticker,
    trade_type,
    direction,
    entry,
    stop,
    target,
    target2,
    created_at,
    expires_at,
    CASE
        WHEN NOW() > expires_at THEN true
        ELSE false
    END as is_expired
FROM trade_signals
WHERE status = 'PENDING'
ORDER BY created_at DESC;

CREATE OR REPLACE VIEW v_performance_summary AS
SELECT
    COUNT(*) as total_signals,
    SUM(CASE WHEN status = 'WIN' THEN 1 ELSE 0 END) as total_wins,
    SUM(CASE WHEN status = 'LOSS' THEN 1 ELSE 0 END) as total_losses,
    SUM(CASE WHEN status = 'PENDING' THEN 1 ELSE 0 END) as total_pending,
    SUM(CASE WHEN status = 'EXPIRED' THEN 1 ELSE 0 END) as total_expired,
    ROUND(
        (SUM(CASE WHEN status = 'WIN' THEN 1 ELSE 0 END)::DECIMAL /
         NULLIF(SUM(CASE WHEN status IN ('WIN','LOSS') THEN 1 ELSE 0 END), 0)) * 100,
        2
    ) as win_rate_pct,
    ROUND(AVG(CASE WHEN status IN ('WIN', 'LOSS') THEN r_achieved END)::numeric, 2) as avg_r_multiple,
    ROUND(SUM(CASE WHEN status IN ('WIN', 'LOSS') THEN r_achieved ELSE 0 END)::numeric, 2) as total_r_achieved,
    ROUND(AVG(confidence)::numeric, 2) as avg_confidence,
    MIN(created_at) as first_signal_date,
    MAX(created_at) as last_signal_date
FROM trade_signals;

CREATE OR REPLACE VIEW v_confidence_performance AS
SELECT
    confidence,
    COUNT(*) as total_trades,
    SUM(CASE WHEN status = 'WIN' THEN 1 ELSE 0 END) as wins,
    SUM(CASE WHEN status = 'LOSS' THEN 1 ELSE 0 END) as losses,
    ROUND(
        (SUM(CASE WHEN status = 'WIN' THEN 1 ELSE 0 END)::DECIMAL /
         NULLIF(SUM(CASE WHEN status IN ('WIN','LOSS') THEN 1 ELSE 0 END), 0)) * 100,
        2
    ) as win_rate_pct,
    ROUND(AVG(CASE WHEN status IN ('WIN', 'LOSS') THEN r_achieved END)::numeric, 2) as avg_r_multiple
FROM trade_signals
WHERE status IN ('WIN', 'LOSS', 'EXPIRED')
GROUP BY confidence
ORDER BY confidence DESC;

CREATE OR REPLACE VIEW v_ticker_performance AS
SELECT
    ticker,
    COUNT(*) as total_trades,
    SUM(CASE WHEN status = 'WIN' THEN 1 ELSE 0 END) as wins,
    SUM(CASE WHEN status = 'LOSS' THEN 1 ELSE 0 END) as losses,
    ROUND(
        (SUM(CASE WHEN status = 'WIN' THEN 1 ELSE 0 END)::DECIMAL /
         NULLIF(SUM(CASE WHEN status IN ('WIN','LOSS') THEN 1 ELSE 0 END), 0)) * 100,
        2
    ) as win_rate_pct,
    ROUND(AVG(CASE WHEN status IN ('WIN', 'LOSS') THEN r_achieved END)::numeric, 2) as avg_r_multiple,
    MAX(created_at) as last_trade_date
FROM trade_signals
WHERE status IN ('WIN', 'LOSS', 'EXPIRED')
GROUP BY ticker
HAVING COUNT(*) >= 3
ORDER BY win_rate_pct DESC NULLS LAST, total_trades DESC;

-- Helper Functions
CREATE OR REPLACE FUNCTION mark_expired_trades()
RETURNS TABLE(expired_count INTEGER) AS $$
DECLARE
    v_count INTEGER;
BEGIN
    UPDATE trade_signals
    SET status = 'EXPIRED',
        closed_at = NOW()
    WHERE status = 'PENDING'
    AND NOW() > expires_at;

    GET DIAGNOSTICS v_count = ROW_COUNT;
    expired_count := v_count;
    RETURN NEXT;
END;
$$ LANGUAGE plpgsql;

CREATE OR REPLACE FUNCTION calculate_r_multiple(
    p_direction VARCHAR,
    p_entry DECIMAL,
    p_stop DECIMAL,
    p_exit_price DECIMAL
) RETURNS DECIMAL AS $$
DECLARE
    risk DECIMAL;
    reward DECIMAL;
BEGIN
    IF p_direction = 'long' THEN
        risk = p_entry - p_stop;
        reward = p_exit_price - p_entry;
    ELSE
        risk = p_stop - p_entry;
        reward = p_entry - p_exit_price;
    END IF;

    IF risk = 0 THEN
        RETURN 0;
    END IF;

    RETURN ROUND((reward / risk)::numeric, 2);
END;
$$ LANGUAGE plpgsql;

CREATE OR REPLACE FUNCTION refresh_edge_performance()
RETURNS void AS $$
BEGIN
    REFRESH MATERIALIZED VIEW CONCURRENTLY edge_performance;
END;
$$ LANGUAGE plpgsql;
