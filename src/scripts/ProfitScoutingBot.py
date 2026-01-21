import MetaTrader5 as mt5
import time
import logging
import os
import signal as signal_module
from typing import Dict, List, Tuple, Optional, Any
from dataclasses import dataclass
import json
from pathlib import Path
import sys
from enum import Enum
from datetime import datetime
from collections import defaultdict

# Add project root to Python path
project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from src.config.config import load_config
from src.config import get_config_manager, initialize_from_static_config

# Constants for MetaTrader5 return codes and symbols
class MT5ReturnCode:
    TRADE_RETCODE_DONE = mt5.TRADE_RETCODE_DONE
    TRADE_ACTION_DEAL = mt5.TRADE_ACTION_DEAL
    ORDER_TYPE_BUY = mt5.ORDER_TYPE_BUY
    ORDER_TYPE_SELL = mt5.ORDER_TYPE_SELL

class DisplaySymbols:
    GREATER_EQUAL = '>='
    PROFIT_UP = '↑'
    PROFIT_DOWN = '↓'
    PROFIT_UNCHANGED = '-'

logger = logging.getLogger(__name__)

class OrderTimeType(Enum):
    GTC = mt5.ORDER_TIME_GTC
    DAY = mt5.ORDER_TIME_DAY
    SPECIFIED = mt5.ORDER_TIME_SPECIFIED

class OrderFillingType(Enum):
    FOK = mt5.ORDER_FILLING_FOK
    IOC = mt5.ORDER_FILLING_IOC
    RETURN = mt5.ORDER_FILLING_RETURN

@dataclass
class ProfitDisplayConfig:
    enabled: bool
    show_pairs: bool
    show_total: bool
    min_profit_change: float

@dataclass
class ProgressIndicatorConfig:
    enabled: bool
    symbol: str
    interval: int
    profit_display: ProfitDisplayConfig

@dataclass
class LoggingConfig:
    file_path: str
    level: str
    format: str
    progress_indicator: ProgressIndicatorConfig

class TradingConfig:
    """Configuration class for Profit Scouting Bot using main config"""
    
    def __init__(self):
        # Load main configuration and seed runtime config manager
        main_config = load_config()
        initialize_from_static_config(main_config)
        self.profit_scouting_config = main_config['profit_scouting']
        self.config_manager = get_config_manager()
        
        # Set trading parameters from main config
        self.target_profit_pair = self.profit_scouting_config['target_profit_pair']
        self.target_profit_position = self.profit_scouting_config['target_profit_position']
        self.total_target_profit = self.profit_scouting_config['total_target_profit']
        self.order_deviation = self.profit_scouting_config['order_deviation']
        self.magic_number = self.profit_scouting_config['magic_number']
        self.check_interval = self.profit_scouting_config['check_interval']
        self.max_retries = self.profit_scouting_config['max_retries']
        self.retry_delay = self.profit_scouting_config['retry_delay']
        self._config_fields = {
            'target_profit_pair': 'target_profit_pair',
            'target_profit_position': 'target_profit_position',
            'total_target_profit': 'total_target_profit',
            'order_deviation': 'order_deviation',
            'magic_number': 'magic_number',
            'check_interval': 'check_interval',
            'max_retries': 'max_retries',
            'retry_delay': 'retry_delay'
        }
        
        # Set order defaults
        self.order_time_type = OrderTimeType.GTC
        self.order_filling_type = OrderFillingType.IOC
        
        # Set logging config
        self.logging = LoggingConfig(
            file_path='profit_scouting.log',
            level='INFO',
            format='%(asctime)s - %(levelname)s - %(message)s',
            progress_indicator=ProgressIndicatorConfig(
                enabled=True,
                symbol=".",
                interval=50,
                profit_display=ProfitDisplayConfig(
                    enabled=True,
                    show_pairs=True,
                    show_total=True,
                    min_profit_change=0.01
                )
            )
        )

    def apply_runtime_updates(self, updates: Dict[str, Any]) -> List[str]:
        """Apply runtime config updates and return updated keys."""
        if not updates:
            return []

        updated_keys = []
        for key, attr in self._config_fields.items():
            if key in updates and updates[key] is not None:
                current_value = getattr(self, attr)
                updated_value = type(current_value)(updates[key])
                if updated_value != current_value:
                    setattr(self, attr, updated_value)
                    updated_keys.append(key)

        return updated_keys

