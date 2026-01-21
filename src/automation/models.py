from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Any, Dict, List, Optional, Sequence


Timeframe = str  # e.g. "D1", "H4", "H1", "M30", "M15", "M5"


@dataclass(frozen=True)
class TimeframeSignal:
    confidence: Optional[float]
    entry: Any
    risk_reward: Any
    signal: str  # "BUY" | "SELL" | "NEUTRAL"
    stop_loss: Any
    strength: Optional[float]
    take_profit: Any
    trend: Optional[str]


@dataclass(frozen=True)
class Signal:
    symbol: str
    bias: str  # "BULLISH" | "BEARISH" | ("NEUTRAL"/"PENDING"/other)
    market_phase: Optional[str]  # "RANGE" | "EXPANSION" | "MIXED" | None
    confidence: Optional[float]
    is_stale: Optional[bool]
    price: Optional[float]
    timeframes: Dict[Timeframe, TimeframeSignal]
    raw: Dict[str, Any]


@dataclass(frozen=True)
class AutomationRule:
    id: int
    user_id: str
    name: str
    enabled: bool
    symbols: Sequence[str]  # empty => all
    biases: Sequence[str]  # e.g. ["BULLISH","BEARISH"]
    market_phases: Sequence[str]  # e.g. ["RANGE","EXPANSION","MIXED"]
    timeframe_chain: Sequence[Timeframe]  # e.g. ["D1","H4","H1"]


@dataclass(frozen=True)
class RuleMatchResult:
    rule_id: int
    rule_name: str
    symbol: str
    direction: Optional[str]  # "buy" | "sell" | None (no-trade)
    matched: bool
    reasons: List[str]
    debug: Dict[str, Any]
    matched_at: datetime


def _to_str_upper(value: Any) -> Optional[str]:
    if value is None:
        return None
    if isinstance(value, str):
        return value.strip().upper()
    return str(value).strip().upper()


def parse_signal(item: Dict[str, Any]) -> Signal:
    """
    Parse one signal object using all_signals.json as the canonical schema.
    Extra/unknown fields are preserved in Signal.raw for UI transparency.
    """
    symbol = str(item.get("symbol", "")).strip().upper()
    bias = _to_str_upper(item.get("bias")) or ""
    market_phase = _to_str_upper(item.get("market_phase"))
    confidence = item.get("confidence")
    is_stale = item.get("is_stale")
    price = item.get("price")

    tf_map: Dict[Timeframe, TimeframeSignal] = {}
    timeframes = item.get("timeframes") or {}
    if isinstance(timeframes, dict):
        for tf, tf_payload in timeframes.items():
            if not isinstance(tf_payload, dict):
                continue
            tf_map[str(tf).strip().upper()] = TimeframeSignal(
                confidence=tf_payload.get("confidence"),
                entry=tf_payload.get("entry"),
                risk_reward=tf_payload.get("risk_reward"),
                signal=_to_str_upper(tf_payload.get("signal")) or "NEUTRAL",
                stop_loss=tf_payload.get("stop_loss"),
                strength=tf_payload.get("strength"),
                take_profit=tf_payload.get("take_profit"),
                trend=_to_str_upper(tf_payload.get("trend")),
            )

    return Signal(
        symbol=symbol,
        bias=bias,
        market_phase=market_phase,
        confidence=confidence if isinstance(confidence, (int, float)) else None,
        is_stale=is_stale if isinstance(is_stale, bool) else None,
        price=price if isinstance(price, (int, float)) else None,
        timeframes=tf_map,
        raw=item,
    )


def parse_signals(payload: Any) -> List[Signal]:
    """
    Parse API payload into a list of Signal objects.

    Supports:
    - list[dict] (like all_signals.json)
    - dict with "data"/"results"/"items"/"symbols" being list[dict]
    """
    items: Any = payload
    if isinstance(payload, dict):
        for key in ("data", "results", "items", "symbols"):
            if key in payload:
                items = payload.get(key)
                break

    if not isinstance(items, list):
        return []

    signals: List[Signal] = []
    for item in items:
        if isinstance(item, dict):
            s = parse_signal(item)
            if s.symbol:
                signals.append(s)
    return signals

