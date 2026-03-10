-- 003_price_snapshots.sql
-- Migración: Tabla para snapshots de precios por usuario

BEGIN;

-- Tabla para snapshots de precios (comparación de tendencias en /ver)
CREATE TABLE IF NOT EXISTS user_price_snapshots (
    user_id BIGINT,
    symbol VARCHAR(20) NOT NULL,
    price DECIMAL(18,8) NOT NULL,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    PRIMARY KEY (user_id, symbol)
);

CREATE INDEX IF NOT EXISTS idx_user_price_snapshots_user_id ON user_price_snapshots(user_id);
CREATE INDEX IF NOT EXISTS idx_user_price_snapshots_symbol ON user_price_snapshots(symbol);

-- Trigger para actualizar updated_at
CREATE TRIGGER update_user_price_snapshots_updated_at
    BEFORE UPDATE ON user_price_snapshots
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

COMMIT;
