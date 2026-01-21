from __future__ import annotations

from dataclasses import asdict
from datetime import UTC, datetime
from typing import Any, Dict, Iterable, List, Optional, Sequence, Tuple

from src.automation.models import AutomationRule, RuleMatchResult, Signal


_NO_TRADE_BIASES = {"NEUTRAL", "PENDING", ""}
_TF_NO_TRADE = {"NEUTRAL", "", None}


def _direction_for_bias(bias: str) -> Optional[str]:
    b = (bias or "").strip().upper()
    if b == "BULLISH":
        return "buy"
    if b == "BEARISH":
        return "sell"
    return None


def _expected_tf_signal(direction: str) -> str:
    return "BUY" if direction == "buy" else "SELL"


def evaluate_rule(rule: AutomationRule, signal: Signal) -> RuleMatchResult:
    """
    Evaluate a single signal against a rule and return a match result with reasons.

    Alignment definition (per requirements):
    - For bullish: configured timeframes must have signal == BUY and not NEUTRAL
    - For bearish: configured timeframes must have signal == SELL and not NEUTRAL
    """
    now = datetime.now(UTC)
    reasons: List[str] = []
    debug: Dict[str, Any] = {
        "signal_bias": signal.bias,
        "signal_market_phase": signal.market_phase,
        "signal_is_stale": signal.is_stale,
        "rule": {
            "id": rule.id,
            "name": rule.name,
            "enabled": rule.enabled,
            "symbols": list(rule.symbols),
            "biases": list(rule.biases),
            "market_phases": list(rule.market_phases),
            "timeframe_chain": list(rule.timeframe_chain),
        },
    }

    if not rule.enabled:
        reasons.append("Rule is disabled")
        return RuleMatchResult(
            rule_id=rule.id,
            rule_name=rule.name,
            symbol=signal.symbol,
            direction=None,
            matched=False,
            reasons=reasons,
            debug=debug,
            matched_at=now,
        )

    # "Actively traded only when the signal is showing / still active":
    # If the upstream API marks a signal as stale, treat it as no-trade.
    if signal.is_stale is True:
        reasons.append("Signal is stale (not active)")
        return RuleMatchResult(
            rule_id=rule.id,
            rule_name=rule.name,
            symbol=signal.symbol,
            direction=None,
            matched=False,
            reasons=reasons,
            debug=debug,
            matched_at=now,
        )

    if rule.symbols and signal.symbol not in {s.strip().upper() for s in rule.symbols if s}:
        reasons.append("Symbol not selected by rule")
        return RuleMatchResult(
            rule_id=rule.id,
            rule_name=rule.name,
            symbol=signal.symbol,
            direction=None,
            matched=False,
            reasons=reasons,
            debug=debug,
            matched_at=now,
        )

    bias = (signal.bias or "").strip().upper()
    if bias in _NO_TRADE_BIASES:
        reasons.append(f"Signal bias '{bias}' treated as no-trade")
        return RuleMatchResult(
            rule_id=rule.id,
            rule_name=rule.name,
            symbol=signal.symbol,
            direction=None,
            matched=False,
            reasons=reasons,
            debug=debug,
            matched_at=now,
        )

    if rule.biases and bias not in {b.strip().upper() for b in rule.biases if b}:
        reasons.append("Bias filter did not match")
        return RuleMatchResult(
            rule_id=rule.id,
            rule_name=rule.name,
            symbol=signal.symbol,
            direction=None,
            matched=False,
            reasons=reasons,
            debug=debug,
            matched_at=now,
        )

    direction = _direction_for_bias(bias)
    if not direction:
        reasons.append("Unrecognized bias direction (no-trade)")
        return RuleMatchResult(
            rule_id=rule.id,
            rule_name=rule.name,
            symbol=signal.symbol,
            direction=None,
            matched=False,
            reasons=reasons,
            debug=debug,
            matched_at=now,
        )

    phase = (signal.market_phase or "").strip().upper()
    if rule.market_phases and phase not in {p.strip().upper() for p in rule.market_phases if p}:
        reasons.append("Market phase filter did not match")
        return RuleMatchResult(
            rule_id=rule.id,
            rule_name=rule.name,
            symbol=signal.symbol,
            direction=None,
            matched=False,
            reasons=reasons,
            debug=debug,
            matched_at=now,
        )

    tf_chain = [tf.strip().upper() for tf in rule.timeframe_chain if tf]
    if not tf_chain:
        reasons.append("Rule has no timeframe configured")
        return RuleMatchResult(
            rule_id=rule.id,
            rule_name=rule.name,
            symbol=signal.symbol,
            direction=None,
            matched=False,
            reasons=reasons,
            debug=debug,
            matched_at=now,
        )

    expected_tf = _expected_tf_signal(direction)
    tf_debug: Dict[str, Any] = {}
    for tf in tf_chain:
        tf_sig = signal.timeframes.get(tf)
        if not tf_sig:
            reasons.append(f"Missing timeframe '{tf}' in signal payload")
            tf_debug[tf] = {"present": False}
            return RuleMatchResult(
                rule_id=rule.id,
                rule_name=rule.name,
                symbol=signal.symbol,
                direction=None,
                matched=False,
                reasons=reasons,
                debug={**debug, "timeframes": tf_debug},
                matched_at=now,
            )

        tf_signal_value = (tf_sig.signal or "").strip().upper()
        tf_debug[tf] = {
            "present": True,
            "signal": tf_signal_value,
            "confidence": tf_sig.confidence,
            "strength": tf_sig.strength,
            "trend": tf_sig.trend,
        }

        if tf_signal_value in _TF_NO_TRADE:
            reasons.append(f"Timeframe '{tf}' is NEUTRAL (no alignment)")
            return RuleMatchResult(
                rule_id=rule.id,
                rule_name=rule.name,
                symbol=signal.symbol,
                direction=None,
                matched=False,
                reasons=reasons,
                debug={**debug, "timeframes": tf_debug},
                matched_at=now,
            )

        if tf_signal_value != expected_tf:
            reasons.append(
                f"Timeframe '{tf}' signal '{tf_signal_value}' != expected '{expected_tf}'"
            )
            return RuleMatchResult(
                rule_id=rule.id,
                rule_name=rule.name,
                symbol=signal.symbol,
                direction=None,
                matched=False,
                reasons=reasons,
                debug={**debug, "timeframes": tf_debug},
                matched_at=now,
            )

    reasons.append("Matched (bias + market_phase + timeframe alignment)")
    return RuleMatchResult(
        rule_id=rule.id,
        rule_name=rule.name,
        symbol=signal.symbol,
        direction=direction,
        matched=True,
        reasons=reasons,
        debug={**debug, "timeframes": tf_debug},
        matched_at=now,
    )


