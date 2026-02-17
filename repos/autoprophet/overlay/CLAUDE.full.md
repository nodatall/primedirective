# CLAUDE.md

6. **DOCS** – Update docs → Commit `Docs: …` (no prompts)

### 📚 Detailed Requirements:
@docs/documentation-requirements.md

## Development Commands

### Main Application
- `npm install` - Install dependencies for main app
- `npm start` - Start API server (port 3000)
- `npm run dev` - Start API server with auto-reload
- `npm run build` - Build React frontend for production
- `npm run dev-client` - Start webpack dev server for UI (port 8080)
- `npm test` - Run all tests using Mocha

### Database Operations
- `npm run migrate` - Run pending database migrations
- `npm run migrate:status` - Check migration status
- `npm run migrate:rollback` - Rollback last migration
- `npm run migrate:create "description"` - Create new migration
- `npm run sync-db` - Sync data from remote database to local

### Live Trading System
Scripts in `scripts/trading/`:
- `./start.sh` - Main launcher with automatic strategy selection
- `node scripts/trading/start-live-trading.js` - Direct trading system start
- `node scripts/trading/start-with-strategy.js` - Legacy manual strategy launcher (removed; exits with guidance)
- `node scripts/trading/add-exchange-orders.js [--stop-loss=4] [--take-profit=6]` - Add exchange-side orders

### Automatic Strategy Selection
The system now features automatic strategy selection via AutoStrategySelector:
- **Real-time Market Analysis**: Continuously evaluates market conditions using MarketIntel
- **Adaptive Strategy Switching**: Automatically switches between MOMENTUM, CONTRARIAN, and HYBRID modes
- **No Manual Configuration**: Eliminates need for manual strategy selection
- **Market Regime Detection**: Uses volatility, funding extremes, and exhaustion signals for optimal mode selection

Legacy manual strategy config files have been removed. Use `scripts/trading/start-live-trading.js` with the new OI momentum strategy.

### System Maintenance
Scripts in `scripts/maintenance/`:
- `node scripts/maintenance/refresh-symbols.js` - Refresh cached Orderly symbols
- `node scripts/maintenance/get-woofi-symbols.js` - Fetch available trading symbols from WooFi Pro
- `node scripts/maintenance/setup-database.js` - Setup database tables

### Strategy Analysis & Backtesting
Legacy backtesting scripts have been removed.

### Development & Debugging
Scripts moved to `scripts/debug/`:
- `node scripts/debug/debug-live-trading-validation.js` - Validate live trading system configuration
- `node scripts/debug/debug-trading-system.js` - General trading system debugging
- `node scripts/debug/debug-signal-analysis.js` - Analyze signal generation
- `node scripts/debug/debug-order-details.js` - Debug exchange order details

### Testing Utilities
Scripts moved to `scripts/utilities/`:
- `node scripts/utilities/test-exchange-stop-loss.js` - Test exchange-side stop loss functionality
- `node scripts/utilities/test-integrated-stop-loss.js` - Test integrated stop loss monitoring
- `node scripts/utilities/test-algo-orders.js` - Test algorithmic order types
- `node scripts/utilities/cleanup-test-data.js` - Clean up test data from database

## Architecture Overview

AutoProphet is a comprehensive cryptocurrency trading system with two main components:

### 1. API Server (`src/`)
- **Entry**: `src/app.js` (main server) and `src/server.js` (basic static server)
- **Purpose**: REST API endpoints and React frontend serving
- **Port**: 3000 (API), 8080 (webpack dev server)
- **Stack**: Express.js backend, React + Material-UI frontend
- **Key endpoints**:
  - `/api/health` - Health check
  - `/api/tokens` - Latest token data
  - `/api/tokens/:symbol` - Token history by symbol

### 2. Live Trading System (`src/trading/`)
- **Entry**: `./start.sh` (interactive) or `scripts/trading/start-live-trading.js` (programmatic)
- **Purpose**: Automated cryptocurrency trading with multi-strategy support
- **Exchange**: WooFi Pro (Orderly Network) with subaccount isolation
- **Strategies**: Momentum, Contrarian, and Hybrid strategy modes
- **Risk Management**: 5x leverage limit, exchange-side stop loss/take profit orders
- **Safety**: Subaccount-only mode, comprehensive error handling and logging

### Key Components

