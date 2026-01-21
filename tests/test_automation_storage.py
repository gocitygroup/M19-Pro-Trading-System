import sqlite3
import unittest

from src.automation.storage import AutomationStateStore, ensure_automation_tables


class TestAutomationStorage(unittest.TestCase):
    def test_replace_active_pairs_removes_missing_immediately(self):
        conn = sqlite3.connect(":memory:")
        conn.row_factory = sqlite3.Row
        try:
            ensure_automation_tables(conn)
            store = AutomationStateStore(conn)

            store.replace_active_pairs(
                {
                    "EURUSD": {"direction": "buy", "timeframes": ["D1"]},
                    "GBPUSD": {"direction": "sell", "timeframes": ["D1"]},
                },
                ttl_seconds=30,
            )
            self.assertEqual({p["symbol"] for p in store.list_active_pairs()}, {"EURUSD", "GBPUSD"})

            # Next cycle: GBPUSD no longer active -> should disappear immediately
            store.replace_active_pairs(
                {
                    "EURUSD": {"direction": "buy", "timeframes": ["D1"]},
                },
                ttl_seconds=30,
            )
            self.assertEqual({p["symbol"] for p in store.list_active_pairs()}, {"EURUSD"})
        finally:
            conn.close()


if __name__ == "__main__":
    unittest.main()