class ProgressIndicator:
    def __init__(self, config: ProgressIndicatorConfig):
        self.config = config
        self.count = 0
        self.last_newline = 0
        self.last_total_profit = 0.0
        self.last_pair_profits = defaultdict(float)

    def _should_show_profit(self, current_profit: float, last_profit: float) -> bool:
        """Determine if profit should be shown based on minimum change threshold."""
        return (abs(current_profit - last_profit) >= self.config.profit_display.min_profit_change
                or self.count % self.config.interval == 0)

    def _get_profit_trend(self, current_profit: float, last_profit: float) -> str:
        """Get trend indicator for profit change."""
        if abs(current_profit - last_profit) < self.config.profit_display.min_profit_change:
            return DisplaySymbols.PROFIT_UNCHANGED
        return DisplaySymbols.PROFIT_UP if current_profit > last_profit else DisplaySymbols.PROFIT_DOWN

    def format_profit(self, profit: float, last_profit: float = 0.0) -> str:
        """Format profit with color and trend indicator."""
        trend = self._get_profit_trend(profit, last_profit)
        if profit > 0:
            return f"\033[32m{profit:+.2f} {trend}\033[0m"  # Green for positive
        elif profit < 0:
            return f"\033[31m{profit:.2f} {trend}\033[0m"   # Red for negative
        return f"{profit:.2f} {trend}"                      # Default color for zero

    def update(self, pair_profits: Dict[str, float], total_profit: float) -> None:
        if not self.config.enabled:
            return
            
        self.count += 1
        show_profits = False
        
        # Check if we should show profits
        if self.config.profit_display.enabled:
            show_total = (self.config.profit_display.show_total and 
                         self._should_show_profit(total_profit, self.last_total_profit))
            
            show_pairs = self.config.profit_display.show_pairs and any(
                self._should_show_profit(curr_profit, self.last_pair_profits[pair])
                for pair, curr_profit in pair_profits.items()
            )
            
            show_profits = show_total or show_pairs or self.count % self.config.interval == 0
        
        # Print progress dot
        print(self.config.symbol, end='', flush=True)
        
        # Show profits if needed
        if show_profits:
            timestamp = datetime.now().strftime('%H:%M:%S')
            profit_str = []
            
            if self.config.profit_display.show_total:
                profit_str.append(f"Total: {self.format_profit(total_profit, self.last_total_profit)}")
            
            if self.config.profit_display.show_pairs:
                pair_profits_str = [
                    f"{pair}: {self.format_profit(profit, self.last_pair_profits[pair])}"
                    for pair, profit in sorted(pair_profits.items())
                    if self._should_show_profit(profit, self.last_pair_profits[pair])
                ]
                if pair_profits_str:
                    profit_str.extend(pair_profits_str)
            
            print(f" [{timestamp}] {' | '.join(profit_str)}")
            self.last_newline = self.count
            self.last_total_profit = total_profit
            self.last_pair_profits.update(pair_profits)
        elif self.count - self.last_newline >= self.config.interval:
            print(f" [{datetime.now().strftime('%H:%M:%S')}]")
            self.last_newline = self.count

def setup_logging(config: LoggingConfig) -> None:
    """Configure logging based on config settings."""
    logging.basicConfig(
        level=getattr(logging, config.level),
        format=config.format,
        handlers=[
            logging.FileHandler(config.file_path, encoding='utf-8'),
            logging.StreamHandler(sys.stdout)
        ]
    )

class MT5ConnectionManager:
    def __init__(self, config: TradingConfig):
        self.config = config
        self._initialize_connection()

    def _initialize_connection(self) -> None:
        for attempt in range(self.config.max_retries):
            try:
                if not mt5.initialize():
                    raise ConnectionError("MT5 initialization failed")
                logger.info("Successfully connected to MetaTrader 5")
                return
            except Exception as e:
                logger.error(f"MT5 connection attempt {attempt + 1} failed: {e}")
                if attempt < self.config.max_retries - 1:
                    time.sleep(self.config.retry_delay)
                else:
                    raise ConnectionError("Failed to connect to MetaTrader 5 after maximum retries")

    def ensure_connection(self) -> bool:
        try:
            if not mt5.terminal_info():
                logger.warning("MT5 connection lost, attempting to reconnect...")
                self._initialize_connection()
            return True
        except Exception as e:
            logger.error(f"Failed to verify MT5 connection: {e}")
            return False

    def shutdown(self) -> None:
        try:
            mt5.shutdown()
            logger.info("MT5 connection closed successfully")
        except Exception as e:
            logger.error(f"Error during MT5 shutdown: {e}")

