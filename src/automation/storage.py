from __future__ import annotations

import json
import os
import sqlite3
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from typing import Any, Dict, Iterable, List, Optional, Sequence, Tuple

from src.config.config import load_config


def _project_root() -> str:
    return os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


def get_db_path() -> str:
    config = load_config()
    return os.path.join(_project_root(), config["db"]["path"])


def get_db_connection() -> sqlite3.Connection:
    conn = sqlite3.connect(get_db_path())
    conn.row_factory = sqlite3.Row
    return conn


def ensure_automation_tables(conn: sqlite3.Connection) -> None:
    """
    Create automation tables if they do not exist.
    This is safe to call from the runner and from the web app.
    """
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


def _json_dumps(value: Any) -> str:
    return json.dumps(value, separators=(",", ":"), ensure_ascii=False)


def _json_loads(value: Any, default: Any) -> Any:
    if value is None:
        return default
    if isinstance(value, (list, dict)):
        return value
    if not isinstance(value, str):
        return default
    try:
        return json.loads(value)
    except Exception:
        return default


@dataclass(frozen=True)
class RuleRow:
    id: int
    user_id: str
    name: str
    enabled: bool
    symbols: List[str]
    biases: List[str]
    phases: List[str]
    timeframes: List[str]
    created_at: Optional[str]
    updated_at: Optional[str]


