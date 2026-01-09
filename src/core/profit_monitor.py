import sys
import MetaTrader5 as mt5
import time
import logging
from datetime import datetime
import json
import os
import math
import sqlite3

# Add project root to Python path
project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, project_root)

from src.config.config import load_config, LOGGING_CONFIG
from src.config import get_config_manager

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format=LOGGING_CONFIG['format'],
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler(LOGGING_CONFIG['profit_monitor_log'])
    ]
)

class ProfitMonitor:
    def __init__(self):
        self.initialized = False
        # Load configuration
        config = load_config()
        self.config = config['profit_monitor']
        self.mt5_config = config['mt5']
        # Get project root directory (3 levels up from profit_monitor.py)
        project_root = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
        self.db_path = os.path.join(project_root, config['db']['path'])
        
        # Configuration manager for dynamic updates
        self.config_manager = get_config_manager()
        self.config_signal_file = os.path.join(project_root, 'config', 'config_changed.signal')
        self.last_config_check = time.time()
        self.config_check_interval = 5  # Check for config changes every 5 seconds
        
        self.initialize_mt5()
    
    def reload_config_if_changed(self):
        """Check if configuration has changed and reload if necessary"""
        try:
            current_time = time.time()
            
            # Only check periodically to avoid excessive file I/O
            if current_time - self.last_config_check < self.config_check_interval:
                return False
            
            self.last_config_check = current_time
            
            # Check if signal file exists and is newer
            if os.path.exists(self.config_signal_file):
                signal_mtime = os.path.getmtime(self.config_signal_file)
                
                # If signal file is recent (within last minute), reload config
                if current_time - signal_mtime < 60:
                    new_config = self.config_manager.get_profit_monitor_config()
                    
                    # Update configuration
                    old_config = self.config.copy()
                    self.config.update(new_config)
                    
                    # Update logging level if changed
                    if old_config.get('log_level') != new_config.get('log_level'):
                        log_level = getattr(logging, new_config.get('log_level', 'INFO'))
                        logging.getLogger().setLevel(log_level)
                    
                    logging.info(f"Configuration reloaded from runtime config: {list(new_config.keys())}")
                    
                    # Remove signal file
                    try:
                        os.remove(self.config_signal_file)
                    except:
                        pass
                    
                    return True
            
            return False
            
        except Exception as e:
            logging.error(f"Error reloading configuration: {str(e)}")
            return False

    def initialize_mt5(self):
        """Initialize MT5 connection"""
        try:
            if not mt5.initialize():
                logging.error(f"Initialize() failed: {mt5.last_error()}")
                return False
            
            # Login if credentials are provided
            if self.mt5_config['server'] and self.mt5_config['login'] and self.mt5_config['password']:
                if not mt5.login(
                    login=self.mt5_config['login'],
                    password=self.mt5_config['password'],
                    server=self.mt5_config['server']
                ):
                    logging.error(f"Login failed: {mt5.last_error()}")
                    return False
            
            account_info = mt5.account_info()
            if not account_info:
                logging.error("Failed to get account info")
                return False
            
            logging.info(f"Connected to: {account_info.server}")
            logging.info(f"Account: {account_info.login}")
            
            self.initialized = True
            return True
            
        except Exception as e:
            logging.error(f"MT5 initialization failed: {str(e)}")
            return False

    def normalize_volume(self, symbol: str, volume: float) -> float:
        """Normalize the volume according to broker's requirements"""
        try:
            symbol_info = mt5.symbol_info(symbol)
            if symbol_info is None:
                return None

            # Get volume constraints
            min_volume = symbol_info.volume_min
            max_volume = symbol_info.volume_max
            volume_step = symbol_info.volume_step

            # Round to the nearest valid volume step
            normalized_volume = round(volume / volume_step) * volume_step
            
            # Ensure volume is within allowed range
            normalized_volume = max(min_volume, min(normalized_volume, max_volume))
            
            # Round to avoid floating point precision issues
            normalized_volume = round(normalized_volume, 8)
            
            return normalized_volume
        except Exception as e:
            logging.error(f"Error normalizing volume for {symbol}: {str(e)}")
            return None

    def get_open_positions(self):
        """Get all open positions"""
        try:
            positions = mt5.positions_get()
            if positions is None:
                positions = []
            return positions
        except Exception as e:
            logging.error(f"Error getting positions: {str(e)}")
            return []

    def calculate_profit_percent(self, position):
        """Calculate profit percentage for a position"""
        try:
            profit = position.profit
            # Calculate the actual position value at open
            position_value = position.volume * position.price_open
            
            # Avoid division by zero
            if position_value == 0:
                return 0
                
            return (profit / position_value) * 100
        except Exception as e:
            logging.error(f"Error calculating profit percent: {str(e)}")
            return 0

    def get_supported_filling_mode(self, symbol: str):
        """Get the supported filling mode for a symbol"""
        try:
            symbol_info = mt5.symbol_info(symbol)
            if symbol_info is None:
                return mt5.ORDER_FILLING_FOK  # Default fallback
            
            # Try to get filling mode from symbol info
            # If the constants are not available, we'll use a fallback approach
            try:
                filling_modes = symbol_info.filling_mode
                
                # Check which filling modes are supported using bitwise operations
                # These values are standard MT5 constants
                SYMBOL_FILLING_FOK = 1
                SYMBOL_FILLING_IOC = 2
                SYMBOL_FILLING_RETURN = 4
                
                if filling_modes & SYMBOL_FILLING_FOK:
                    return mt5.ORDER_FILLING_FOK
                elif filling_modes & SYMBOL_FILLING_IOC:
                    return mt5.ORDER_FILLING_IOC
                elif filling_modes & SYMBOL_FILLING_RETURN:
                    return mt5.ORDER_FILLING_RETURN
                else:
                    return mt5.ORDER_FILLING_FOK
                    
            except AttributeError:
                # If filling_mode attribute doesn't exist, use default
                return mt5.ORDER_FILLING_FOK
                
        except Exception as e:
            logging.error(f"Error getting filling mode for {symbol}: {str(e)}")
            return mt5.ORDER_FILLING_FOK

    def close_position(self, position, volume=None):
        """Close position fully or partially"""
        try:
            symbol_info = mt5.symbol_info(position.symbol)
            if symbol_info is None:
                logging.error(f"Failed to get symbol info for {position.symbol}")
                return False

            # If no volume specified, close entire position
            if volume is None:
                volume = position.volume
            
            # Normalize the volume
            volume = self.normalize_volume(position.symbol, volume)
            if volume is None:
                logging.error(f"Failed to normalize volume for {position.symbol}")
                return False
            
            # Validate volume
            if volume < symbol_info.volume_min or volume > position.volume:
                logging.error(f"Invalid volume {volume} for {position.symbol} (min: {symbol_info.volume_min}, current: {position.volume})")
                return False

            # Get current market price
            tick = mt5.symbol_info_tick(position.symbol)
            if tick is None:
                logging.error(f"Failed to get tick data for {position.symbol}")
                return False

            # Determine price based on position type
            if position.type == mt5.ORDER_TYPE_BUY:
                price = tick.bid  # Sell at bid price
            else:
                price = tick.ask  # Buy at ask price

            # Get supported filling mode
            filling_mode = self.get_supported_filling_mode(position.symbol)

            request = {
                "action": mt5.TRADE_ACTION_DEAL,
                "position": position.ticket,
                "symbol": position.symbol,
                "volume": volume,
                "type": mt5.ORDER_TYPE_SELL if position.type == mt5.ORDER_TYPE_BUY else mt5.ORDER_TYPE_BUY,
                "price": price,
                "deviation": 20,
                "magic": position.magic,
                "comment": "profit_monitor_close",
                "type_time": mt5.ORDER_TIME_GTC,
                "type_filling": filling_mode,
            }
            
            # Log the order details before sending
            logging.info(f"Attempting to close position {position.ticket} for {position.symbol} with volume {volume} at price {price}")
            
            result = mt5.order_send(request)
            if result.retcode != mt5.TRADE_RETCODE_DONE:
                logging.error(f"Order failed: {result.comment} (Code: {result.retcode})")
                
                # If filling mode failed, try with a different approach
                if result.retcode == 10030:  # Unsupported filling mode
                    logging.info(f"Retrying with different filling mode for {position.symbol}")
                    return self.retry_close_position(position, volume, price)
                
                return False
            
            logging.info(f"Successfully closed position {position.ticket} for {position.symbol} with profit {position.profit}")
            return True
            
        except Exception as e:
            logging.error(f"Error closing position: {str(e)}")
            return False

    def retry_close_position(self, position, volume, price):
        """Retry closing position with different filling modes"""
        try:
            # Try different filling modes
            filling_modes = [
                mt5.ORDER_FILLING_FOK,
                mt5.ORDER_FILLING_IOC,
                mt5.ORDER_FILLING_RETURN
            ]
            
            for filling_mode in filling_modes:
                try:
                    request = {
                        "action": mt5.TRADE_ACTION_DEAL,
                        "position": position.ticket,
                        "symbol": position.symbol,
                        "volume": volume,
                        "type": mt5.ORDER_TYPE_SELL if position.type == mt5.ORDER_TYPE_BUY else mt5.ORDER_TYPE_BUY,
                        "price": price,
                        "deviation": 20,
                        "magic": position.magic,
                        "comment": "profit_monitor_close_retry",
                        "type_time": mt5.ORDER_TIME_GTC,
                        "type_filling": filling_mode,
                    }
                    
                    logging.info(f"Retrying with filling mode {filling_mode}")
                    result = mt5.order_send(request)
                    
                    if result.retcode == mt5.TRADE_RETCODE_DONE:
                        logging.info(f"Successfully closed position {position.ticket} with filling mode {filling_mode}")
                        return True
                    else:
                        logging.warning(f"Filling mode {filling_mode} failed: {result.comment} (Code: {result.retcode})")
                        
                except Exception as e:
                    logging.warning(f"Error with filling mode {filling_mode}: {str(e)}")
                    continue
            
            logging.error(f"All filling modes failed for position {position.ticket}")
            return False
            
        except Exception as e:
            logging.error(f"Error in retry_close_position: {str(e)}")
            return False

    def manage_profitable_positions(self):
        """Check and manage profitable positions"""
        if not self.initialized:
            if not self.initialize_mt5():
                return

        positions = self.get_open_positions()
        
        # Update database with current positions and account info
        self.update_positions_in_database(positions)
        
        for position in positions:
            try:
                # Check if market is open for this symbol (if enabled)
                if self.config.get("enable_market_check", True):
                    if not self.is_market_open(position.symbol):
                        logging.info(f"Market closed for {position.symbol}, skipping position {position.ticket}")
                        continue
                
                profit_percent = self.calculate_profit_percent(position)
                
                # Log position status
                logging.info(f"Position {position.ticket}: {position.symbol} - Profit: {profit_percent:.2f}%")
                
                # Handle partial closing
                if (self.config["partial_close_enabled"] and 
                    profit_percent >= self.config["partial_close_threshold"]):
                    
                    symbol_info = mt5.symbol_info(position.symbol)
                    if symbol_info:
                        # Calculate partial volume
                        partial_volume = position.volume * (self.config["partial_close_percent"] / 100)
                        partial_volume = self.normalize_volume(position.symbol, partial_volume)
                        
                        if partial_volume and partial_volume >= symbol_info.volume_min:
                            if self.close_position_with_retry(position, partial_volume):
                                logging.info(f"Partially closed position {position.ticket} ({self.config['partial_close_percent']}%)")
                            else:
                                logging.warning(f"Failed to partially close position {position.ticket}")
                        else:
                            logging.warning(f"Skipping partial close for {position.ticket}: volume {partial_volume} too small")
                
                # Handle full position closing
                elif profit_percent >= self.config["min_profit_percent"]:
                    if self.close_position_with_retry(position):
                        logging.info(f"Fully closed profitable position {position.ticket}")
                    else:
                        logging.warning(f"Failed to close profitable position {position.ticket}")
                    
            except Exception as e:
                logging.error(f"Error managing position {position.ticket}: {str(e)}")
                continue

    def close_position_with_retry(self, position, volume=None):
        """Close position with retry logic"""
        max_retries = self.config.get("max_retries", 3)
        retry_delay = self.config.get("retry_delay", 1)
        
        for attempt in range(max_retries):
            try:
                if self.close_position(position, volume):
                    return True
                else:
                    if attempt < max_retries - 1:
                        logging.warning(f"Close attempt {attempt + 1} failed for position {position.ticket}, retrying in {retry_delay}s...")
                        time.sleep(retry_delay)
                    else:
                        logging.error(f"All {max_retries} close attempts failed for position {position.ticket}")
                        return False
            except Exception as e:
                if attempt < max_retries - 1:
                    logging.warning(f"Close attempt {attempt + 1} failed with error: {str(e)}, retrying in {retry_delay}s...")
                    time.sleep(retry_delay)
                else:
                    logging.error(f"All {max_retries} close attempts failed for position {position.ticket} with error: {str(e)}")
                    return False
        
        return False

    def update_positions_in_database(self, positions):
        """Update database with current positions and account info"""
        try:
            # Get account info
            account_info = mt5.account_info()
            if not account_info:
                logging.error("Failed to get account info")
                return
            
            # Calculate position data
            positions_data = []
            total_profit = 0
            total_loss = 0
            profitable_count = 0
            losing_count = 0
            
            for position in positions:
                profit_percent = self.calculate_profit_percent(position)
                
                position_data = {
                    'ticket': position.ticket,
                    'symbol': position.symbol,
                    'type': 'buy' if position.type == mt5.ORDER_TYPE_BUY else 'sell',
                    'volume': position.volume,
                    'open_price': position.price_open,
                    'current_price': position.price_current,
                    'profit': position.profit,
                    'profit_percent': profit_percent,
                    'time': datetime.fromtimestamp(position.time).isoformat(),
                    'magic': position.magic,
                    'comment': position.comment
                }
                positions_data.append(position_data)
                
                if position.profit > 0:
                    total_profit += position.profit
                    profitable_count += 1
                else:
                    total_loss += abs(position.profit)
                    losing_count += 1
            
            # Update position tracking table
            self.update_position_tracking(positions_data)
            
            # Update profit monitoring table
            summary_data = {
                'total_positions': len(positions),
                'total_profit': total_profit,
                'total_loss': total_loss,
                'net_profit': total_profit - total_loss,
                'balance': account_info.balance,
                'equity': account_info.equity,
                'margin': account_info.margin,
                'free_margin': account_info.margin_free,
                'profitable_count': profitable_count,
                'losing_count': losing_count,
                'positions_count': len(positions)
            }
            
            self.update_profit_monitoring(summary_data)
            
        except Exception as e:
            logging.error(f"Error updating positions in database: {str(e)}")

    def process_command_files(self):
        """Process command files from web interface"""
        try:
            # Get project root directory (3 levels up from profit_monitor.py)
            project_root = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
            commands_dir = os.path.join(project_root, 'commands')
            if not os.path.exists(commands_dir):
                return
                
            command_files = [f for f in os.listdir(commands_dir) if f.startswith('cmd_') and f.endswith('.json')]
            
            for command_file in command_files:
                try:
                    file_path = os.path.join(commands_dir, command_file)
                    
                    with open(file_path, 'r') as f:
                        command = json.load(f)
                    
                    # Process the command
                    result = self.execute_command(command)
                    
                    # Update database with result
                    self.update_command_result(command['id'], result)
                    
                    # Remove processed command file
                    os.remove(file_path)
                    logging.info(f"Processed and removed command file: {command_file}")
                    
                except Exception as e:
                    logging.error(f"Error processing command file {command_file}: {str(e)}")
                    # Move failed command to error directory
                    self.move_to_error_dir(file_path)
                    
        except Exception as e:
            logging.error(f"Error in process_command_files: {str(e)}")
    
    def execute_command(self, command):
        """Execute a command from the web interface"""
        try:
            command_type = command.get('type')
            ticket = command.get('ticket')
            
            logging.info(f"Executing command: {command_type} (ID: {command['id']})")
            
            if command_type in ['all', 'profit', 'loss']:
                return self.close_positions_by_type(command_type)
            elif command_type == 'single' and ticket:
                return self.close_single_position(ticket)
            else:
                return {'error': f'Unknown command type: {command_type}'}
                
        except Exception as e:
            logging.error(f"Error executing command: {str(e)}")
            return {'error': str(e)}
    
    def update_command_result(self, command_id, result):
        """Update command result in database"""
        try:
            conn = self.get_db_connection()
            try:
                if 'error' in result:
                    conn.execute('''
                        UPDATE position_close_operations
                        SET status = 'failed',
                            error_message = ?
                        WHERE id = ?
                    ''', (result['error'], command_id))
                else:
                    conn.execute('''
                        UPDATE position_close_operations
                        SET status = 'completed',
                            positions_closed = ?,
                            positions_failed = ?,
                            total_profit_closed = ?,
                            total_loss_closed = ?
                        WHERE id = ?
                    ''', (
                        result.get('closed', 0),
                        result.get('failed', 0),
                        result.get('total_profit_closed', 0),
                        result.get('total_loss_closed', 0),
                        command_id
                    ))
                conn.commit()
            finally:
                conn.close()
        except Exception as e:
            logging.error(f"Error updating command result: {str(e)}")
    
    def move_to_error_dir(self, file_path):
        """Move failed command to error directory"""
        try:
            # Get project root directory (3 levels up from profit_monitor.py)
            project_root = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
            error_dir = os.path.join(project_root, 'commands', 'errors')
            os.makedirs(error_dir, exist_ok=True)
            
            filename = os.path.basename(file_path)
            error_path = os.path.join(error_dir, filename)
            
            os.rename(file_path, error_path)
            logging.info(f"Moved failed command to: {error_path}")
        except Exception as e:
            logging.error(f"Error moving file to error directory: {str(e)}")

    def run(self):
        """Main monitoring loop"""
        logging.info("Starting autonomous profit monitor...")
        
        while True:
            try:
                # Check for configuration changes
                if self.reload_config_if_changed():
                    logging.info("Configuration updated, applying new settings")
                
                # Process any pending commands from web interface
                self.process_command_files()
                
                # Regular profit monitoring
                self.manage_profitable_positions()
                
                # Sleep for the configured interval
                time.sleep(self.config["check_interval"])
                
            except KeyboardInterrupt:
                logging.info("Profit monitor stopped by user")
                break
            except Exception as e:
                logging.error(f"Error in monitoring loop: {str(e)}")
                time.sleep(60)  # Wait a minute before retrying on error

    def is_market_open(self, symbol: str):
        """Check if market is open for the symbol"""
        try:
            symbol_info = mt5.symbol_info(symbol)
            if symbol_info is None:
                return False
            
            # Check if trading is allowed
            if not symbol_info.trade_mode == mt5.SYMBOL_TRADE_MODE_FULL:
                return False
            
            # Get current tick to see if market is active
            tick = mt5.symbol_info_tick(symbol)
            if tick is None:
                return False
            
            return True
            
        except Exception as e:
            logging.error(f"Error checking market status for {symbol}: {str(e)}")
            return False

    def get_account_status(self):
        """Get current account status including balance, equity, and positions"""
        try:
            if not self.initialized and not self.initialize_mt5():
                return {
                    'balance': 0,
                    'equity': 0,
                    'margin': 0,
                    'free_margin': 0,
                    'positions_count': 0,
                    'total_profit': 0,
                    'total_loss': 0,
                    'net_profit': 0,
                    'error': 'MT5 not initialized'
                }

            account_info = mt5.account_info()
            if not account_info:
                return {
                    'balance': 0,
                    'equity': 0,
                    'margin': 0,
                    'free_margin': 0,
                    'positions_count': 0,
                    'total_profit': 0,
                    'total_loss': 0,
                    'net_profit': 0,
                    'error': 'Failed to get account info'
                }

            positions = self.get_open_positions()
            total_profit = sum(pos.profit for pos in positions if pos.profit > 0)
            total_loss = abs(sum(pos.profit for pos in positions if pos.profit < 0))
            profitable_count = len([pos for pos in positions if pos.profit > 0])
            losing_count = len([pos for pos in positions if pos.profit < 0])

            return {
                'balance': account_info.balance,
                'equity': account_info.equity,
                'margin': account_info.margin,
                'free_margin': account_info.margin_free,
                'positions_count': len(positions),
                'profitable_count': profitable_count,
                'losing_count': losing_count,
                'total_profit': total_profit,
                'total_loss': total_loss,
                'net_profit': total_profit - total_loss,
                'timestamp': datetime.now().isoformat()
            }
        except Exception as e:
            logging.error(f"Error getting account status: {str(e)}")
            return {
                'balance': 0,
                'equity': 0,
                'margin': 0,
                'free_margin': 0,
                'positions_count': 0,
                'profitable_count': 0,
                'losing_count': 0,
                'total_profit': 0,
                'total_loss': 0,
                'net_profit': 0,
                'error': str(e),
                'timestamp': datetime.now().isoformat()
            }

    def get_db_connection(self):
        """Get database connection"""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn

    def update_position_tracking(self, positions_data):
        """Update position tracking in database"""
        conn = self.get_db_connection()
        try:
            conn.execute('BEGIN')
            
            # Mark all positions as closed first
            conn.execute('UPDATE position_tracking SET status = "closed" WHERE status = "open"')
            
            # Update or insert each position
            for pos in positions_data:
                conn.execute('''
                    INSERT INTO position_tracking (
                        ticket, symbol, type, volume, open_price, current_price,
                        profit, profit_percent, open_time, status
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, "open")
                    ON CONFLICT(ticket) DO UPDATE SET
                        current_price = excluded.current_price,
                        profit = excluded.profit,
                        profit_percent = excluded.profit_percent,
                        last_update = CURRENT_TIMESTAMP,
                        status = "open"
                ''', (
                    pos['ticket'], pos['symbol'], pos['type'], pos['volume'],
                    pos['open_price'], pos['current_price'], pos['profit'],
                    pos['profit_percent'], pos['time']
                ))
            
            conn.commit()
        except Exception as e:
            conn.rollback()
            logging.error(f"Error updating position tracking: {str(e)}")
        finally:
            conn.close()

    def update_profit_monitoring(self, summary_data):
        """Update profit monitoring in database"""
        conn = self.get_db_connection()
        try:
            conn.execute('''
                INSERT INTO profit_monitoring (
                    total_positions, total_profit, total_loss, net_profit,
                    balance, equity, margin, free_margin
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                summary_data['total_positions'],
                summary_data['total_profit'],
                summary_data['total_loss'],
                summary_data['net_profit'],
                summary_data['balance'],
                summary_data['equity'],
                summary_data['margin'],
                summary_data['free_margin']
            ))
            conn.commit()
        except Exception as e:
            logging.error(f"Error updating profit monitoring: {str(e)}")
        finally:
            conn.close()

    def record_close_operation(self, operation_type, result):
        """Record position close operation in database"""
        conn = self.get_db_connection()
        try:
            conn.execute('''
                INSERT INTO position_close_operations (
                    operation_type, positions_closed, positions_failed,
                    total_profit_closed, total_loss_closed, status,
                    error_message
                ) VALUES (?, ?, ?, ?, ?, ?, ?)
            ''', (
                operation_type,
                result.get('closed', 0),
                result.get('failed', 0),
                result.get('total_profit_closed', 0),
                result.get('total_loss_closed', 0),
                'completed' if 'error' not in result else 'failed',
                result.get('error', None)
            ))
            conn.commit()
        except Exception as e:
            logging.error(f"Error recording close operation: {str(e)}")
        finally:
            conn.close()

    def close_positions_by_type(self, position_type='all'):
        """Close positions based on type (all, profit, loss)"""
        try:
            if not self.initialized and not self.initialize_mt5():
                return {'error': 'MT5 not initialized'}

            positions = self.get_open_positions()
            if not positions:
                return {'message': 'No positions to close', 'closed': 0, 'failed': 0}

            closed_count = 0
            failed_count = 0
            total_profit_closed = 0
            total_loss_closed = 0

            for pos in positions:
                should_close = False
                if position_type == 'all':
                    should_close = True
                elif position_type == 'profit' and pos.profit > 0:
                    should_close = True
                elif position_type == 'loss' and pos.profit < 0:
                    should_close = True

                if should_close:
                    if self.close_position(pos):
                        closed_count += 1
                        if pos.profit >= 0:
                            total_profit_closed += pos.profit
                        else:
                            total_loss_closed += abs(pos.profit)
                    else:
                        failed_count += 1

            result = {
                'message': f'Closed {closed_count} positions, {failed_count} failed',
                'closed': closed_count,
                'failed': failed_count,
                'total_profit_closed': total_profit_closed,
                'total_loss_closed': total_loss_closed
            }

            # Record operation in database
            self.record_close_operation(position_type, result)

            return result

        except Exception as e:
            error_result = {'error': str(e)}
            self.record_close_operation(position_type, error_result)
            return error_result

    def get_positions_data(self):
        """Get formatted positions data for API response"""
        try:
            if not self.initialized and not self.initialize_mt5():
                return {
                    'error': 'MT5 not initialized',
                    'positions': [],
                    'summary': self.get_account_status() or {
                        'total_positions': 0,
                        'total_profit': 0,
                        'total_loss': 0,
                        'net_profit': 0
                    }
                }

            positions = self.get_open_positions()
            formatted_positions = []
            total_profit = 0
            total_loss = 0

            for pos in positions:
                profit_percent = self.calculate_profit_percent(pos)
                current_price = mt5.symbol_info_tick(pos.symbol).bid if pos.type == mt5.ORDER_TYPE_BUY else mt5.symbol_info_tick(pos.symbol).ask

                position_data = {
                    'ticket': pos.ticket,
                    'symbol': pos.symbol,
                    'type': 'buy' if pos.type == mt5.ORDER_TYPE_BUY else 'sell',
                    'volume': pos.volume,
                    'open_price': pos.price_open,
                    'current_price': current_price,
                    'profit': pos.profit,
                    'profit_percent': profit_percent,
                    'time': datetime.fromtimestamp(pos.time).strftime('%Y-%m-%d %H:%M:%S')
                }

                formatted_positions.append(position_data)
                if pos.profit >= 0:
                    total_profit += pos.profit
                else:
                    total_loss += abs(pos.profit)

            account_status = self.get_account_status()
            if not account_status:
                account_status = {
                    'total_positions': len(formatted_positions),
                    'total_profit': total_profit,
                    'total_loss': total_loss,
                    'net_profit': total_profit - total_loss,
                    'balance': 0,
                    'equity': 0,
                    'margin': 0,
                    'free_margin': 0
                }

            # Update database
            self.update_position_tracking(formatted_positions)
            self.update_profit_monitoring(account_status)

            return {
                'positions': formatted_positions,
                'summary': account_status
            }

        except Exception as e:
            logging.error(f"Error getting positions data: {str(e)}")
            return {
                'error': str(e),
                'positions': [],
                'summary': {
                    'total_positions': 0,
                    'total_profit': 0,
                    'total_loss': 0,
                    'net_profit': 0,
                    'balance': 0,
                    'equity': 0,
                    'margin': 0,
                    'free_margin': 0
                }
            }

    def close_positions_by_condition(self, condition='all'):
        """Close positions based on condition (all, profit, loss)"""
        try:
            if not self.initialized:
                if not self.initialize_mt5():
                    return {"error": "MT5 not initialized"}
            
            positions = self.get_open_positions()
            closed_count = 0
            failed_count = 0
            
            for pos in positions:
                should_close = False
                
                if condition == 'all':
                    should_close = True
                elif condition == 'profit' and pos.profit > 0:
                    should_close = True
                elif condition == 'loss' and pos.profit < 0:
                    should_close = True
                
                if should_close:
                    if self.close_position_with_retry(pos):
                        closed_count += 1
                    else:
                        failed_count += 1
            
            return {
                "status": "success",
                "message": f"Closed {closed_count} positions, {failed_count} failed",
                "closed_count": closed_count,
                "failed_count": failed_count
            }
            
        except Exception as e:
            logging.error(f"Error in close_positions_by_condition: {str(e)}")
            return {"error": str(e)}

    def close_single_position(self, ticket):
        """Close a single position by ticket number"""
        try:
            if not self.initialized:
                if not self.initialize_mt5():
                    return {"error": "MT5 not initialized"}
            
            positions = self.get_open_positions()
            target_position = None
            
            for pos in positions:
                if pos.ticket == ticket:
                    target_position = pos
                    break
            
            if target_position is None:
                return {"error": f"Position {ticket} not found"}
            
            if self.close_position_with_retry(target_position):
                return {
                    "status": "success",
                    "message": f"Position {ticket} closed successfully"
                }
            else:
                return {"error": f"Failed to close position {ticket}"}
            
        except Exception as e:
            logging.error(f"Error in close_single_position: {str(e)}")
            return {"error": str(e)}

    def get_profit_history(self, hours=24):
        """Get profit monitoring history"""
        conn = self.get_db_connection()
        try:
            cursor = conn.execute('''
                SELECT * FROM profit_monitoring
                WHERE timestamp >= datetime('now', '-' || ? || ' hours')
                ORDER BY timestamp DESC
            ''', (hours,))
            return [dict(row) for row in cursor.fetchall()]
        finally:
            conn.close()

    def get_close_operations_history(self, limit=50):
        """Get position close operations history"""
        conn = self.get_db_connection()
        try:
            cursor = conn.execute('''
                SELECT * FROM position_close_operations
                ORDER BY timestamp DESC
                LIMIT ?
            ''', (limit,))
            return [dict(row) for row in cursor.fetchall()]
        finally:
            conn.close()

if __name__ == "__main__":
    try:
        monitor = ProfitMonitor()
        monitor.run()
    except KeyboardInterrupt:
        logging.info("Program terminated by user")
    except Exception as e:
        logging.error(f"Fatal error: {str(e)}") 