class ProfitMonitor:
    def __init__(self, config: TradingConfig):
        self.config = config
        self.connection_manager = MT5ConnectionManager(config)
        self.pair_profits: Dict[str, List[Tuple[int, float]]] = {}
        self.total_profit: float = 0.0
        self.progress = ProgressIndicator(config.logging.progress_indicator)
        self.config_manager = config.config_manager
        self.config_signal_file = os.path.join(project_root, 'config', 'config_changed.signal')
        self.last_config_check = 0
        self.config_check_interval = 3

    def reload_config_if_changed(self) -> bool:
        """Reload profit scouting config when the dashboard signals changes."""
        try:
            current_time = time.time()
            if current_time - self.last_config_check < self.config_check_interval:
                return False

            self.last_config_check = current_time

            if not os.path.exists(self.config_signal_file):
                return False

            signal_mtime = os.path.getmtime(self.config_signal_file)
            if current_time - signal_mtime >= 60:
                return False

            updates = self.config_manager.get_profit_scouting_config()
            updates = {k: v for k, v in updates.items() if k != '_metadata'}
            changed_keys = self.config.apply_runtime_updates(updates)
            if changed_keys:
                logger.info("Profit scouting config updated: %s", ", ".join(changed_keys))

            try:
                os.remove(self.config_signal_file)
            except Exception:
                pass

            return bool(changed_keys)
        except Exception as e:
            logger.error("Error reloading profit scouting config: %s", e)
            return False

    def get_open_positions(self) -> Optional[tuple]:
        try:
            return mt5.positions_get()
        except Exception as e:
            logger.error(f"Error getting open positions: {e}")
            return None

    def create_close_request(self, position: Any) -> Dict[str, Any]:
        """Create a standardized order request for closing a position."""
        return {
            "action": MT5ReturnCode.TRADE_ACTION_DEAL,
            "position": position.ticket,
            "symbol": position.symbol,
            "volume": position.volume,
            "type": (MT5ReturnCode.ORDER_TYPE_SELL 
                    if position.type == MT5ReturnCode.ORDER_TYPE_BUY 
                    else MT5ReturnCode.ORDER_TYPE_BUY),
            "deviation": self.config.order_deviation,
            "magic": self.config.magic_number,
            "comment": "Auto Close",
            "type_time": self.config.order_time_type.value,
            "type_filling": self.config.order_filling_type.value,
        }

    def close_position(self, ticket: int) -> bool:
        try:
            position = mt5.positions_get(ticket=ticket)
            if not position:
                logger.warning(f"Position {ticket} not found")
                return False

            request = self.create_close_request(position[0])
            result = mt5.order_send(request)
            
            if result and result.retcode == MT5ReturnCode.TRADE_RETCODE_DONE:
                logger.info(f"Successfully closed position {ticket}")
                return True
            else:
                logger.error(f"Failed to close position {ticket}: {result.comment if result else 'Unknown error'}")
                return False
        except Exception as e:
            logger.error(f"Error closing position {ticket}: {e}")
            return False

    def process_positions(self) -> None:
        if not self.connection_manager.ensure_connection():
            return

        positions = self.get_open_positions()
        if positions is None:
            logger.info("No open positions")
            self.progress.update({}, 0.0)  # Update with no positions
            return

        # Reset profit tracking
        self.pair_profits.clear()
        current_pair_profits = defaultdict(float)
        positions_to_close = set()  # Track positions that should be closed
        
        # First pass: Calculate all profits and identify positions to close
        for pos in positions:
            symbol = pos.symbol
            profit = pos.profit
            ticket = pos.ticket
            
            # Track profits
            if symbol not in self.pair_profits:
                self.pair_profits[symbol] = []
            self.pair_profits[symbol].append((ticket, profit))
            current_pair_profits[symbol] += profit
            
        # Calculate total profit
        self.total_profit = sum(profit for symbol_profit in current_pair_profits.values() for profit in [symbol_profit])
        
        # Check all conditions and mark positions for closing
        for pos in positions:
            symbol = pos.symbol
            profit = pos.profit
            ticket = pos.ticket
            
            # Check individual position profit target
            if profit >= self.config.target_profit_position:
                positions_to_close.add(ticket)
                logger.info(f"Position {ticket} marked for closing: individual profit target met ({profit} >= {self.config.target_profit_position})")
            
            # Check pair profit target
            pair_profit = current_pair_profits[symbol]
            if pair_profit >= self.config.target_profit_pair:
                # Mark all positions of this pair for closing
                for pair_ticket, _ in self.pair_profits[symbol]:
                    positions_to_close.add(pair_ticket)
                    logger.info(f"Position {pair_ticket} marked for closing: pair profit target met ({pair_profit} >= {self.config.target_profit_pair})")
            
            # Check total profit target
            if self.total_profit >= self.config.total_target_profit:
                # Mark all positions for closing when they're profitable
                if profit > 0:
                    positions_to_close.add(ticket)
                    logger.info(f"Position {ticket} marked for closing: total profit target met ({self.total_profit} >= {self.config.total_target_profit})")
        
        # Close all marked positions
        for ticket in positions_to_close:
            if self.close_position(ticket):
                logger.info(f"Successfully closed position {ticket}")
            else:
                logger.warning(f"Failed to close position {ticket}")
        
        # Update progress indicator with current profits
        self.progress.update(dict(current_pair_profits), self.total_profit)

    def run(self) -> None:
        logger.info("Starting Profit Monitor")
        try:
            while True:
                try:
                    self.reload_config_if_changed()
                    self.process_positions()
                    time.sleep(self.config.check_interval)
                except Exception as e:
                    logger.error(f"Error in main loop: {e}")
                    time.sleep(self.config.retry_delay)
        except KeyboardInterrupt:
            logger.info("Shutting down Profit Monitor")
        finally:
            self.connection_manager.shutdown()