class AutomationRuleStore:
    def __init__(self, conn: sqlite3.Connection):
        self.conn = conn
        ensure_automation_tables(self.conn)

    def list_rules(self, user_id: str) -> List[RuleRow]:
        cur = self.conn.execute(
            """
            SELECT * FROM automation_rules
            WHERE user_id = ?
            ORDER BY id DESC
            """,
            (user_id,),
        )
        rows = []
        for r in cur.fetchall():
            rows.append(
                RuleRow(
                    id=int(r["id"]),
                    user_id=r["user_id"],
                    name=r["name"],
                    enabled=bool(r["enabled"]),
                    symbols=[s.strip().upper() for s in _json_loads(r["symbols_json"], []) if s],
                    biases=[b.strip().upper() for b in _json_loads(r["biases_json"], []) if b],
                    phases=[p.strip().upper() for p in _json_loads(r["phases_json"], []) if p],
                    timeframes=[t.strip().upper() for t in _json_loads(r["timeframes_json"], []) if t],
                    created_at=r["created_at"],
                    updated_at=r["updated_at"],
                )
            )
        return rows

    def list_all_rules(self, enabled_only: bool = False) -> List[RuleRow]:
        where = ""
        params: Tuple[Any, ...] = ()
        if enabled_only:
            where = "WHERE enabled = 1"
        cur = self.conn.execute(
            f"""
            SELECT * FROM automation_rules
            {where}
            ORDER BY id DESC
            """,
            params,
        )
        rows: List[RuleRow] = []
        for r in cur.fetchall():
            rows.append(
                RuleRow(
                    id=int(r["id"]),
                    user_id=r["user_id"],
                    name=r["name"],
                    enabled=bool(r["enabled"]),
                    symbols=[s.strip().upper() for s in _json_loads(r["symbols_json"], []) if s],
                    biases=[b.strip().upper() for b in _json_loads(r["biases_json"], []) if b],
                    phases=[p.strip().upper() for p in _json_loads(r["phases_json"], []) if p],
                    timeframes=[t.strip().upper() for t in _json_loads(r["timeframes_json"], []) if t],
                    created_at=r["created_at"],
                    updated_at=r["updated_at"],
                )
            )
        return rows

    def create_rule(
        self,
        user_id: str,
        name: str,
        enabled: bool,
        symbols: Sequence[str],
        biases: Sequence[str],
        phases: Sequence[str],
        timeframes: Sequence[str],
    ) -> int:
        cur = self.conn.execute(
            """
            INSERT INTO automation_rules
            (user_id, name, enabled, symbols_json, biases_json, phases_json, timeframes_json)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (
                user_id,
                name.strip() or "Rule",
                1 if enabled else 0,
                _json_dumps([s.strip().upper() for s in symbols if s]),
                _json_dumps([b.strip().upper() for b in biases if b]),
                _json_dumps([p.strip().upper() for p in phases if p]),
                _json_dumps([t.strip().upper() for t in timeframes if t]),
            ),
        )
        self.conn.commit()
        return int(cur.lastrowid)

    def update_rule(
        self,
        rule_id: int,
        user_id: str,
        name: Optional[str] = None,
        enabled: Optional[bool] = None,
        symbols: Optional[Sequence[str]] = None,
        biases: Optional[Sequence[str]] = None,
        phases: Optional[Sequence[str]] = None,
        timeframes: Optional[Sequence[str]] = None,
    ) -> bool:
        updates: List[str] = []
        params: List[Any] = []

        if name is not None:
            updates.append("name = ?")
            params.append(name.strip() or "Rule")
        if enabled is not None:
            updates.append("enabled = ?")
            params.append(1 if enabled else 0)
        if symbols is not None:
            updates.append("symbols_json = ?")
            params.append(_json_dumps([s.strip().upper() for s in symbols if s]))
        if biases is not None:
            updates.append("biases_json = ?")
            params.append(_json_dumps([b.strip().upper() for b in biases if b]))
        if phases is not None:
            updates.append("phases_json = ?")
            params.append(_json_dumps([p.strip().upper() for p in phases if p]))
        if timeframes is not None:
            updates.append("timeframes_json = ?")
            params.append(_json_dumps([t.strip().upper() for t in timeframes if t]))

        if not updates:
            return True

        updates.append("updated_at = CURRENT_TIMESTAMP")
        params.extend([rule_id, user_id])

        cur = self.conn.execute(
            f"""
            UPDATE automation_rules
            SET {", ".join(updates)}
            WHERE id = ? AND user_id = ?
            """,
            tuple(params),
        )
        self.conn.commit()
        return cur.rowcount > 0

    def delete_rule(self, rule_id: int, user_id: str) -> bool:
        cur = self.conn.execute(
            "DELETE FROM automation_rules WHERE id = ? AND user_id = ?",
            (rule_id, user_id),
        )
        self.conn.commit()
        return cur.rowcount > 0


class AutomationStateStore:
    def __init__(self, conn: sqlite3.Connection):
        self.conn = conn
        ensure_automation_tables(self.conn)

    def upsert_signal_snapshots(self, snapshots: Dict[str, Dict[str, Any]]) -> None:
        """
        snapshots: symbol -> raw payload dict
        """
        rows = [(symbol, _json_dumps(payload)) for symbol, payload in snapshots.items()]
        self.conn.executemany(
            """
            INSERT INTO automation_signal_snapshots (symbol, payload_json, updated_at)
            VALUES (?, ?, CURRENT_TIMESTAMP)
            ON CONFLICT(symbol) DO UPDATE SET
                payload_json = excluded.payload_json,
                updated_at = CURRENT_TIMESTAMP
            """,
            rows,
        )
        self.conn.commit()

    def list_signal_snapshots(self, limit: int = 500) -> List[Dict[str, Any]]:
        cur = self.conn.execute(
            """
            SELECT symbol, payload_json, updated_at
            FROM automation_signal_snapshots
            ORDER BY updated_at DESC
            LIMIT ?
            """,
            (limit,),
        )
        out: List[Dict[str, Any]] = []
        for r in cur.fetchall():
            out.append(
                {
                    "symbol": r["symbol"],
                    "updated_at": r["updated_at"],
                    "payload": _json_loads(r["payload_json"], {}),
                }
            )
        return out

    def replace_active_pairs(
        self,
        active_pairs: Dict[str, Dict[str, Any]],
        ttl_seconds: int,
    ) -> None:
        """
        Replace the currently-active pairs set.

        Important behavior:
        - Pairs that are not present in the latest cycle are removed immediately.
        - `expires_at` remains as a safety net if the runner stops updating (fail-safe TTL).
        """
        now = datetime.now(UTC)
        expires_at = now + timedelta(seconds=ttl_seconds)

        rows = []
        for symbol, item in active_pairs.items():
            rows.append(
                (
                    symbol,
                    item.get("direction"),
                    _json_dumps(item.get("timeframes") or []),
                    item.get("market_phase"),
                    item.get("confidence"),
                    _json_dumps(item.get("matched_rule_ids") or []),
                    expires_at.isoformat(),
                )
            )

        # Replace semantics: remove anything not in the latest active set immediately.
        # We do this in a single transaction so readers see either the old set or the new set.
        with self.conn:
            self.conn.execute("DELETE FROM automation_active_pairs")

            if rows:
                self.conn.executemany(
                    """
                    INSERT INTO automation_active_pairs
                    (symbol, direction, timeframes_json, market_phase, confidence, matched_rule_ids_json, updated_at, expires_at)
                    VALUES (?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP, ?)
                    ON CONFLICT(symbol) DO UPDATE SET
                        direction = excluded.direction,
                        timeframes_json = excluded.timeframes_json,
                        market_phase = excluded.market_phase,
                        confidence = excluded.confidence,
                        matched_rule_ids_json = excluded.matched_rule_ids_json,
                        updated_at = CURRENT_TIMESTAMP,
                        expires_at = excluded.expires_at
                    """,
                    rows,
                )

            # Purge expired (kept as a safety net; normally the table was just replaced)
            self.conn.execute(
                "DELETE FROM automation_active_pairs WHERE expires_at <= CURRENT_TIMESTAMP"
            )

    def replace_rule_matches(
        self,
        matches: List[Dict[str, Any]],
        ttl_seconds: int,
    ) -> None:
        now = datetime.now(UTC)
        expires_at = (now + timedelta(seconds=ttl_seconds)).isoformat()

        rows = []
        for m in matches:
            rows.append(
                (
                    int(m["rule_id"]),
                    str(m["symbol"]).strip().upper(),
                    m["direction"],
                    _json_dumps(m.get("reason") or {}),
                    expires_at,
                )
            )

        # Replace semantics: keep only latest-cycle matches for transparency.
        with self.conn:
            self.conn.execute("DELETE FROM automation_rule_matches")

            if rows:
                self.conn.executemany(
                    """
                    INSERT INTO automation_rule_matches
                    (rule_id, symbol, direction, reason_json, matched_at, expires_at)
                    VALUES (?, ?, ?, ?, CURRENT_TIMESTAMP, ?)
                    ON CONFLICT(rule_id, symbol) DO UPDATE SET
                        direction = excluded.direction,
                        reason_json = excluded.reason_json,
                        matched_at = CURRENT_TIMESTAMP,
                        expires_at = excluded.expires_at
                    """,
                    rows,
                )

            self.conn.execute(
                "DELETE FROM automation_rule_matches WHERE expires_at <= CURRENT_TIMESTAMP"
            )

    def list_active_pairs(self) -> List[Dict[str, Any]]:
        cur = self.conn.execute(
            """
            SELECT symbol, direction, timeframes_json, market_phase, confidence, matched_rule_ids_json,
                   updated_at, expires_at
            FROM automation_active_pairs
            WHERE expires_at > CURRENT_TIMESTAMP
            ORDER BY updated_at DESC
            """
        )
        out: List[Dict[str, Any]] = []
        for r in cur.fetchall():
            out.append(
                {
                    "symbol": r["symbol"],
                    "direction": r["direction"],
                    "timeframes": _json_loads(r["timeframes_json"], []),
                    "market_phase": r["market_phase"],
                    "confidence": r["confidence"],
                    "matched_rule_ids": _json_loads(r["matched_rule_ids_json"], []),
                    "updated_at": r["updated_at"],
                    "expires_at": r["expires_at"],
                }
            )
        return out

    def list_rule_matches(self, user_id: str) -> List[Dict[str, Any]]:
        cur = self.conn.execute(
            """
            SELECT rm.rule_id, r.name as rule_name, rm.symbol, rm.direction, rm.reason_json, rm.matched_at, rm.expires_at
            FROM automation_rule_matches rm
            JOIN automation_rules r ON r.id = rm.rule_id
            WHERE r.user_id = ?
            AND rm.expires_at > CURRENT_TIMESTAMP
            ORDER BY rm.matched_at DESC
            """,
            (user_id,),
        )
        out: List[Dict[str, Any]] = []
        for row in cur.fetchall():
            out.append(
                {
                    "rule_id": row["rule_id"],
                    "rule_name": row["rule_name"],
                    "symbol": row["symbol"],
                    "direction": row["direction"],
                    "reason": _json_loads(row["reason_json"], {}),
                    "matched_at": row["matched_at"],
                    "expires_at": row["expires_at"],
                }
            )
        return out

