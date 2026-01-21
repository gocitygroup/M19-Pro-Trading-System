#!/usr/bin/env python3
"""
Continuous automation runner:
- Poll GSignalX signals (API or file mode)
- Evaluate enabled automation rules
- Publish active pairs + match details to SQLite (for MarketSessionTradingBot + web UI)

This runner is intentionally a separate process from:
- src/scripts/MarketSessionTradingBot.py
- src/scripts/run_enhanced_profit_monitor.py
- src/web/app.py
"""

import argparse
import json
import logging
import os
import signal as signal_module
import sys
import time
from datetime import UTC, datetime
from typing import Any, Dict, List

# Add project root to Python path (must be done before other imports)
project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

def _load_dotenv_if_present():
    """
    Load environment variables from .env if available.
    This runner relies on env vars for GSignalX API config, and we want it to work
    the same way as the web app/auth config does.
    """
    try:
        from dotenv import load_dotenv  # type: ignore

        env_path = os.path.join(project_root, ".env")
        if os.path.exists(env_path):
            load_dotenv(env_path)
    except Exception:
        # If python-dotenv isn't installed or file can't be read, continue.
        pass

from src.automation.models import AutomationRule, Signal
from src.automation.rule_engine import evaluate_rules
from src.automation.signal_fetcher import SignalFetcher, load_fetch_config_from_env
from src.automation.storage import AutomationRuleStore, AutomationStateStore, get_db_connection


def _configure_logging():
    os.makedirs(os.path.join(project_root, "logs"), exist_ok=True)
    log_path = os.path.join(project_root, "logs", "automation_runner.log")
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(levelname)s - %(message)s",
        handlers=[logging.StreamHandler(), logging.FileHandler(log_path)],
    )


def _atomic_write_json(path: str, payload: Dict[str, Any]) -> None:
    tmp = path + ".tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(payload, f, indent=2)
    os.replace(tmp, path)


