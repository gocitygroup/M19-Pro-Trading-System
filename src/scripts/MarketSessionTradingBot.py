"""
Copyright (c) 2025 GocityGroup. All Rights Reserved.

PROPRIETARY SOFTWARE - LICENSE REQUIRED

This software is proprietary and protected by copyright. Unauthorized use, 
copying, distribution, or modification is strictly prohibited and may result 
in legal action.

A valid license must be purchased for:
- Personal use (Personal License)
- Corporate/business use (Corporate License)
- Reselling or distribution (Reseller License)

For license purchases and inquiries, contact GocityGroup.
See LICENSE file for complete terms and conditions.
"""

import os
import sys

# Add project root to Python path (must be done before other imports)
project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

import MetaTrader5 as mt5
import pandas as pd
import time
import datetime
import pytz
from datetime import UTC
import logging
import sqlite3
from typing import Dict, List, Tuple

from src.config.config import load_config, LOGGING_CONFIG, TRADING_SESSIONS

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format=LOGGING_CONFIG['format'],
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler(LOGGING_CONFIG['market_sessions_log'])
    ]
)

# Note: ConfigWatcher import removed as it's not used and module doesn't exist
# from utils.config_watcher import ConfigWatcher

class MarketSessionTrader:
    def __init__(self):
        # Load configuration
        self.config = load_config()
        trading_config = self.config['trading_bot']
        
        # Initialize parameters from config
        self.max_positions = trading_config['max_positions']
        self.volume = trading_config['volume']
        self.scalp_multiplier = trading_config['scalp_multiplier']
        self.base_entry_pips = trading_config['base_entry_pips']
        self.min_spread_multiplier = trading_config['min_spread_multiplier']
        self.order_expiry_minutes = trading_config['order_expiry_minutes']
        self.session_check_interval = trading_config['session_check_interval']
        self.initialized = False
        
        # Set up timezone handling
        self.trading_tz = pytz.UTC
        self.local_tz = self.config['timezone']['local_timezone_obj']
        
        # Database configuration (project root to keep consistent across modules)
        self.db_path = os.path.join(project_root, self.config['db']['path'])
        self.sessions_synced = False
        self.sync_sessions_with_config()
        
        # Initialize last check time
        self.last_session_check = 0
        
        # Bot status file path
        self.status_file = os.path.join(project_root, 'bot_status.json')

    def get_db_connection(self):
        """Get a database connection"""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn
    
    def update_bot_status(self, connected: bool, message: str = None):
        """Update bot status file for web interface monitoring"""
        try:
            status = {
                'is_connected': connected,
                'is_paused': False,  # Keep existing field for compatibility
                'last_updated': datetime.datetime.now(UTC).isoformat(),
                'bot_type': 'MarketSessionTradingBot',
                'message': message or ('Connected' if connected else 'Disconnected')
            }
            with open(self.status_file, 'w') as f:
                import json
                json.dump(status, f, indent=2)
        except Exception as e:
            logging.error(f"Error updating bot status: {str(e)}")
    
    def sync_sessions_with_config(self):
        """
        Ensure trading sessions and pair mappings reflect config definitions.
        Only uses pairs that exist in the database - never creates new pairs.
        Uses batch operations for better performance.
        """
        if self.sessions_synced:
            return
        try:
            conn = self.get_db_connection()
            cursor = conn.cursor()
            
            # Upsert sessions based on configuration
            for session in TRADING_SESSIONS:
                name = session['name']
                start_time = session['start_time']
                end_time = session['end_time']
                volatility = session.get('volatility_factor', 1.0)
                
                # Normalize times to HH:MM:SS for SQLite time columns
                if len(start_time) == 5:
                    start_time = f"{start_time}:00"
                if len(end_time) == 5:
                    end_time = f"{end_time}:00"
                
                cursor.execute('''
                    INSERT OR IGNORE INTO trading_sessions (name, start_time, end_time, volatility_factor, is_active)
                    VALUES (?, ?, ?, ?, 1)
                ''', (name, start_time, end_time, volatility))
                
                cursor.execute('''
                    UPDATE trading_sessions
                    SET start_time = ?, end_time = ?, volatility_factor = ?, is_active = 1
                    WHERE name = ?
                ''', (start_time, end_time, volatility, name))
            
            # Only map existing pairs from database - never create new pairs
            session_ids = [row['id'] for row in cursor.execute('SELECT id FROM trading_sessions').fetchall()]
            pair_ids = [row['id'] for row in cursor.execute('SELECT id FROM currency_pairs WHERE is_active = 1').fetchall()]
            
            # Batch insert for better performance
            if session_ids and pair_ids:
                mappings = [(session_id, pair_id) for session_id in session_ids for pair_id in pair_ids]
                cursor.executemany('''
                    INSERT OR IGNORE INTO session_pairs (session_id, pair_id, trade_direction)
                    VALUES (?, ?, 'neutral')
                ''', mappings)
            
            conn.commit()
            self.sessions_synced = True
            logging.info(f"Synced {len(session_ids)} sessions with {len(pair_ids)} pairs from database")
        except Exception as e:
            logging.error(f"Error syncing sessions with config: {str(e)}")
        finally:
            if 'conn' in locals():
                conn.close()
        
    def get_current_time(self, tz=None):
        """Get current time in specified timezone (defaults to trading timezone)"""
        current = datetime.datetime.now(UTC)
        if tz is None:
            tz = self.trading_tz
        return current.astimezone(tz)
        
    def convert_session_time(self, time_str: str, to_tz=None) -> datetime.time:
        """Convert session time between timezones"""
        if to_tz is None:
            to_tz = self.trading_tz
            
        # Parse the time string
        time_obj = datetime.datetime.strptime(time_str, '%H:%M:%S').time()
        
        # Create a datetime object for today with this time in UTC
        utc_dt = datetime.datetime.combine(
            datetime.datetime.now(UTC).date(),
            time_obj
        ).replace(tzinfo=UTC)
        
        # Convert to target timezone
        converted = utc_dt.astimezone(to_tz)
        return converted.time()

    def initialize_mt5(self):
        """Initialize MT5 connection"""
        try:
            logging.info(f"Initializing MT5 with timezone: {self.local_tz.zone}")
            logging.info(f"Server time (UTC): {self.get_current_time(pytz.UTC)}")
            logging.info(f"Local time: {self.get_current_time(self.local_tz)}")
            
            config = self.config
            mt5_config = config['mt5']
            
            if not mt5.initialize():
                raise RuntimeError(f"Initialize() failed: {mt5.last_error()}")
            
            # Login if credentials are provided
            if mt5_config['server'] and mt5_config['login'] and mt5_config['password']:
                if not mt5.login(
                    login=mt5_config['login'],
                    password=mt5_config['password'],
                    server=mt5_config['server']
                ):
                    raise RuntimeError(f"Login failed: {mt5.last_error()}")
            
            # Verify connection
            if not mt5.terminal_info():
                raise RuntimeError("Terminal info not available")
                
            account_info = mt5.account_info()
            if not account_info:
                raise RuntimeError("Failed to get account info")
                
            logging.info(f"Connected to: {account_info.server}")
            logging.info(f"Account: {account_info.login}")
            logging.info(f"Balance: {account_info.balance}")
            
            self.initialized = True
            logging.info("MT5 initialized successfully")
            self.update_bot_status(True, f"Connected to MT5 - Account: {account_info.login}, Server: {account_info.server}")
            
        except Exception as e:
            logging.error(f"MT5 initialization failed: {str(e)}")
            self.initialized = False
            self.update_bot_status(False, f"Connection failed: {str(e)}")
            raise

    def verify_symbol(self, symbol: str) -> bool:
        """Verify if symbol is available and enabled for trading"""
        try:
            symbol_info = mt5.symbol_info(symbol)
            if symbol_info is None:
                logging.error(f"Symbol {symbol} not found")
                return False
                
            if not symbol_info.visible:
                if not mt5.symbol_select(symbol, True):
                    logging.error(f"Symbol {symbol} selection failed")
                    return False
                    
            if not symbol_info.trade_mode == mt5.SYMBOL_TRADE_MODE_FULL:
                logging.error(f"Symbol {symbol} not available for full trading")
                return False
                
            return True
            
        except Exception as e:
            logging.error(f"Error verifying symbol {symbol}: {str(e)}")
            return False

    def get_symbol_info(self, symbol: str) -> Dict:
        """Get symbol information including spread"""
        try:
            if not self.verify_symbol(symbol):
                return None
                
            info = mt5.symbol_info(symbol)
            if info is None:
                return None
                
            return {
                "spread": info.spread * info.point,
                "point": info.point,
                "digits": info.digits,
                "trade_mode": info.trade_mode
            }
        except Exception as e:
            logging.error(f"Error getting symbol info for {symbol}: {str(e)}")
            return None

    def send_order(self, order_request: Dict) -> bool:
        """Send order with proper error handling"""
        try:
            if not self.initialized:
                logging.error("MT5 not initialized")
                return False
                
            result = mt5.order_send(order_request)
            if result is None:
                error = mt5.last_error()
                logging.error(f"Order send failed: {error}")
                return False
                
            if result.retcode != mt5.TRADE_RETCODE_DONE:
                logging.error(f"Order failed: {result.retcode}, {result.comment}")
                return False
                
            logging.info(f"Order placed successfully: {result.order}")
            return True
            
        except Exception as e:
            logging.error(f"Error sending order: {str(e)}")
            return False

    def clean_expired_orders(self, symbol: str):
        """Cancel orders that have been pending for too long"""
        try:
            if not self.verify_symbol(symbol):
                return
                
            # Skip cleaning for direct market orders (max_positions = 1)
            if self.max_positions == 1:
                return
                
            orders = mt5.orders_get(symbol=symbol)
            if orders is None:
                return
                
            now = datetime.datetime.now()
            current_minutes = int((now - now.replace(hour=0, minute=0, second=0, microsecond=0)).total_seconds() / 60)
            
            for order in orders:
                try:
                    # Extract timestamp from order comment
                    if not order.comment or not order.comment.startswith("S"):
                        continue
                        
                    try:
                        # Parse minutes from comment (format: SXXXX where XXXX is minutes since midnight)
                        order_minutes = int(order.comment[1:])
                        
                        # Handle orders across midnight
                        if order_minutes > current_minutes:
                            order_age = (current_minutes + 1440 - order_minutes)  # 1440 = minutes in a day
                        else:
                            order_age = current_minutes - order_minutes
                        
                        if order_age > self.order_expiry_minutes:
                            request = {
                                "action": mt5.TRADE_ACTION_REMOVE,
                                "order": order.ticket,
                                "comment": "Expired order"
                            }
                            self.send_order(request)
                            logging.info(f"Cancelled expired order {order.ticket} for {symbol}, age: {order_age:.1f} minutes")
                            
                    except (ValueError, IndexError) as e:
                        logging.warning(f"Could not parse minutes from order comment: {order.comment}, Error: {str(e)}")
                        continue
                        
                except Exception as e:
                    logging.error(f"Error processing order {order.ticket}: {str(e)}")
                    continue
                    
        except Exception as e:
            logging.error(f"Error cleaning expired orders for {symbol}: {str(e)}")

    def combine_session_pairs(self, active_sessions: List[Tuple[str, Dict]]) -> Dict[str, List[str]]:
        """Combine trading pairs from all active sessions"""
        try:
            combined_pairs = {
                'buy_pairs': set(),
                'sell_pairs': set()
            }
            
            for _, session in active_sessions:
                combined_pairs['buy_pairs'].update(session['pairs'].keys())
                combined_pairs['sell_pairs'].update(session['pairs'].keys())
                
            return {
                'buy_pairs': list(combined_pairs['buy_pairs']),
                'sell_pairs': list(combined_pairs['sell_pairs'])
            }
            
        except Exception as e:
            logging.error(f"Error combining session pairs: {str(e)}")
            return {'buy_pairs': [], 'sell_pairs': []}

    def get_active_sessions(self) -> List[Tuple[str, Dict]]:
        """Get currently active trading sessions and their pairs"""
        try:
            current_time = self.get_current_time().time()
            conn = self.get_db_connection()
            
            active_sessions = []
            try:
                # Get all sessions
                cursor = conn.execute('''
                    SELECT id, name, time(start_time) as start_time, time(end_time) as end_time,
                           volatility_factor
                    FROM trading_sessions
                    WHERE is_active = 1
                ''')
                sessions = cursor.fetchall()
                
                for session in sessions:
                    start_time = datetime.datetime.strptime(session['start_time'], '%H:%M:%S').time()
                    end_time = datetime.datetime.strptime(session['end_time'], '%H:%M:%S').time()
                    
                    # Check if session is active
                    is_active = False
                    if start_time < end_time:
                        is_active = start_time <= current_time < end_time
                    else:  # Session crosses midnight
                        is_active = current_time >= start_time or current_time < end_time
                    
                    if is_active:
                        # Get pairs for this session
                        cursor = conn.execute('''
                            SELECT cp.symbol, sp.trade_direction
                            FROM session_pairs sp
                            JOIN currency_pairs cp ON cp.id = sp.pair_id
                            WHERE sp.session_id = ? 
                            AND cp.is_active = 1
                            AND sp.trade_direction != 'neutral'
                        ''', (session['id'],))
                        pairs = cursor.fetchall()
                        
                        session_data = {
                            'name': session['name'],
                            'start_time': start_time,
                            'end_time': end_time,
                            'volatility_factor': session['volatility_factor'],
                            'buy_pairs': [row['symbol'] for row in pairs if row['trade_direction'] == 'buy'],
                            'sell_pairs': [row['symbol'] for row in pairs if row['trade_direction'] == 'sell']
                        }
                        active_sessions.append((session['name'], session_data))
                
                return active_sessions
                
            finally:
                conn.close()
                
        except Exception as e:
            logging.error(f"Error getting active sessions: {str(e)}")
            return []

    def manage_session_orders(self):
        """Manage orders based on active sessions"""
        try:
            # Get active sessions and their pairs
            active_sessions = self.get_active_sessions()
            if not active_sessions:
                logging.info("No active sessions found")
                return
                
            logging.info(f"Found {len(active_sessions)} active sessions")
            for session_name, session_data in active_sessions:
                logging.info(f"Processing session: {session_name}")
                logging.info(f"Buy pairs: {session_data['buy_pairs']}")
                logging.info(f"Sell pairs: {session_data['sell_pairs']}")
                
                # Process buy pairs
                for symbol in session_data['buy_pairs']:
                    if not self.verify_symbol(symbol):
                        continue
                    self.place_pending_orders(symbol, 'buy')
                    
                # Process sell pairs
                for symbol in session_data['sell_pairs']:
                    if not self.verify_symbol(symbol):
                        continue
                    self.place_pending_orders(symbol, 'sell')
                    
                # Clean up expired orders for all pairs (only for pending orders mode)
                if self.max_positions > 1:
                    all_pairs = set(session_data['buy_pairs']) | set(session_data['sell_pairs'])
                    for symbol in all_pairs:
                        self.clean_expired_orders(symbol)
                    
        except Exception as e:
            logging.error(f"Error managing session orders: {str(e)}")
            raise

    def is_session_active(self, start: datetime.time, end: datetime.time, current: datetime.time) -> bool:
        """Check if a session is currently active"""
        if start < end:
            return start <= current < end
        else:  # Session goes over midnight UTC
            return current >= start or current < end

    def get_positions_count(self, symbol: str, order_type: str) -> int:
        """Get count of active positions and pending orders for a symbol and type"""
        try:
            if not self.verify_symbol(symbol):
                return 0
                
            positions = mt5.positions_get(symbol=symbol)
            pending_orders = mt5.orders_get(symbol=symbol)
            
            total_count = 0
            
            # For direct market orders (max_positions = 1), only count actual positions
            if self.max_positions == 1:
                if positions:
                    for pos in positions:
                        if (order_type == "buy" and pos.type == mt5.POSITION_TYPE_BUY) or \
                           (order_type == "sell" and pos.type == mt5.POSITION_TYPE_SELL):
                            total_count += 1
            else:
                # For pending orders mode, count both positions and pending orders
                if positions:
                    for pos in positions:
                        if (order_type == "buy" and pos.type == mt5.POSITION_TYPE_BUY) or \
                           (order_type == "sell" and pos.type == mt5.POSITION_TYPE_SELL):
                            total_count += 1
                
                if pending_orders:
                    for order in pending_orders:
                        if order_type == "buy" and order.type in [mt5.ORDER_TYPE_BUY_LIMIT, mt5.ORDER_TYPE_BUY_STOP]:
                            total_count += 1
                        elif order_type == "sell" and order.type in [mt5.ORDER_TYPE_SELL_LIMIT, mt5.ORDER_TYPE_SELL_STOP]:
                            total_count += 1
            
            return total_count
            
        except Exception as e:
            logging.error(f"Error getting positions count for {symbol}: {str(e)}")
            return 0

    def get_30m_candle(self, symbol: str) -> Dict:
        """Get the last completed 30-minute candle"""
        try:
            if not self.verify_symbol(symbol):
                return None
                
            rates = mt5.copy_rates_from_pos(symbol, mt5.TIMEFRAME_M30, 0, 2)
            if rates is None or len(rates) < 2:
                logging.error(f"Failed to get candle data for {symbol}")
                return None
                
            # Use index 1 for the last completed candle
            candle = rates[1]
            candle_range = abs(candle['high'] - candle['low'])
            
            return {
                "high": candle["high"],
                "low": candle["low"],
                "close": candle["close"],
                "range": candle_range
            }
        except Exception as e:
            logging.error(f"Error getting candle data for {symbol}: {str(e)}")
            return None

    def calculate_daily_atr(self, symbol: str, period: int = 14) -> float:
        """Calculate Daily ATR (Average True Range)"""
        try:
            if not self.verify_symbol(symbol):
                return None

            # Get daily rates for ATR calculation
            rates = mt5.copy_rates_from_pos(symbol, mt5.TIMEFRAME_D1, 0, period + 1)
            if rates is None or len(rates) < period + 1:
                logging.error(f"Failed to get daily rates for ATR calculation for {symbol}")
                return None

            # Convert rates to pandas DataFrame
            df = pd.DataFrame(rates)
            
            # Calculate True Range
            df['high_low'] = df['high'] - df['low']
            df['high_close'] = abs(df['high'] - df['close'].shift(1))
            df['low_close'] = abs(df['low'] - df['close'].shift(1))
            
            df['tr'] = df[['high_low', 'high_close', 'low_close']].max(axis=1)
            
            # Calculate ATR
            atr = df['tr'].rolling(window=period).mean().iloc[-1]
            
            return atr
            
        except Exception as e:
            logging.error(f"Error calculating ATR for {symbol}: {str(e)}")
            return None

    def get_atr_based_stop_loss(self, symbol: str, entry_price: float, order_type: str, atr_multiplier: float = 1.0) -> float:
        """Calculate stop loss based on ATR"""
        try:
            symbol_info = self.get_symbol_info(symbol)
            if not symbol_info:
                return None
                
            # Get daily ATR
            atr = self.calculate_daily_atr(symbol)
            if not atr:
                return None
                
            # Calculate stop loss distance using ATR
            stop_distance = atr * atr_multiplier
            
            # Ensure minimum distance based on spread
            min_distance = symbol_info['spread'] * self.min_spread_multiplier
            stop_distance = max(stop_distance, min_distance)
            
            # Calculate stop loss price
            if order_type == "buy":
                stop_loss = round(entry_price - stop_distance, symbol_info['digits'])
            else:  # sell
                stop_loss = round(entry_price + stop_distance, symbol_info['digits'])
                
            return stop_loss
            
        except Exception as e:
            logging.error(f"Error calculating ATR-based stop loss for {symbol}: {str(e)}")
            return None

    def get_atr_based_take_profit(self, symbol: str, entry_price: float, order_type: str, atr_multiplier: float = 1.0) -> float:
        """Calculate take profit based on ATR"""
        try:
            symbol_info = self.get_symbol_info(symbol)
            if not symbol_info:
                return None
                
            # Get daily ATR
            atr = self.calculate_daily_atr(symbol)
            if not atr:
                return None
                
            # Calculate take profit distance using ATR
            tp_distance = atr * atr_multiplier
            
            # Calculate take profit price
            if order_type == "buy":
                take_profit = round(entry_price + tp_distance, symbol_info['digits'])
            else:  # sell
                take_profit = round(entry_price - tp_distance, symbol_info['digits'])
                
            return take_profit
            
        except Exception as e:
            logging.error(f"Error calculating ATR-based take profit for {symbol}: {str(e)}")
            return None

    def calculate_order_levels(self, symbol: str, current_price: float, order_type: str, candle: Dict) -> Tuple[float, float]:
        """Calculate scalping order levels based on current price and candle range"""
        try:
            symbol_info = self.get_symbol_info(symbol)
            if not symbol_info:
                return None, None
                
            pip_value = 0.0001 if not "JPY" in symbol else 0.01
            
            # Calculate minimum distance based on spread
            min_distance = symbol_info['spread'] * self.min_spread_multiplier
            
            # Use candle range for dynamic entry distances
            candle_range = candle['range']
            volatility_mult = 1.2 if "JPY" in symbol else 1.0
            
            # Scale entry distances based on candle range and volatility
            base_distance = max(
                self.base_entry_pips * pip_value,
                candle_range * 0.1  # 10% of candle range
            ) * volatility_mult * self.scalp_multiplier
            
            # Ensure distance is not smaller than minimum spread-based distance
            entry_distance = max(base_distance, min_distance)
            
            if order_type == "buy":
                limit_price = round(current_price - entry_distance, symbol_info['digits'])
                stop_price = round(current_price + entry_distance, symbol_info['digits'])
            else:  # sell
                limit_price = round(current_price + entry_distance, symbol_info['digits'])
                stop_price = round(current_price - entry_distance, symbol_info['digits'])
                
            return limit_price, stop_price
            
        except Exception as e:
            logging.error(f"Error calculating order levels for {symbol}: {str(e)}")
            return None, None

    def calculate_trailing_stop(self, symbol: str, candle: Dict, order_type: str, entry_price: float) -> float:
        """Calculate trailing stop based on last 30-minute candle range"""
        try:
            symbol_info = self.get_symbol_info(symbol)
            if not symbol_info:
                return None
                
            candle_range = candle['range']
            pip_value = 0.0001 if not "JPY" in symbol else 0.01
            
            # Minimum trailing stop based on spread
            min_trailing_distance = symbol_info['spread'] * self.min_spread_multiplier
            
            # Calculate trailing stop distance
            base_trailing_distance = max(5 * pip_value, candle_range * 0.5)
            trailing_distance = max(base_trailing_distance, min_trailing_distance)
            
            if order_type == "buy":
                trailing_stop = round(entry_price - trailing_distance, symbol_info['digits'])
            else:  # sell
                trailing_stop = round(entry_price + trailing_distance, symbol_info['digits'])
                
            return trailing_stop
            
        except Exception as e:
            logging.error(f"Error calculating trailing stop for {symbol}: {str(e)}")
            return None

    def get_session_volatility_multiplier(self, active_sessions: List[Tuple[str, Dict]]) -> float:
        """Calculate volatility multiplier based on active sessions"""
        if not active_sessions:
            return 1.0
            
        # Get maximum volatility factor from active sessions
        max_volatility = max(session_data['volatility_factor'] 
                           for _, session_data in active_sessions)
        
        return max_volatility

    def place_direct_market_order(self, symbol: str, order_type: str, volatility_mult: float):
        """Place direct market order with automatic stop loss and take profit"""
        try:
            if not self.verify_symbol(symbol):
                return
                
            # Get current price
            tick = mt5.symbol_info_tick(symbol)
            if not tick:
                logging.error(f"Failed to get tick data for {symbol}")
                return
                
            current_price = tick.ask if order_type == "buy" else tick.bid
            
            # Calculate ATR-based stop loss and take profit
            sl = self.get_atr_based_stop_loss(symbol, current_price, order_type, atr_multiplier=0.30 * volatility_mult)
            tp = self.get_atr_based_take_profit(symbol, current_price, order_type, atr_multiplier=0.30 * volatility_mult)
            
            if not sl or not tp:
                logging.error(f"Failed to calculate SL/TP levels for {symbol}")
                return
            
            # Generate timestamp for order comments
            now = datetime.datetime.now()
            minutes_since_midnight = int((now - now.replace(hour=0, minute=0, second=0, microsecond=0)).total_seconds() / 60)
            
            # Create direct market order
            if order_type == "buy":
                order_request = {
                    "action": mt5.TRADE_ACTION_DEAL,
                    "symbol": symbol,
                    "volume": self.volume,
                    "type": mt5.ORDER_TYPE_BUY,
                    "price": current_price,
                    "sl": sl,
                    "tp": tp,
                    "deviation": 10,
                    "magic": 123456,
                    "type_time": mt5.ORDER_TIME_GTC,
                    "type_filling": mt5.ORDER_FILLING_IOC,
                    "comment": f"DM{minutes_since_midnight}"
                }
            else:  # sell
                order_request = {
                    "action": mt5.TRADE_ACTION_DEAL,
                    "symbol": symbol,
                    "volume": self.volume,
                    "type": mt5.ORDER_TYPE_SELL,
                    "price": current_price,
                    "sl": sl,
                    "tp": tp,
                    "deviation": 10,
                    "magic": 123456,
                    "type_time": mt5.ORDER_TIME_GTC,
                    "type_filling": mt5.ORDER_FILLING_IOC,
                    "comment": f"DM{minutes_since_midnight}"
                }
            
            # Send the order
            if self.send_order(order_request):
                logging.info(f"Direct market {order_type} order placed for {symbol} at {current_price}, SL: {sl}, TP: {tp}")
            else:
                logging.error(f"Failed to place direct market {order_type} order for {symbol}")
                
        except Exception as e:
            logging.error(f"Error placing direct market order for {symbol}: {str(e)}")

    def place_pending_orders(self, symbol: str, order_type: str):
        """Place pending orders for scalping or direct market orders for single position mode"""
        try:
            if not self.verify_symbol(symbol):
                return
                
            # Clean expired orders first
            self.clean_expired_orders(symbol)
            
            # Get active sessions for volatility adjustment
            active_sessions = self.get_active_sessions()
            volatility_mult = self.get_session_volatility_multiplier(active_sessions)
            
            current_positions = self.get_positions_count(symbol, order_type)
            
            if current_positions >= self.max_positions:
                logging.info(f"Maximum positions reached for {symbol} {order_type}")
                return
                
            # Check if we should place direct market orders (when max_positions = 1)
            if self.max_positions == 1:
                self.place_direct_market_order(symbol, order_type, volatility_mult)
                return
                
            # Get current price and candle data
            tick = mt5.symbol_info_tick(symbol)
            if not tick:
                logging.error(f"Failed to get tick data for {symbol}")
                return
                
            current_price = tick.ask if order_type == "buy" else tick.bid
            candle = self.get_30m_candle(symbol)
            
            if not candle:
                logging.error(f"Failed to get candle data for {symbol}")
                return
                
            # Adjust candle range based on session volatility
            candle['range'] = candle['range'] * volatility_mult
            
            limit_price, stop_price = self.calculate_order_levels(symbol, current_price, order_type, candle)
            if not limit_price or not stop_price:
                return
            
            # Generate timestamp for order comments
            now = datetime.datetime.now()
            minutes_since_midnight = int((now - now.replace(hour=0, minute=0, second=0, microsecond=0)).total_seconds() / 60)
            
            orders = []
            if order_type == "buy":
                # Calculate ATR-based stop losses and take profits with volatility adjustment
                limit_sl = self.get_atr_based_stop_loss(symbol, limit_price, "buy", atr_multiplier=0.30 * volatility_mult)
                stop_sl = self.get_atr_based_stop_loss(symbol, stop_price, "buy", atr_multiplier=0.30 * volatility_mult)
                limit_tp = self.get_atr_based_take_profit(symbol, limit_price, "buy", atr_multiplier=0.30 * volatility_mult)
                stop_tp = self.get_atr_based_take_profit(symbol, stop_price, "buy", atr_multiplier=0.30 * volatility_mult)
                
                if not all([limit_sl, stop_sl, limit_tp, stop_tp]):
                    logging.error(f"Failed to calculate SL/TP levels for {symbol}")
                    return
                
                # Buy Limit order
                buy_limit = {
                    "action": mt5.TRADE_ACTION_PENDING,
                    "symbol": symbol,
                    "volume": self.volume,
                    "type": mt5.ORDER_TYPE_BUY_LIMIT,
                    "price": limit_price,
                    "sl": limit_sl,
                    "tp": limit_tp,
                    "deviation": 10,
                    "magic": 123456,
                    "type_time": mt5.ORDER_TIME_GTC,
                    "type_filling": mt5.ORDER_FILLING_IOC,
                    "comment": f"S{minutes_since_midnight}"
                }
                orders.append(buy_limit)
                
                # Buy Stop order
                buy_stop = {
                    "action": mt5.TRADE_ACTION_PENDING,
                    "symbol": symbol,
                    "volume": self.volume,
                    "type": mt5.ORDER_TYPE_BUY_STOP,
                    "price": stop_price,
                    "sl": stop_sl,
                    "tp": stop_tp,
                    "deviation": 10,
                    "magic": 123456,
                    "type_time": mt5.ORDER_TIME_GTC,
                    "type_filling": mt5.ORDER_FILLING_IOC,
                    "comment": f"S{minutes_since_midnight}"
                }
                orders.append(buy_stop)
            else:
                # Calculate ATR-based stop losses and take profits with volatility adjustment
                limit_sl = self.get_atr_based_stop_loss(symbol, limit_price, "sell", atr_multiplier=0.30 * volatility_mult)
                stop_sl = self.get_atr_based_stop_loss(symbol, stop_price, "sell", atr_multiplier=0.30 * volatility_mult)
                limit_tp = self.get_atr_based_take_profit(symbol, limit_price, "sell", atr_multiplier=0.30 * volatility_mult)
                stop_tp = self.get_atr_based_take_profit(symbol, stop_price, "sell", atr_multiplier=0.30 * volatility_mult)
                
                if not all([limit_sl, stop_sl, limit_tp, stop_tp]):
                    logging.error(f"Failed to calculate SL/TP levels for {symbol}")
                    return
                
                # Sell Limit order
                sell_limit = {
                    "action": mt5.TRADE_ACTION_PENDING,
                    "symbol": symbol,
                    "volume": self.volume,
                    "type": mt5.ORDER_TYPE_SELL_LIMIT,
                    "price": limit_price,
                    "sl": limit_sl,
                    "tp": limit_tp,
                    "deviation": 10,
                    "magic": 123456,
                    "type_time": mt5.ORDER_TIME_GTC,
                    "type_filling": mt5.ORDER_FILLING_IOC,
                    "comment": f"S{minutes_since_midnight}"
                }
                orders.append(sell_limit)
                
                # Sell Stop order
                sell_stop = {
                    "action": mt5.TRADE_ACTION_PENDING,
                    "symbol": symbol,
                    "volume": self.volume,
                    "type": mt5.ORDER_TYPE_SELL_STOP,
                    "price": stop_price,
                    "sl": stop_sl,
                    "tp": stop_tp,
                    "deviation": 10,
                    "magic": 123456,
                    "type_time": mt5.ORDER_TIME_GTC,
                    "type_filling": mt5.ORDER_FILLING_IOC,
                    "comment": f"S{minutes_since_midnight}"
                }
                orders.append(sell_stop)

            # Send orders
            for order in orders:
                if self.get_positions_count(symbol, order_type) < self.max_positions:
                    self.send_order(order)
                    
        except Exception as e:
            logging.error(f"Error placing orders for {symbol}: {str(e)}")

    def run(self):
        """Main trading loop"""
        try:
            self.initialize_mt5()
            
            while True:
                try:
                    current_time = time.time()
                    
                    # Check sessions periodically
                    if current_time - self.last_session_check >= self.session_check_interval:
                        self.manage_session_orders()
                        self.last_session_check = current_time
                    
                    time.sleep(1)  # Prevent CPU overuse
                    
                except Exception as e:
                    logging.error(f"Error in trading loop: {str(e)}")
                    time.sleep(5)  # Wait before retrying
                    
        except KeyboardInterrupt:
            logging.info("Trading bot stopped by user")
            self.update_bot_status(False, "Trading bot stopped by user")
        except Exception as e:
            logging.error(f"Fatal error in trading bot: {str(e)}")
            self.update_bot_status(False, f"Fatal error: {str(e)}")
        finally:
            if self.initialized:
                mt5.shutdown()
                self.update_bot_status(False, "MT5 connection closed")

if __name__ == "__main__":
    trader = MarketSessionTrader()
    trader.run() 