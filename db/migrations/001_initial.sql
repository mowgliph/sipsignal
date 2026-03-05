-- 001_initial.sql - Schema inicial de SipSignal
-- Tablas: signals, active_trades, user_config, drawdown_tracker

BEGIN;

-- Tabla de señales trades
CREATE TABLE IF NOT EXISTS signals (
    id SERIAL PRIMARY KEY,
    detected_at TIMESTAMPTZ NOT NULL,
    direction VARCHAR(5) NOT NULL CHECK (direction IN ('LONG', 'SHORT')),
    entry_price DECIMAL(12,2),
    tp1_level DECIMAL(12,2),
    sl_level DECIMAL(12,2),
    rr_ratio DECIMAL(5,3),
    atr_value DECIMAL(12,2),
    timeframe VARCHAR(5) NOT NULL,
    status VARCHAR(20) DEFAULT 'EMITIDA' CHECK (status IN ('EMITIDA', 'TOMADA', 'CERRADA', 'CANCELADA')),
    taken_at TIMESTAMPTZ,
    tp1_hit BOOLEAN DEFAULT FALSE,
    tp1_hit_at TIMESTAMPTZ,
    sl_moved_to_breakeven BOOLEAN DEFAULT FALSE,
    close_price DECIMAL(12,2),
    close_at TIMESTAMPTZ,
    result VARCHAR(15) CHECK (result IN ('GANADA', 'PERDIDA', 'BREAKEVEN', NULL)),
    pnl_usdt DECIMAL(10,2),
    pnl_percent DECIMAL(6,3),
    supertrend_exit BOOLEAN DEFAULT FALSE,
    ai_context TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_signals_detected_at ON signals(detected_at);
CREATE INDEX IF NOT EXISTS idx_signals_status ON signals(status);
CREATE INDEX IF NOT EXISTS idx_signals_direction ON signals(direction);
CREATE INDEX IF NOT EXISTS idx_signals_timeframe ON signals(timeframe);

-- Tabla de trades activos
CREATE TABLE IF NOT EXISTS active_trades (
    id SERIAL PRIMARY KEY,
    signal_id INT NOT NULL REFERENCES signals(id) ON DELETE CASCADE,
    direction VARCHAR(5) NOT NULL CHECK (direction IN ('LONG', 'SHORT')),
    entry_price DECIMAL(12,2) NOT NULL,
    tp1_level DECIMAL(12,2),
    sl_level DECIMAL(12,2),
    status VARCHAR(20) DEFAULT 'ABIERTO' CHECK (status IN ('ABIERTO', 'CERRADO', 'PAUSADO')),
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_active_trades_signal_id ON active_trades(signal_id);
CREATE INDEX IF NOT EXISTS idx_active_trades_status ON active_trades(status);

-- Tabla de configuración de usuarios
CREATE TABLE IF NOT EXISTS user_config (
    user_id BIGINT PRIMARY KEY,
    capital_total DECIMAL(12,2) NOT NULL DEFAULT 1000.00,
    risk_percent DECIMAL(4,2) NOT NULL DEFAULT 1.00,
    max_drawdown_percent DECIMAL(4,2) NOT NULL DEFAULT 5.00,
    direction VARCHAR(10) DEFAULT 'LONG' CHECK (direction IN ('LONG', 'SHORT', 'AMBOS')),
    timeframe_primary VARCHAR(5) DEFAULT '15m',
    setup_completed BOOLEAN DEFAULT FALSE,
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Tabla de seguimiento de drawdown
CREATE TABLE IF NOT EXISTS drawdown_tracker (
    user_id BIGINT PRIMARY KEY REFERENCES user_config(user_id) ON DELETE CASCADE,
    current_drawdown_usdt DECIMAL(10,2) DEFAULT 0.00,
    current_drawdown_percent DECIMAL(5,3) DEFAULT 0.000,
    losses_count INT DEFAULT 0,
    last_reset_at TIMESTAMPTZ,
    is_paused BOOLEAN DEFAULT FALSE,
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Trigger para actualizar updated_at
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER update_signals_updated_at BEFORE UPDATE ON signals
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_active_trades_updated_at BEFORE UPDATE ON active_trades
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_user_config_updated_at BEFORE UPDATE ON user_config
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_drawdown_tracker_updated_at BEFORE UPDATE ON drawdown_tracker
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

COMMIT;