class ProfitScoutingService:
    """Service wrapper for the profit scouting bot."""

    def __init__(self):
        self.monitor: Optional[ProfitMonitor] = None
        self.running = False

    def start(self) -> None:
        """Start the profit scouting bot service."""
        try:
            config = TradingConfig()
            setup_logging(config.logging)

            logger.info("=" * 60)
            logger.info("STARTING AUTONOMOUS PROFIT SCOUTING BOT")
            logger.info("=" * 60)
            logger.info("Start time: %s", datetime.now().strftime('%Y-%m-%d %H:%M:%S'))

            self.monitor = ProfitMonitor(config)
            self.running = True

            try:
                signal_module.signal(signal_module.SIGINT, self._signal_handler)
                signal_module.signal(signal_module.SIGTERM, self._signal_handler)
            except Exception:
                # Signal handling may not be available in all environments (e.g., Windows services)
                pass

            self._print_config_summary(config)
            logger.info("Starting monitoring loop...")
            self.monitor.run()
        except KeyboardInterrupt:
            logger.info("Received keyboard interrupt")
            self._shutdown()
        except Exception as e:
            logger.error("Fatal error in profit scouting service: %s", str(e))
            self._shutdown()

    def _signal_handler(self, signum, frame):
        logger.info("Received signal %s, initiating shutdown...", signum)
        self._shutdown()

    def _shutdown(self):
        if self.running:
            logger.info("Shutting down profit scouting service...")
            self.running = False
            if self.monitor:
                self.monitor.connection_manager.shutdown()

            logger.info("=" * 60)
            logger.info("PROFIT SCOUTING SERVICE STOPPED")
            logger.info("=" * 60)
            logger.info("Stop time: %s", datetime.now().strftime('%Y-%m-%d %H:%M:%S'))
        sys.exit(0)

    def _print_config_summary(self, config: TradingConfig) -> None:
        logger.info("-" * 40)
        logger.info("CONFIGURATION SUMMARY")
        logger.info("-" * 40)
        logger.info("Target Profit (Position): %s", config.target_profit_position)
        logger.info("Target Profit (Pair): %s", config.target_profit_pair)
        logger.info("Target Profit (Total): %s", config.total_target_profit)
        logger.info("Check Interval: %s seconds", config.check_interval)
        logger.info("Order Deviation: %s", config.order_deviation)
        logger.info("Magic Number: %s", config.magic_number)
        logger.info("Max Retries: %s", config.max_retries)
        logger.info("Retry Delay: %s seconds", config.retry_delay)
        logger.info("-" * 40)

def main() -> None:
    print("Profit Scouting Bot - Autonomous Service")
    print("Press Ctrl+C to stop")
    print()
    service = ProfitScoutingService()
    service.start()


if __name__ == "__main__":
    main()
