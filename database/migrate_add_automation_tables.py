"""
Migration script to add automation tables used by the GSignalX auto-trading runner.

Safe to run multiple times (CREATE TABLE IF NOT EXISTS).
"""

import os
import sqlite3


def migrate_add_automation_tables():
    current_dir = os.path.dirname(os.path.abspath(__file__))
    db_path = os.path.join(current_dir, "trading_sessions.db")

    if not os.path.exists(db_path):
        print(f"Database not found at {db_path}")
        return

    conn = sqlite3.connect(db_path)
    try:
        conn.executescript(
            """
            CREATE TABLE IF NOT EXISTS automation_rules (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id TEXT NOT NULL,
                name TEXT NOT NULL,
                enabled INTEGER NOT NULL DEFAULT 1,
                symbols_json TEXT NOT NULL DEFAULT '[]',
                biases_json TEXT NOT NULL DEFAULT '["BULLISH","BEARISH"]',
                phases_json TEXT NOT NULL DEFAULT '["RANGE","EXPANSION","MIXED"]',
                timeframes_json TEXT NOT NULL DEFAULT '["D1"]',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );

            CREATE INDEX IF NOT EXISTS idx_automation_rules_user ON automation_rules(user_id);
            CREATE INDEX IF NOT EXISTS idx_automation_rules_enabled ON automation_rules(enabled);

            CREATE TABLE IF NOT EXISTS automation_active_pairs (
                symbol TEXT PRIMARY KEY,
                direction TEXT NOT NULL CHECK(direction IN ('buy','sell')),
                timeframes_json TEXT NOT NULL DEFAULT '[]',
                market_phase TEXT,
                confidence REAL,
                matched_rule_ids_json TEXT NOT NULL DEFAULT '[]',
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                expires_at TIMESTAMP NOT NULL
            );

            CREATE INDEX IF NOT EXISTS idx_automation_active_pairs_expires ON automation_active_pairs(expires_at);

            CREATE TABLE IF NOT EXISTS automation_rule_matches (
                rule_id INTEGER NOT NULL,
                symbol TEXT NOT NULL,
                direction TEXT NOT NULL CHECK(direction IN ('buy','sell')),
                reason_json TEXT NOT NULL DEFAULT '{}',
                matched_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                expires_at TIMESTAMP NOT NULL,
                PRIMARY KEY (rule_id, symbol),
                FOREIGN KEY (rule_id) REFERENCES automation_rules(id) ON DELETE CASCADE
            );

            CREATE INDEX IF NOT EXISTS idx_automation_rule_matches_expires ON automation_rule_matches(expires_at);

            CREATE TABLE IF NOT EXISTS automation_signal_snapshots (
                symbol TEXT PRIMARY KEY,
                payload_json TEXT NOT NULL,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
            """
        )
        conn.commit()
        print("Automation tables migration completed successfully!")
        print(f"Database updated: {db_path}")
    except Exception as e:
        conn.rollback()
        raise
    finally:
        conn.close()


if __name__ == "__main__":
    migrate_add_automation_tables()

