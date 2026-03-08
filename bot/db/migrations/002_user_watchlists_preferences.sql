-- 002_user_watchlists_preferences.sql
-- Migración: Tablas para watchlists, preferencias y estadísticas de uso

BEGIN;

-- Tabla para watchlists de criptos (migrar desde users.json → monedas)
CREATE TABLE IF NOT EXISTS user_watchlists (
    user_id BIGINT PRIMARY KEY REFERENCES users(user_id) ON DELETE CASCADE,
    coins TEXT[] NOT NULL DEFAULT '{}',
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_user_watchlists_user_id ON user_watchlists(user_id);

-- Tabla para preferencias de usuario (migrar desde users.json → hbd_alerts, intervalo_alerta_h)
CREATE TABLE IF NOT EXISTS user_preferences (
    user_id BIGINT PRIMARY KEY REFERENCES users(user_id) ON DELETE CASCADE,
    hbd_alerts BOOLEAN DEFAULT FALSE,
    alerta_interval_hours DECIMAL(4,2) DEFAULT 1.0,
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_user_preferences_user_id ON user_preferences(user_id);

-- Tabla para estadísticas de uso diario (migrar desde users.json → daily_usage)
CREATE TABLE IF NOT EXISTS user_usage_stats (
    user_id BIGINT REFERENCES users(user_id) ON DELETE CASCADE,
    usage_date DATE NOT NULL,
    ver_count INT DEFAULT 0,
    ta_count INT DEFAULT 0,
    temp_changes_count INT DEFAULT 0,
    btc_count INT DEFAULT 0,
    graf_count INT DEFAULT 0,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    PRIMARY KEY (user_id, usage_date)
);

CREATE INDEX IF NOT EXISTS idx_user_usage_stats_user_id ON user_usage_stats(user_id);
CREATE INDEX IF NOT EXISTS idx_user_usage_stats_date ON user_usage_stats(usage_date);

-- Trigger para actualizar updated_at en user_watchlists
CREATE TRIGGER update_user_watchlists_updated_at
    BEFORE UPDATE ON user_watchlists
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- Trigger para actualizar updated_at en user_preferences
CREATE TRIGGER update_user_preferences_updated_at
    BEFORE UPDATE ON user_preferences
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- Trigger para actualizar updated_at en user_usage_stats
CREATE TRIGGER update_user_usage_stats_updated_at
    BEFORE UPDATE ON user_usage_stats
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

COMMIT;
