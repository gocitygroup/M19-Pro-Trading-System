#!/usr/bin/env python3
"""
Enhanced Profit Monitor with Real-time Updates
Optimized for fast profit/loss calculations and responsive position closing
"""

import sys
import MetaTrader5 as mt5
import time
import logging
from datetime import datetime
import json
import os
import math
import sqlite3
import threading
from concurrent.futures import ThreadPoolExecutor, as_completed
from queue import Queue, Empty
from typing import Dict, List, Optional, Tuple, Any

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

class EnhancedProfitMonitor:
    """Enhanced profit monitor with real-time updates and fast processing"""
    
    def __init__(self):
        self.initialized = False
        self.running = False
        
        # Load configuration
        config = load_config()
        self.config = config['profit_monitor']
        self.mt5_config = config['mt5']
        
        # Database path
        project_root = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
        self.db_path = os.path.join(project_root, config['db']['path'])
        
        # Configuration manager for dynamic updates
        self.config_manager = get_config_manager()
        self.config_signal_file = os.path.join(project_root, 'config', 'config_changed.signal')
        self.last_config_check = 0
        self.config_check_interval = 3  # Check for config changes every 3 seconds (faster for enhanced)
        
        # Real-time data cache
        self.positions_cache = {}
        self.profit_cache = {
            'total_profit': 0.0,
            'total_loss': 0.0,
            'net_profit': 0.0,
            'profitable_count': 0,
            'losing_count': 0,
            'last_update': datetime.now()
        }
        
        # Thread-safe queues for operations
        self.command_queue = Queue()
        self.update_queue = Queue()
        
        # Thread pool for parallel operations
        self.executor = ThreadPoolExecutor(max_workers=4)
        
        # Update frequency controls
        self.fast_update_interval = 1.0  # Fast updates every 1 second
        self.db_update_interval = 5.0    # Database updates every 5 seconds
        self.last_fast_update = 0
        self.last_db_update = 0
        
        # Initialize MT5
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
                    
                    # Update intervals if changed
                    if 'check_interval' in new_config:
                        # For enhanced monitor, use faster intervals
                        self.fast_update_interval = min(1.0, new_config['check_interval'] / 10)
                        self.db_update_interval = min(5.0, new_config['check_interval'] / 2)
                    
                    logging.info(f"Enhanced monitor configuration reloaded: {list(new_config.keys())}")
                    
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
        """Initialize MT5 connection with enhanced error handling"""
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
            
            logging.info(f"Enhanced Monitor Connected to: {account_info.server}")
            logging.info(f"Account: {account_info.login}")
            
            self.initialized = True
            return True
            
        except Exception as e:
            logging.error(f"MT5 initialization failed: {str(e)}")
            return False

    def get_real_time_positions(self) -> List[Dict[str, Any]]:
        """Get positions with optimized real-time calculations"""
        try:
            positions = mt5.positions_get()
            if positions is None:
                return []
            
            position_list = []
            total_profit = 0.0
            total_loss = 0.0
            profitable_count = 0
            losing_count = 0
            
            for pos in positions:
                # Calculate profit percentage efficiently
                position_value = pos.volume * pos.price_open
                profit_percent = (pos.profit / position_value * 100) if position_value > 0 else 0
                
                position_data = {
                    'ticket': pos.ticket,
                    'symbol': pos.symbol,
                    'type': 'BUY' if pos.type == mt5.ORDER_TYPE_BUY else 'SELL',
                    'volume': pos.volume,
                    'open_price': pos.price_open,
                    'current_price': pos.price_current,
                    'profit': pos.profit,
                    'profit_percent': round(profit_percent, 2),
                    'open_time': datetime.fromtimestamp(pos.time).isoformat(),
                    'swap': getattr(pos, 'swap', 0),
                    'commission': getattr(pos, 'commission', 0)
                }
                
                position_list.append(position_data)
                
                # Update profit/loss totals
                if pos.profit > 0:
                    total_profit += pos.profit
                    profitable_count += 1
                else:
                    total_loss += abs(pos.profit)
                    losing_count += 1
            
            # Update cache
            self.profit_cache.update({
                'total_profit': round(total_profit, 2),
                'total_loss': round(total_loss, 2),
                'net_profit': round(total_profit - total_loss, 2),
                'profitable_count': profitable_count,
                'losing_count': losing_count,
                'total_count': len(position_list),
                'last_update': datetime.now()
            })
            
            return position_list
            
        except Exception as e:
            logging.error(f"Error getting real-time positions: {str(e)}")
            return []

    def get_account_summary(self) -> Dict[str, Any]:
        """Get account summary with cached profit data"""
        try:
            account_info = mt5.account_info()
            if not account_info:
                return {}
            
            return {
                'balance': account_info.balance,
                'equity': account_info.equity,
                'margin': account_info.margin,
                'free_margin': account_info.margin_free,
                'profit': account_info.profit,
                'margin_level': account_info.margin_level if account_info.margin > 0 else 0,
                **self.profit_cache  # Include cached profit/loss data
            }
            
        except Exception as e:
            logging.error(f"Error getting account summary: {str(e)}")
            return self.profit_cache

    def close_positions_by_condition_fast(self, condition: str = 'all') -> Dict[str, Any]:
        """Fast parallel position closing with real-time updates"""
        try:
            positions = self.get_real_time_positions()
            
            if not positions:
                return {
                    'status': 'completed',
                    'message': 'No positions to close',
                    'closed': 0,
                    'failed': 0,
                    'total_profit_closed': 0,
                    'total_loss_closed': 0
                }
            
            # Filter positions based on condition
            positions_to_close = []
            if condition == 'profit':
                positions_to_close = [p for p in positions if p['profit'] > 0]
            elif condition == 'loss':
                positions_to_close = [p for p in positions if p['profit'] < 0]
            else:  # 'all'
                positions_to_close = positions
            
            if not positions_to_close:
                return {
                    'status': 'completed',
                    'message': f'No {condition} positions to close',
                    'closed': 0,
                    'failed': 0,
                    'total_profit_closed': 0,
                    'total_loss_closed': 0
                }
            
            logging.info(f"Starting parallel close of {len(positions_to_close)} {condition} positions")
            
            # Close positions in parallel
            futures = []
            for position in positions_to_close:
                future = self.executor.submit(self._close_single_position_fast, position)
                futures.append((future, position))
            
            # Collect results
            closed_count = 0
            failed_count = 0
            total_profit_closed = 0.0
            total_loss_closed = 0.0
            
            for future, position in futures:
                try:
                    result = future.result(timeout=10)  # 10 second timeout per position
                    if result['success']:
                        closed_count += 1
                        if position['profit'] > 0:
                            total_profit_closed += position['profit']
                        else:
                            total_loss_closed += abs(position['profit'])
                        logging.info(f"[OK] Closed position {position['ticket']} ({position['symbol']})")
                    else:
                        failed_count += 1
                        logging.error(f"[FAILED] Failed to close position {position['ticket']}: {result['error']}")
                except Exception as e:
                    failed_count += 1
                    logging.error(f"[ERROR] Timeout/error closing position {position['ticket']}: {str(e)}")
            
            # Update cache immediately
            self.get_real_time_positions()
            
            result = {
                'status': 'completed',
                'message': f'Closed {closed_count} of {len(positions_to_close)} positions',
                'closed': closed_count,
                'failed': failed_count,
                'total_profit_closed': round(total_profit_closed, 2),
                'total_loss_closed': round(total_loss_closed, 2)
            }
            
            logging.info(f"Position closing completed: {result}")
            return result
            
        except Exception as e:
            logging.error(f"Error in fast position closing: {str(e)}")
            return {
                'status': 'failed',
                'message': f'Failed to close positions: {str(e)}',
                'closed': 0,
                'failed': 0,
                'total_profit_closed': 0,
                'total_loss_closed': 0
            }

    def _close_single_position_fast(self, position: Dict[str, Any]) -> Dict[str, Any]:
        """Close a single position quickly with optimized parameters"""
        try:
            ticket = position['ticket']
            symbol = position['symbol']
            
            # Get MT5 position object
            mt5_positions = mt5.positions_get(ticket=ticket)
            if not mt5_positions:
                return {'success': False, 'error': 'Position not found'}
            
            mt5_position = mt5_positions[0]
            
            # Get symbol info for optimal closing
            symbol_info = mt5.symbol_info(symbol)
            if symbol_info is None:
                return {'success': False, 'error': f'Symbol {symbol} not found'}
            
            # Get current tick
            tick = mt5.symbol_info_tick(symbol)
            if tick is None:
                return {'success': False, 'error': f'No tick data for {symbol}'}
            
            # Determine close price
            if mt5_position.type == mt5.ORDER_TYPE_BUY:
                price = tick.bid
            else:
                price = tick.ask
            
            # Create close request with optimized parameters
            request = {
                "action": mt5.TRADE_ACTION_DEAL,
                "position": ticket,
                "symbol": symbol,
                "volume": mt5_position.volume,
                "type": mt5.ORDER_TYPE_SELL if mt5_position.type == mt5.ORDER_TYPE_BUY else mt5.ORDER_TYPE_BUY,
                "price": price,
                "deviation": 20,  # Increased deviation for faster execution
                "magic": mt5_position.magic,
                "comment": f"Enhanced close {ticket}",
                "type_time": mt5.ORDER_TIME_GTC,
                "type_filling": mt5.ORDER_FILLING_IOC  # Immediate or Cancel for speed
            }
            
            # Send close order
            result = mt5.order_send(request)
            
            if result is None:
                return {'success': False, 'error': 'Order send failed - no result'}
            
            if result.retcode != mt5.TRADE_RETCODE_DONE:
                # Try alternative filling mode if IOC fails
                request["type_filling"] = mt5.ORDER_FILLING_FOK
                result = mt5.order_send(request)
                
                if result is None or result.retcode != mt5.TRADE_RETCODE_DONE:
                    return {
                        'success': False, 
                        'error': f'Close failed: {result.retcode if result else "No result"}'
                    }
            
            return {
                'success': True,
                'ticket': ticket,
                'close_price': price,
                'profit': position['profit']
            }
            
        except Exception as e:
            return {'success': False, 'error': f'Exception: {str(e)}'}

    def process_commands_async(self):
        """Process command files asynchronously"""
        try:
            project_root = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
            commands_dir = os.path.join(project_root, 'commands')
            
            if not os.path.exists(commands_dir):
                return
            
            # Process command files
            for filename in os.listdir(commands_dir):
                if filename.startswith('cmd_') and filename.endswith('.json'):
                    filepath = os.path.join(commands_dir, filename)
                    
                    try:
                        with open(filepath, 'r') as f:
                            command = json.load(f)
                        
                        # Process command in background
                        self.executor.submit(self._execute_command_async, command, filepath)
                        
                    except Exception as e:
                        logging.error(f"Error processing command file {filename}: {str(e)}")
                        self._move_to_error_dir(filepath)
        
        except Exception as e:
            logging.error(f"Error in async command processing: {str(e)}")

    def _execute_command_async(self, command: Dict[str, Any], filepath: str):
        """Execute command asynchronously and update database"""
        try:
            command_id = command.get('id')
            operation_type = command.get('type', 'unknown')
            ticket = command.get('ticket')
            
            logging.info(f"Executing command {command_id}: {operation_type}")
            
            # Update command status to pending (processing)
            self._update_command_status(command_id, 'pending')
            
            # Execute based on operation type
            if operation_type == 'single' and ticket:
                result = self._close_single_position_by_ticket(ticket)
            elif operation_type in ['profit', 'loss', 'all']:
                result = self.close_positions_by_condition_fast(operation_type)
            else:
                result = {
                    'status': 'failed',
                    'message': f'Unknown operation type: {operation_type}',
                    'closed': 0,
                    'failed': 0
                }
            
            # Update database with results
            self._update_command_status(command_id, result['status'], result)
            
            # Remove command file
            if os.path.exists(filepath):
                os.remove(filepath)
                logging.info(f"Command file {filepath} processed and removed")
            
        except Exception as e:
            logging.error(f"Error executing async command: {str(e)}")
            self._update_command_status(command.get('id'), 'failed', {'error': str(e)})
            self._move_to_error_dir(filepath)

    def _close_single_position_by_ticket(self, ticket: int) -> Dict[str, Any]:
        """Close a single position by ticket number"""
        try:
            positions = self.get_real_time_positions()
            position = next((p for p in positions if p['ticket'] == ticket), None)
            
            if not position:
                return {
                    'status': 'failed',
                    'message': f'Position {ticket} not found',
                    'closed': 0,
                    'failed': 1
                }
            
            result = self._close_single_position_fast(position)
            
            if result['success']:
                return {
                    'status': 'completed',
                    'message': f'Position {ticket} closed successfully',
                    'closed': 1,
                    'failed': 0,
                    'total_profit_closed': position['profit'] if position['profit'] > 0 else 0,
                    'total_loss_closed': abs(position['profit']) if position['profit'] < 0 else 0
                }
            else:
                return {
                    'status': 'failed',
                    'message': f'Failed to close position {ticket}: {result["error"]}',
                    'closed': 0,
                    'failed': 1
                }
                
        except Exception as e:
            return {
                'status': 'failed',
                'message': f'Error closing position {ticket}: {str(e)}',
                'closed': 0,
                'failed': 1
            }

    def _update_command_status(self, command_id: int, status: str, result: Dict[str, Any] = None):
        """Update command status in database with retry logic"""
        max_retries = 3
        retry_delay = 0.1
        
        for attempt in range(max_retries):
            try:
                conn = sqlite3.connect(self.db_path, timeout=30.0)  # 30 second timeout
                conn.execute('PRAGMA journal_mode=WAL')  # Enable WAL mode for better concurrency
                
                if result:
                    conn.execute('''
                        UPDATE position_close_operations 
                        SET status = ?, 
                            positions_closed = ?, 
                            positions_failed = ?,
                            total_profit_closed = ?,
                            total_loss_closed = ?,
                            error_message = ?
                        WHERE id = ?
                    ''', (
                        status,
                        result.get('closed', 0),
                        result.get('failed', 0),
                        result.get('total_profit_closed', 0),
                        result.get('total_loss_closed', 0),
                        result.get('message', ''),
                        command_id
                    ))
                else:
                    conn.execute('''
                        UPDATE position_close_operations 
                        SET status = ? 
                        WHERE id = ?
                    ''', (status, command_id))
                
                conn.commit()
                conn.close()
                return  # Success, exit retry loop
                
            except sqlite3.OperationalError as e:
                if "database is locked" in str(e) and attempt < max_retries - 1:
                    logging.warning(f"Database locked, retrying in {retry_delay} seconds (attempt {attempt + 1}/{max_retries})")
                    time.sleep(retry_delay)
                    retry_delay *= 2  # Exponential backoff
                    continue
                else:
                    logging.error(f"Error updating command status: {str(e)}")
                    break
            except Exception as e:
                logging.error(f"Error updating command status: {str(e)}")
                break

    def _move_to_error_dir(self, filepath: str):
        """Move failed command to error directory"""
        try:
            error_dir = os.path.join(os.path.dirname(filepath), 'errors')
            os.makedirs(error_dir, exist_ok=True)
            
            filename = os.path.basename(filepath)
            error_path = os.path.join(error_dir, filename)
            
            if os.path.exists(filepath):
                os.rename(filepath, error_path)
                logging.info(f"Moved failed command to {error_path}")
                
        except Exception as e:
            logging.error(f"Error moving file to error directory: {str(e)}")

    def update_database_fast(self):
        """Fast database update with optimized queries and retry logic"""
        max_retries = 3
        retry_delay = 0.1
        
        for attempt in range(max_retries):
            try:
                positions = self.get_real_time_positions()
                account_summary = self.get_account_summary()
                
                conn = sqlite3.connect(self.db_path, timeout=30.0)  # 30 second timeout
                conn.execute('PRAGMA journal_mode=WAL')  # Enable WAL mode for better concurrency
                
                # Clear old position data
                conn.execute('DELETE FROM position_tracking WHERE status = "open"')
                
                # Batch insert new position data
                if positions:
                    position_data = [
                        (
                            p['ticket'], p['symbol'], p['type'], p['volume'],
                            p['open_price'], p['current_price'], p['profit'],
                            p['profit_percent'], p['open_time'], 'open'
                        )
                        for p in positions
                    ]
                    
                    conn.executemany('''
                        INSERT INTO position_tracking 
                        (ticket, symbol, type, volume, open_price, current_price, 
                         profit, profit_percent, open_time, status)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    ''', position_data)
                
                # Update profit monitoring
                conn.execute('''
                    INSERT INTO profit_monitoring 
                    (total_positions, total_profit, total_loss, net_profit,
                     balance, equity, margin, free_margin)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    len(positions),
                    account_summary.get('total_profit', 0),
                    account_summary.get('total_loss', 0),
                    account_summary.get('net_profit', 0),
                    account_summary.get('balance', 0),
                    account_summary.get('equity', 0),
                    account_summary.get('margin', 0),
                    account_summary.get('free_margin', 0)
                ))
                
                conn.commit()
                conn.close()
                
                logging.debug(f"Database updated with {len(positions)} positions")
                return  # Success, exit retry loop
                
            except sqlite3.OperationalError as e:
                if "database is locked" in str(e) and attempt < max_retries - 1:
                    logging.warning(f"Database locked during update, retrying in {retry_delay} seconds (attempt {attempt + 1}/{max_retries})")
                    time.sleep(retry_delay)
                    retry_delay *= 2  # Exponential backoff
                    continue
                else:
                    logging.error(f"Error in fast database update: {str(e)}")
                    break
            except Exception as e:
                logging.error(f"Error in fast database update: {str(e)}")
                break

    def run_enhanced(self):
        """Run enhanced profit monitor with real-time updates"""
        self.running = True
        logging.info("Starting Enhanced Profit Monitor with real-time updates...")
        
        try:
            while self.running:
                current_time = time.time()
                
                # Check for configuration changes
                if self.reload_config_if_changed():
                    logging.info("Enhanced monitor configuration updated, applying new settings")
                
                # Fast updates every 1 second (cache updates)
                if current_time - self.last_fast_update >= self.fast_update_interval:
                    self.get_real_time_positions()  # Updates cache
                    self.process_commands_async()
                    self.last_fast_update = current_time
                
                # Database updates every 5 seconds
                if current_time - self.last_db_update >= self.db_update_interval:
                    self.update_database_fast()
                    self.last_db_update = current_time
                
                # Short sleep to prevent excessive CPU usage
                time.sleep(0.1)
                
        except KeyboardInterrupt:
            logging.info("Enhanced Profit Monitor stopping...")
        except Exception as e:
            logging.error(f"Error in enhanced monitor: {str(e)}")
        finally:
            self.running = False
            self.executor.shutdown(wait=True)
            logging.info("Enhanced Profit Monitor stopped")

if __name__ == "__main__":
    monitor = EnhancedProfitMonitor()
    monitor.run_enhanced() 