class Runner:
    def __init__(
        self,
        poll_seconds: int,
        active_ttl_seconds: int,
        source: str,
        file_path: str | None,
    ):
        self.poll_seconds = poll_seconds
        self.active_ttl_seconds = active_ttl_seconds
        self.source = source
        self.file_path = file_path
        self.stop_requested = False

        self.fetcher = SignalFetcher(load_fetch_config_from_env())

        self.status_file = os.path.join(project_root, "automation_status.json")

    def request_stop(self):
        self.stop_requested = True

    def _load_rules(self) -> List[AutomationRule]:
        with get_db_connection() as conn:
            store = AutomationRuleStore(conn)
            rows = store.list_all_rules(enabled_only=True)
            rules: List[AutomationRule] = []
            for r in rows:
                rules.append(
                    AutomationRule(
                        id=r.id,
                        user_id=r.user_id,
                        name=r.name,
                        enabled=r.enabled,
                        symbols=r.symbols,
                        biases=r.biases,
                        market_phases=r.phases,
                        timeframe_chain=r.timeframes,
                    )
                )
            return rules

    def _fetch_signals(self) -> tuple[list[Signal], dict]:
        if self.source == "file":
            if not self.file_path:
                raise RuntimeError("--file-path is required when --source=file")
            return self.fetcher.load_from_file(self.file_path)
        return self.fetcher.fetch_all()

    def _persist(self, signals: List[Signal], active_pairs: Dict[str, Dict[str, Any]], match_results):
        snapshots = {s.symbol: s.raw for s in signals}
        match_rows = []
        for r in match_results:
            match_rows.append(
                {
                    "rule_id": r.rule_id,
                    "symbol": r.symbol,
                    "direction": r.direction,
                    "reason": {
                        "reasons": r.reasons,
                        "debug": r.debug,
                    },
                }
            )

        with get_db_connection() as conn:
            state = AutomationStateStore(conn)
            state.upsert_signal_snapshots(snapshots)
            state.replace_active_pairs(active_pairs, ttl_seconds=self.active_ttl_seconds)
            state.replace_rule_matches(match_rows, ttl_seconds=self.active_ttl_seconds)

    def run_forever(self):
        logging.info(
            "Starting automation runner: source=%s poll=%ss ttl=%ss",
            self.source,
            self.poll_seconds,
            self.active_ttl_seconds,
        )
        cycle = 0
        last_success: str | None = None
        last_error: str | None = None

        while not self.stop_requested:
            cycle += 1
            cycle_started = datetime.now(UTC)
            try:
                rules = self._load_rules()
                signals, fetch_meta = self._fetch_signals()
                match_results, active_pairs = evaluate_rules(signals, rules)

                self._persist(signals, active_pairs, match_results)

                last_success = datetime.now(UTC).isoformat()
                last_error = None

                status = {
                    "runner": "GSignalXAutomationRunner",
                    "source": self.source,
                    "poll_seconds": self.poll_seconds,
                    "active_ttl_seconds": self.active_ttl_seconds,
                    "cycle": cycle,
                    "last_fetch_time": cycle_started.isoformat(),
                    "last_successful_cycle": last_success,
                    "last_error": last_error,
                    "rules_loaded": len(rules),
                    "signals_loaded": len(signals),
                    "matches_count": len(match_results),
                    "active_pairs_count": len(active_pairs),
                    "fetch_meta": fetch_meta,
                }
                _atomic_write_json(self.status_file, status)

                logging.info(
                    "Cycle %s OK: rules=%s signals=%s matches=%s active=%s (%.2fs)",
                    cycle,
                    len(rules),
                    len(signals),
                    len(match_results),
                    len(active_pairs),
                    (datetime.now(UTC) - cycle_started).total_seconds(),
                )
            except Exception as e:
                last_error = str(e)
                status = {
                    "runner": "GSignalXAutomationRunner",
                    "source": self.source,
                    "poll_seconds": self.poll_seconds,
                    "active_ttl_seconds": self.active_ttl_seconds,
                    "cycle": cycle,
                    "last_fetch_time": cycle_started.isoformat(),
                    "last_successful_cycle": last_success,
                    "last_error": last_error,
                }
                _atomic_write_json(self.status_file, status)
                logging.exception("Cycle %s FAILED: %s", cycle, str(e))

            # Sleep with early stop support
            for _ in range(max(1, self.poll_seconds)):
                if self.stop_requested:
                    break
                time.sleep(1)

        logging.info("Automation runner stopped.")


def main():
    _configure_logging()
    _load_dotenv_if_present()

    parser = argparse.ArgumentParser(description="Run the GSignalX automation runner")
    parser.add_argument("--poll-seconds", type=int, default=int(os.getenv("GSIGNALX_POLL_SECONDS", "10")))
    parser.add_argument("--active-ttl-seconds", type=int, default=int(os.getenv("GSIGNALX_ACTIVE_TTL_SECONDS", "30")))
    parser.add_argument("--source", choices=["api", "file"], default=os.getenv("GSIGNALX_SOURCE", "api"))
    parser.add_argument("--file-path", default=os.getenv("GSIGNALX_FILE_PATH"))
    args = parser.parse_args()

    runner = Runner(
        poll_seconds=max(1, args.poll_seconds),
        active_ttl_seconds=max(5, args.active_ttl_seconds),
        source=args.source,
        file_path=args.file_path,
    )

    def _handle_stop(signum, frame):
        logging.info("Received signal %s, stopping...", signum)
        runner.request_stop()

    try:
        signal_module.signal(signal_module.SIGINT, _handle_stop)
        signal_module.signal(signal_module.SIGTERM, _handle_stop)
    except Exception:
        # Windows environments may not support all signals; KeyboardInterrupt still works.
        pass

    try:
        runner.run_forever()
    except KeyboardInterrupt:
        runner.request_stop()


if __name__ == "__main__":
    main()

