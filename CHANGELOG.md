# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

---

## [1.0.0] - 2026-03-06

### 🚀 Added
- **Signal Scheduler**: Autonomous signal scheduler integrated in bot main loop
- **Journal System**: `/journal` command with paginated history, stats, and `/active` command
- **Drawdown Manager**: Auto-pause trading when drawdown threshold is reached, `/capital` command
- **WebSocket Price Monitor**: Real-time WebSocket price monitor for TP and SL tracking
- **Setup Handler**: `/setup` capital onboarding conversation handler
- **Signal Response Handler**: Signal status tracking and migration

### 🛠 Fixed
- Cleaned dead code from removed features (BTC alerts, valerts, price alerts)
- Fixed import errors in handlers/admin.py

### ⚠️ Breaking Changes
- **Removed Alert System**: The alert system has been removed, keeping only trading signals
- **Removed /graf Command**: The chart command was removed from the system

### ✅ Tests
- All 67 tests passing
- Bot starts without critical errors

### 📦 Dependencies
- Updated various dependencies for stability

---

## [0.0.0] - 2026-01-XX (Pre-release)

### 🚀 Initial Pre-release
- Initial Telegram bot setup
- Basic trading signal generation
- Technical analysis (RSI, MACD, Bollinger Bands, EMA)
- User management and language support
- Price alerts system

---

*For older releases, please refer to the git history.*