#### Trading Engine (`src/trading/LiveTradingSystem.js`)
- Real-time signal processing and position management with WebSocket price feeds
- 5x leverage enforcement with dynamic position sizing
- Trailing Take Profit system with 2% ratcheting mechanism
- Enhanced Trailing Stop Loss with dynamic distances (2% → 1.5% → 1% based on profit)
- Exchange-side risk management with automated order updates
- Comprehensive trade logging and performance tracking
- Client-side monitoring with WebSocket + polling fallback

#### WebSocket Price Monitor (`src/trading/WebSocketPriceMonitor.js`)
- Real-time ticker feeds via Orderly Network WebSocket API (wss://ws-evm.orderly.org)
- Sub-second price updates for active positions vs 30-second polling
- Bandwidth-efficient symbol subscription/unsubscription
- Exponential backoff reconnection with long-term retry strategy
- Graceful fallback to polling when WebSocket unavailable

#### OI Strategy (`src/trading/ProductionOIStrategy.js`)
- Implementation of Open Interest strategy from `strategy_resources/openintereststrat.png`
- Component weighting: 17% OI, 70% Funding, 13% Price
- Signal types: TREND_CONFIRMATION, SHORT_COVER_RALLY, AGGRESSIVE_SHORTING, FLUSH_RESET
- Advanced funding rate analysis and trend context evaluation
- Volatility filtering to prevent low-volatility trades (ATR < 0.5%)
- Dynamic position sizing based on signal strength and market volatility
- Funding rate z-score normalization using 30-day historical data
- Market regime detection with BTC trend bias adjustments
- Post-only limit order execution with market order fallback
- Comprehensive trade logging with volatility and regime metrics

#### ContrrarianSignalGenerator (`src/trading/ContrrarianSignalGenerator.js`)
- Exhaustion-based signal generation for counter-trend trading
- 4-signal detection system: price momentum, open interest, CVD, and funding rate extremes
- Configurable thresholds: >2% price moves, >5% OI changes, >70% CVD, >0.05% funding
- Requires 3+ exhaustion signals simultaneously for high-confidence entries
- Token exclusion system for volatile meme coins (MOG, PEPE, SHIB, DOGE, BONK)
- Integrated with ProductionOIStrategy for seamless mode switching

#### Market Analyzer (`src/trading/MarketAnalyzer.js`)
- Volatility calculation using ATR and realized volatility metrics
- Regime classification (LOW/NORMAL/HIGH/EXTREME volatility)
- Funding rate statistical analysis with z-score calculations
- BTC trend analysis for market regime detection
- Signal adjustment methods for funding extremes and market conditions

#### Exchange Connection (`src/trading/WooFiConnection.js`)
- WooFi Pro/Orderly Network API integration with Ed25519 authentication
- Subaccount-only safety mode with main account protection
- Exchange-side order management (LIMIT orders for TP, algo orders for SL)
- Position monitoring, balance tracking, and symbol conversion

#### Database Models
- **ScreenerData** (`src/models/ScreenerData.js`): 15 cryptocurrency metrics with extreme value protection
- **TradeHistory** (`src/models/TradeHistory.js`): Comprehensive trade logging with OI strategy analysis and position tracking

#### Utilities
- **OrderlySymbolFetcher** (`src/utils/OrderlySymbolFetcher.js`): Symbol mapping and caching for Orderly API
- **Migration System** (`scripts/migrate.js`): Database schema management with rollback support

## Development Workflow

### Full Stack Development
```bash
# Terminal 1: Start API server
npm start

# Terminal 2: Start React dev server
npm run dev-client

# Terminal 3: Start live trading with strategy selection (optional)
./start.sh

# Access at: http://localhost:8080
```

### Live Trading Workflow
```bash
# 1. Start live trading with strategy selection
./start.sh

# 2. Debug order details (optional)
node scripts/debug/debug-order-details.js
```

### Position Management Workflow
```bash
# Add exchange orders to existing positions
node scripts/trading/add-exchange-orders.js [--stop-loss=4] [--take-profit=6]  # Execute

# Monitor and debug positions
node scripts/debug/debug-position-state.js                # Debug position state
```

### Position Closure Detection
AutoProphet now includes advanced position closure detection that provides accurate PnL calculations when positions are closed on the exchange while the system is offline:

**Key Features:**
- **Actual Trade Data Retrieval**: Fetches real execution prices from exchange API
- **Weighted Average Exit Price**: Handles partial fills correctly across multiple trades
- **Fee Accounting**: Includes trading fees in PnL calculations for accurate net results
- **Multiple Fallback Strategies**: Graceful degradation through order history and price estimation
- **Exit Reason Detection**: Accurately identifies stop loss, take profit, or manual exits

### Logging System
AutoProphet uses a smart logging system to reduce noise while preserving critical events:

**Log Levels:**
- `CRITICAL`: Trade opens, closes, stop loss/take profit triggers (always visible)
- `IMPORTANT`: Position monitoring summaries, system status (production default)
- `INFO`: Signal processing, validation results
- `DEBUG`: Exchange API calls, detailed diagnostics (development only)

**Environment Configuration:**
```bash
# Production (clean, essential logs only)
LOG_LEVEL=IMPORTANT

# Development (verbose debugging)
LOG_LEVEL=DEBUG

# Rate limiting settings
LOG_RATE_LIMIT_WINDOW=30    # seconds
LOG_RATE_LIMIT_THRESHOLD=5  # messages before suppression
```

**Rate Limiting:**
- Repetitive messages automatically suppressed after threshold
- Shows summaries: "VIC/USDT: 47 messages suppressed (last 30s)"
- Critical trade events never suppressed

### Database Schema
- PostgreSQL with connection pooling
- **screener_data**: 15 cryptocurrency metrics with extreme value protection
- **trade_history**: Comprehensive trade logging with OI strategy analysis and position tracking (uses exit_time IS NULL for active positions)
- Automatic table creation and indexing
- Migration system for schema changes
- Decimal precision handling for extreme crypto values

## Environment Configuration

- `.env` - Main environment variables (database, WooFi API credentials)
- `.env.test` - Test environment variables
- **Required Variables**:
  - `DB_HOST`, `DB_PORT`, `DB_NAME`, `DB_USER`, `DB_PASSWORD` - Database connection
  - `WOOFI_APPLICATION_ID`, `WOOFI_API_KEY`, `WOOFI_API_SECRET` - WooFi API credentials
  - `WOOFI_SUBACCOUNT_ID` - Subaccount ID for trading (CRITICAL for safety)
- **Optional Variables**:
  - `ENHANCED_SCHEDULER=true` - Enable enhanced data collector features
  - `NODE_ENV=test` - Enable test mode

## Deployment Architecture

The application supports a hybrid deployment model with three components:

### Production Deployment
- **Data Collector**: Deployed to cloud (Railway, Render, or DigitalOcean) for 24/7 data collection
- **Live Trading**: Runs locally or on VPS with reliable internet for real-time trading
- **API/UI**: Can run locally for development/monitoring or deployed for remote access
- **Database**: Centralized PostgreSQL database accessible by all components

### Safety Considerations
- **Subaccount Isolation**: All trading operations restricted to subaccount only
- **5x Leverage Limit**: Hard-coded maximum leverage to prevent over-exposure
- **Exchange-Side Orders**: Stop losses and take profits managed by exchange for reliability
- **Comprehensive Logging**: All trades logged to database for audit and analysis
- **Graceful Error Handling**: System continues with client-side monitoring if exchange orders fail

### Performance Features
- **Symbol Caching**: Orderly API symbols cached for fast lookup (`cache/orderly-symbols.json`)
- **Real-time Monitoring**: Position monitoring every 30 seconds with leverage checks
- **Dynamic Position Sizing**: Automatically adjusts position sizes to respect leverage limits
- **Efficient Database**: Optimized queries with proper indexing for real-time performance

This architecture provides continuous data collection with reliable, safe, and profitable automated trading capabilities.

## CLAUDE.md — TDD Enforcement Rules

## 📁 CONTEXTUAL DOCUMENTATION SYSTEM

### 🎯 PURPOSE: ENHANCED CODE UNDERSTANDING
Every critical folder MUST have a `claude.md` file providing contextual documentation to help Claude understand the codebase structure, patterns, and conventions.

### 📂 REQUIRED CONTEXTUAL DOCUMENTATION:
- **`src/claude.md`** - Main source code overview and architecture
- **`src/models/claude.md`** - Database models, schemas, and data patterns
- **`src/services/claude.md`** - External API integrations and service patterns
- **`src/trading/claude.md`** - Trading engine, strategies, and risk management
- **`src/utils/claude.md`** - Utility functions and helper patterns
- **`test/claude.md`** - Testing strategies, patterns, and frameworks
