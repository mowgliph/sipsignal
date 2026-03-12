-- Migration: 004_referral_system.sql
-- Description: Add referral tracking system to users table

-- 1. Add columns to users table
ALTER TABLE users
ADD COLUMN referrer_code VARCHAR(32) UNIQUE,
ADD COLUMN referred_by INTEGER REFERENCES users(user_id) ON DELETE SET NULL;

-- 2. Create indexes for performance
CREATE INDEX IF NOT EXISTS idx_users_referrer_code ON users(referrer_code);
CREATE INDEX IF NOT EXISTS idx_users_referred_by ON users(referred_by);

-- 3. Create referrals tracking table
CREATE TABLE referrals (
    id SERIAL PRIMARY KEY,
    referrer_id INTEGER NOT NULL REFERENCES users(user_id) ON DELETE CASCADE,
    referred_id INTEGER NOT NULL REFERENCES users(user_id) ON DELETE CASCADE,
    referred_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    UNIQUE(referrer_id, referred_id)
);

-- 4. Create indexes for referrals table
CREATE INDEX IF NOT EXISTS idx_referrals_referrer_id ON referrals(referrer_id);
CREATE INDEX IF NOT EXISTS idx_referrals_referred_id ON referrals(referred_id);

-- 5. Add documentation comments
COMMENT ON TABLE referrals IS 'Tracking de referidos entre usuarios';
COMMENT ON COLUMN users.referrer_code IS 'Código único para referidos';
COMMENT ON COLUMN users.referred_by IS 'ID del usuario que lo refirió';