def evaluate_rules(
    signals: Sequence[Signal], rules: Sequence[AutomationRule]
) -> Tuple[List[RuleMatchResult], Dict[str, Dict[str, Any]]]:
    """
    Evaluate all rules across signals.

    Returns:
    - list of RuleMatchResult (one per (rule, signal) evaluated that produced match or meaningful no-trade)
    - active_pairs dict keyed by symbol with resolved direction and metadata

    Conflict rule:
    - If multiple rules match the same symbol with different directions, the symbol becomes no-trade (not activated).
    """
    results: List[RuleMatchResult] = []

    # symbol -> set(directions) + metadata
    activation: Dict[str, Dict[str, Any]] = {}

    for rule in rules:
        for sig in signals:
            # Cheap prefilter by symbol list to avoid creating huge results.
            if rule.symbols:
                if sig.symbol not in {s.strip().upper() for s in rule.symbols if s}:
                    continue

            r = evaluate_rule(rule, sig)
            if r.matched:
                results.append(r)
                entry = activation.setdefault(
                    sig.symbol,
                    {
                        "symbol": sig.symbol,
                        "directions": set(),
                        "matched_rule_ids": set(),
                        "matched_rule_names": set(),
                        "market_phase": sig.market_phase,
                        "bias": sig.bias,
                        "confidence": sig.confidence,
                        "timeframes": list(rule.timeframe_chain),
                        "matched_at": r.matched_at.isoformat(),
                    },
                )
                entry["directions"].add(r.direction)
                entry["matched_rule_ids"].add(r.rule_id)
                entry["matched_rule_names"].add(r.rule_name)

    # Resolve conflicts and normalize json-safe fields
    active_pairs: Dict[str, Dict[str, Any]] = {}
    for symbol, entry in activation.items():
        directions = sorted([d for d in entry["directions"] if d])
        if len(set(directions)) != 1:
            # conflict => do not activate
            continue

        active_pairs[symbol] = {
            "symbol": symbol,
            "direction": directions[0],
            "matched_rule_ids": sorted(list(entry["matched_rule_ids"])),
            "matched_rule_names": sorted(list(entry["matched_rule_names"])),
            "market_phase": entry.get("market_phase"),
            "bias": entry.get("bias"),
            "confidence": entry.get("confidence"),
            "timeframes": entry.get("timeframes") or [],
            "matched_at": entry.get("matched_at"),
        }

    return results, active_pairs

