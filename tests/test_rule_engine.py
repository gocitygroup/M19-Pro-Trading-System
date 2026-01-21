import unittest

from src.automation.models import AutomationRule, parse_signal
from src.automation.rule_engine import evaluate_rule, evaluate_rules


class TestRuleEngine(unittest.TestCase):
    def _base_signal_payload(self):
        return {
            "symbol": "EURUSD",
            "bias": "BULLISH",
            "market_phase": "RANGE",
            "confidence": 0.8,
            "is_stale": False,
            "price": 1.2345,
            "timeframes": {
                "D1": {
                    "signal": "BUY",
                    "confidence": 0.7,
                    "strength": 70.0,
                    "trend": "UP",
                    "entry": None,
                    "risk_reward": None,
                    "stop_loss": None,
                    "take_profit": None,
                },
                "H4": {
                    "signal": "BUY",
                    "confidence": 0.6,
                    "strength": 60.0,
                    "trend": "UP",
                    "entry": None,
                    "risk_reward": None,
                    "stop_loss": None,
                    "take_profit": None,
                },
                "H1": {
                    "signal": "NEUTRAL",
                    "confidence": 0.1,
                    "strength": 10.0,
                    "trend": "NEUTRAL",
                    "entry": None,
                    "risk_reward": None,
                    "stop_loss": None,
                    "take_profit": None,
                },
            },
        }

    def test_single_timeframe_match(self):
        sig = parse_signal(self._base_signal_payload())
        rule = AutomationRule(
            id=1,
            user_id="admin",
            name="D1 bullish",
            enabled=True,
            symbols=["EURUSD"],
            biases=["BULLISH"],
            market_phases=["RANGE"],
            timeframe_chain=["D1"],
        )

        r = evaluate_rule(rule, sig)
        self.assertTrue(r.matched)
        self.assertEqual(r.direction, "buy")

    def test_multi_timeframe_chain_match(self):
        sig = parse_signal(self._base_signal_payload())
        rule = AutomationRule(
            id=2,
            user_id="admin",
            name="D1+H4 aligned",
            enabled=True,
            symbols=["EURUSD"],
            biases=["BULLISH"],
            market_phases=["RANGE"],
            timeframe_chain=["D1", "H4"],
        )

        r = evaluate_rule(rule, sig)
        self.assertTrue(r.matched)
        self.assertEqual(r.direction, "buy")

    def test_neutral_timeframe_breaks_alignment(self):
        payload = self._base_signal_payload()
        payload["timeframes"]["D1"]["signal"] = "NEUTRAL"
        sig = parse_signal(payload)
        rule = AutomationRule(
            id=3,
            user_id="admin",
            name="D1 must align",
            enabled=True,
            symbols=["EURUSD"],
            biases=["BULLISH"],
            market_phases=["RANGE"],
            timeframe_chain=["D1"],
        )

        r = evaluate_rule(rule, sig)
        self.assertFalse(r.matched)

    def test_neutral_or_pending_bias_is_no_trade(self):
        payload = self._base_signal_payload()
        payload["bias"] = "NEUTRAL"
        sig = parse_signal(payload)
        rule = AutomationRule(
            id=4,
            user_id="admin",
            name="ignore neutral",
            enabled=True,
            symbols=["EURUSD"],
            biases=["BULLISH", "BEARISH"],
            market_phases=["RANGE", "EXPANSION", "MIXED"],
            timeframe_chain=["D1"],
        )

        r = evaluate_rule(rule, sig)
        self.assertFalse(r.matched)

    def test_stale_signal_is_no_trade(self):
        payload = self._base_signal_payload()
        payload["is_stale"] = True
        sig = parse_signal(payload)
        rule = AutomationRule(
            id=5,
            user_id="admin",
            name="ignore stale",
            enabled=True,
            symbols=["EURUSD"],
            biases=["BULLISH", "BEARISH"],
            market_phases=["RANGE", "EXPANSION", "MIXED"],
            timeframe_chain=["D1"],
        )

        r = evaluate_rule(rule, sig)
        self.assertFalse(r.matched)

    def test_conflicting_rules_do_not_activate_symbol(self):
        sig_bull = parse_signal(self._base_signal_payload())

        payload_bear = self._base_signal_payload()
        payload_bear["bias"] = "BEARISH"
        payload_bear["timeframes"]["D1"]["signal"] = "SELL"
        payload_bear["timeframes"]["H4"]["signal"] = "SELL"
        sig_bear = parse_signal(payload_bear)

        rule_any = AutomationRule(
            id=10,
            user_id="admin",
            name="bullish eurusd",
            enabled=True,
            symbols=["EURUSD"],
            biases=["BULLISH"],
            market_phases=["RANGE"],
            timeframe_chain=["D1"],
        )
        rule_any2 = AutomationRule(
            id=11,
            user_id="admin",
            name="bearish eurusd",
            enabled=True,
            symbols=["EURUSD"],
            biases=["BEARISH"],
            market_phases=["RANGE"],
            timeframe_chain=["D1"],
        )

        _, active = evaluate_rules([sig_bull, sig_bear], [rule_any, rule_any2])
        # Conflicts are resolved by omitting the symbol from activations
        self.assertEqual(active, {})


if __name__ == "__main__":
    unittest.main()

