import unittest
from unittest.mock import MagicMock, patch

from src.automation.signal_fetcher import FetchConfig, SignalFetcher


class _FakeResp:
    def __init__(self, payload, status_code=200, raise_exc=None):
        self._payload = payload
        self.status_code = status_code
        self._raise_exc = raise_exc

    def raise_for_status(self):
        if self._raise_exc:
            raise self._raise_exc
        if self.status_code >= 400:
            raise RuntimeError(f"HTTP {self.status_code}")

    def json(self):
        return self._payload


class TestSignalFetcher(unittest.TestCase):
    def test_next_url_pagination(self):
        cfg = FetchConfig(signals_url="https://example.test/signals", api_key=None, max_retries=1, max_pages=10)
        f = SignalFetcher(cfg)

        page1 = {"results": [{"symbol": "EURUSD", "bias": "BULLISH", "market_phase": "RANGE", "timeframes": {}}], "next": "https://example.test/signals?page=2"}
        page2 = {"results": [{"symbol": "GBPUSD", "bias": "BEARISH", "market_phase": "RANGE", "timeframes": {}}], "next": None}

        with patch.object(f._session, "get") as mget:
            mget.side_effect = [
                _FakeResp(page1),
                _FakeResp(page2),
            ]
            signals, meta = f.fetch_all()

        self.assertEqual(meta["pages_fetched"], 2)
        self.assertEqual(len(signals), 2)
        self.assertEqual({s.symbol for s in signals}, {"EURUSD", "GBPUSD"})

    def test_symbols_key_payload_supported(self):
        cfg = FetchConfig(signals_url="https://example.test/signals", api_key=None, max_retries=1, max_pages=10)
        f = SignalFetcher(cfg)

        page1 = {"symbols": [{"symbol": "EURUSD", "bias": "BULLISH", "market_phase": "RANGE", "timeframes": {}}]}

        with patch.object(f._session, "get") as mget:
            mget.side_effect = [
                _FakeResp(page1),
            ]
            signals, meta = f.fetch_all()

        self.assertEqual(meta["pages_fetched"], 1)
        self.assertEqual(len(signals), 1)
        self.assertEqual(signals[0].symbol, "EURUSD")

    def test_retry_and_backoff(self):
        cfg = FetchConfig(signals_url="https://example.test/signals", api_key=None, max_retries=3, backoff_seconds=0.01)
        f = SignalFetcher(cfg)

        class _Boom(Exception):
            pass

        with patch.object(f._session, "get") as mget, patch("time.sleep") as msleep:
            mget.side_effect = [
                _Boom("net1"),
                _Boom("net2"),
                _FakeResp([]),
            ]
            signals, meta = f.fetch_all()

        self.assertEqual(signals, [])
        self.assertGreaterEqual(msleep.call_count, 2)


if __name__ == "__main__":
    unittest.main()

