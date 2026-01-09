-- Trading Sessions Schema

-- Drop existing tables if they exist
DROP TABLE IF EXISTS session_pairs;
DROP TABLE IF EXISTS currency_pairs;
DROP TABLE IF EXISTS trading_sessions;
DROP TABLE IF EXISTS trading_suspension;

-- Create trading_suspension table
CREATE TABLE trading_suspension (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    is_suspended BOOLEAN DEFAULT 0,
    suspended_at TIMESTAMP,
    suspended_by TEXT,
    reason TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Insert default suspension status
INSERT INTO trading_suspension (is_suspended, suspended_at, suspended_by, reason) 
VALUES (0, NULL, NULL, NULL);

-- Create trading_sessions table
CREATE TABLE trading_sessions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL UNIQUE,
    start_time TIME NOT NULL,
    end_time TIME NOT NULL,
    volatility_factor REAL DEFAULT 1.0,
    is_active BOOLEAN DEFAULT 1,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Create currency_pairs table
CREATE TABLE currency_pairs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    symbol TEXT NOT NULL UNIQUE,
    category TEXT CHECK(category IN ('mostTraded', 'metals', 'crypto', 'other')) DEFAULT 'other',
    is_active BOOLEAN DEFAULT 1,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Create session_pairs table
CREATE TABLE session_pairs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    session_id INTEGER NOT NULL,
    pair_id INTEGER NOT NULL,
    trade_direction TEXT CHECK(trade_direction IN ('buy', 'sell', 'neutral')) DEFAULT 'neutral',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (session_id) REFERENCES trading_sessions(id) ON DELETE CASCADE,
    FOREIGN KEY (pair_id) REFERENCES currency_pairs(id) ON DELETE CASCADE,
    UNIQUE(session_id, pair_id)
);

-- Create indexes
CREATE INDEX idx_sessions_name ON trading_sessions(name);
CREATE INDEX idx_pairs_symbol ON currency_pairs(symbol);
CREATE INDEX idx_session_pairs_direction ON session_pairs(trade_direction);

-- Insert default trading sessions
INSERT INTO trading_sessions (name, start_time, end_time, volatility_factor) VALUES
    ('Tokyo & Sydney', '21:00', '08:00', 1.2),
    ('Tokyo-London Overlap', '08:00', '09:00', 1.5),
    ('London', '08:00', '17:00', 1.3),
    ('London-NY Overlap', '13:00', '17:00', 1.6),
    ('New York', '13:00', '21:00', 1.3);

-- Create trigger to update updated_at timestamp
CREATE TRIGGER update_sessions_timestamp 
AFTER UPDATE ON trading_sessions
BEGIN
    UPDATE trading_sessions SET updated_at = CURRENT_TIMESTAMP WHERE id = NEW.id;
END;

CREATE TRIGGER update_pairs_timestamp
AFTER UPDATE ON currency_pairs
BEGIN
    UPDATE currency_pairs SET updated_at = CURRENT_TIMESTAMP WHERE id = NEW.id;
END;

CREATE TRIGGER update_session_pairs_timestamp
AFTER UPDATE ON session_pairs
BEGIN
    UPDATE session_pairs SET updated_at = CURRENT_TIMESTAMP WHERE id = NEW.id;
END; 

-- Create trigger to update trading_suspension timestamp
CREATE TRIGGER update_suspension_timestamp
AFTER UPDATE ON trading_suspension
BEGIN
    UPDATE trading_suspension SET updated_at = CURRENT_TIMESTAMP WHERE id = NEW.id;
END; 

-- Table for tracking profit monitoring data
CREATE TABLE IF NOT EXISTS profit_monitoring (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
    total_positions INTEGER NOT NULL,
    total_profit REAL NOT NULL,
    total_loss REAL NOT NULL,
    net_profit REAL NOT NULL,
    balance REAL NOT NULL,
    equity REAL NOT NULL,
    margin REAL NOT NULL,
    free_margin REAL NOT NULL
);

-- Table for tracking individual positions
CREATE TABLE IF NOT EXISTS position_tracking (
    ticket INTEGER PRIMARY KEY,
    symbol TEXT NOT NULL,
    type TEXT NOT NULL,
    volume REAL NOT NULL,
    open_price REAL NOT NULL,
    current_price REAL NOT NULL,
    profit REAL NOT NULL,
    profit_percent REAL NOT NULL,
    open_time DATETIME NOT NULL,
    last_update DATETIME DEFAULT CURRENT_TIMESTAMP,
    status TEXT DEFAULT 'open' CHECK(status IN ('open', 'closed', 'pending_close'))
);

-- Table for position close operations
CREATE TABLE IF NOT EXISTS position_close_operations (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    operation_type TEXT NOT NULL CHECK(operation_type IN ('single', 'profit', 'loss', 'all')),
    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
    positions_closed INTEGER DEFAULT 0,
    positions_failed INTEGER DEFAULT 0,
    total_profit_closed REAL DEFAULT 0,
    total_loss_closed REAL DEFAULT 0,
    status TEXT DEFAULT 'pending' CHECK(status IN ('pending', 'completed', 'failed')),
    error_message TEXT
);

-- Trading suspension management
CREATE TABLE IF NOT EXISTS trading_suspension (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    is_suspended BOOLEAN DEFAULT 0,
    suspended_at DATETIME,
    suspended_by TEXT,
    reason TEXT,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

-- Initialize trading suspension with default values
INSERT OR IGNORE INTO trading_suspension (id, is_suspended) VALUES (1, 0); 