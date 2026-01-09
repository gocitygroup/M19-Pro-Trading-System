#!/usr/bin/env python3
"""
Enhanced API Service for Real-time Profit Monitoring
Optimized for fast profit/loss calculations and responsive UI operations
"""

import sys
import sqlite3
import json
import os
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
import threading
from concurrent.futures import ThreadPoolExecutor
import time

# Add project root to Python path
project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, project_root)

from src.config.config import load_config

logger = logging.getLogger(__name__)

class EnhancedTradingAPIService:
    """Enhanced API service with real-time profit monitoring and fast operations"""
    
    def __init__(self):
        self.config = load_config()
        project_root = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
        self.db_path = os.path.join(project_root, self.config['db']['path'])
        
        # Real-time cache for faster responses
        self.positions_cache = {}
        self.profit_cache = {}
        self.cache_lock = threading.Lock()
        self.cache_expiry = 2.0  # Cache valid for 2 seconds
        self.last_cache_update = 0
        
        # Thread pool for async operations
        self.executor = ThreadPoolExecutor(max_workers=3)
        
    def get_db_connection(self):
        """Get database connection with optimized settings"""
        conn = sqlite3.connect(self.db_path, timeout=5.0)
        conn.row_factory = sqlite3.Row
        # Optimize for read performance
        conn.execute('PRAGMA synchronous = NORMAL')
        conn.execute('PRAGMA cache_size = 10000')
        conn.execute('PRAGMA temp_store = MEMORY')
        return conn

    def get_positions_summary_fast(self) -> Dict[str, Any]:
        """Get positions summary with smart caching for real-time performance"""
        current_time = time.time()
        
        # Check if cache is still valid
        with self.cache_lock:
            if (current_time - self.last_cache_update < self.cache_expiry and 
                self.positions_cache and self.profit_cache):
                return {
                    'positions': self.positions_cache.get('positions', []),
                    'summary': self.profit_cache.get('summary', {}),
                    'account': self.profit_cache.get('account', {}),
                    'cached': True,
                    'cache_age': round(current_time - self.last_cache_update, 2)
                }
        
        # Cache expired or empty, refresh data
        return self._refresh_positions_cache()

    def _refresh_positions_cache(self) -> Dict[str, Any]:
        """Refresh positions cache with optimized database queries"""
        try:
            conn = self.get_db_connection()
            
            try:
                # Get positions with optimized query
                cursor = conn.execute('''
                    SELECT ticket, symbol, type, volume, open_price, current_price, 
                           profit, profit_percent, open_time, last_update
                    FROM position_tracking 
                    WHERE status = 'open' 
                    ORDER BY profit DESC
                ''')
                positions = [dict(row) for row in cursor.fetchall()]
                
                # Get latest profit monitoring data with single query
                cursor = conn.execute('''
                    SELECT total_positions, total_profit, total_loss, net_profit,
                           balance, equity, margin, free_margin, timestamp
                    FROM profit_monitoring 
                    ORDER BY timestamp DESC 
                    LIMIT 1
                ''')
                summary_row = cursor.fetchone()
                
                # Calculate real-time summary if no monitoring data
                if summary_row:
                    summary = dict(summary_row)
                else:
                    summary = self._calculate_summary_from_positions(positions)
                
                # Calculate position counts efficiently
                profitable_positions = [p for p in positions if p['profit'] > 0]
                losing_positions = [p for p in positions if p['profit'] < 0]
                
                profitable_count = len(profitable_positions)
                losing_count = len(losing_positions)
                
                # Calculate totals from actual positions for accuracy
                actual_total_profit = sum(p['profit'] for p in profitable_positions)
                actual_total_loss = sum(abs(p['profit']) for p in losing_positions)
                actual_net_profit = actual_total_profit - actual_total_loss
                
                # Create account summary with real-time data
                account_summary = {
                    'balance': summary.get('balance', 0),
                    'equity': summary.get('equity', 0),
                    'margin': summary.get('margin', 0),
                    'free_margin': summary.get('free_margin', 0),
                    'profitable_count': profitable_count,
                    'losing_count': losing_count,
                    'positions_count': len(positions),
                    'total_profit': round(actual_total_profit, 2),
                    'total_loss': round(actual_total_loss, 2),
                    'net_profit': round(actual_net_profit, 2),
                    'timestamp': datetime.now().isoformat(),
                    'margin_level': 0 if summary.get('margin', 0) == 0 else round(summary.get('equity', 0) / summary.get('margin', 1) * 100, 2)
                }
                
                # Update summary with real-time calculations
                summary.update({
                    'total_profit': actual_total_profit,
                    'total_loss': actual_total_loss,
                    'net_profit': actual_net_profit,
                    'total_positions': len(positions)
                })
                
                result = {
                    'positions': positions,
                    'summary': summary,
                    'account': account_summary,
                    'cached': False,
                    'update_time': datetime.now().isoformat()
                }
                
                # Update cache
                with self.cache_lock:
                    self.positions_cache = {'positions': positions}
                    self.profit_cache = {
                        'summary': summary,
                        'account': account_summary
                    }
                    self.last_cache_update = time.time()
                
                return result
                
            finally:
                conn.close()
                
        except Exception as e:
            logger.error(f"Error refreshing positions cache: {str(e)}")
            return self._get_fallback_data(str(e))

    def _calculate_summary_from_positions(self, positions: List[Dict]) -> Dict[str, Any]:
        """Calculate summary directly from positions when monitoring data is unavailable"""
        total_profit = sum(p['profit'] for p in positions if p['profit'] > 0)
        total_loss = sum(abs(p['profit']) for p in positions if p['profit'] < 0)
        
        return {
            'total_positions': len(positions),
            'total_profit': round(total_profit, 2),
            'total_loss': round(total_loss, 2),
            'net_profit': round(total_profit - total_loss, 2),
            'balance': 0,
            'equity': 0,
            'margin': 0,
            'free_margin': 0,
            'timestamp': datetime.now().isoformat()
        }

    def _get_fallback_data(self, error: str) -> Dict[str, Any]:
        """Return fallback data when database operations fail"""
        return {
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
            },
            'account': {
                'balance': 0,
                'equity': 0,
                'margin': 0,
                'free_margin': 0,
                'profitable_count': 0,
                'losing_count': 0,
                'positions_count': 0,
                'error': error,
                'timestamp': datetime.now().isoformat()
            },
            'error': True
        }

    def request_position_close_fast(self, operation_type: str, ticket: Optional[int] = None) -> Dict[str, Any]:
        """Fast position close request with immediate response"""
        try:
            # Validate operation type
            valid_types = ['single', 'profit', 'loss', 'all']
            if operation_type not in valid_types:
                return {
                    'status': 'error',
                    'error': f'Invalid operation type. Must be one of: {valid_types}'
                }
            
            # Check if single position exists
            if operation_type == 'single':
                if not ticket:
                    return {
                        'status': 'error',
                        'error': 'Ticket number required for single position close'
                    }
                
                # Quick check if position exists
                positions_data = self.get_positions_summary_fast()
                position_exists = any(p['ticket'] == ticket for p in positions_data['positions'])
                
                if not position_exists:
                    return {
                        'status': 'error',
                        'error': f'Position {ticket} not found'
                    }
            
            # Create database entry
            conn = self.get_db_connection()
            try:
                cursor = conn.execute('''
                    INSERT INTO position_close_operations 
                    (operation_type, timestamp, status)
                    VALUES (?, CURRENT_TIMESTAMP, 'pending')
                ''', (operation_type,))
                
                request_id = cursor.lastrowid
                conn.commit()
                
                # Create command file immediately
                command = {
                    'id': request_id,
                    'type': operation_type,
                    'ticket': ticket,
                    'timestamp': datetime.now().isoformat(),
                    'status': 'pending',
                    'priority': 'high'  # Mark as high priority for faster processing
                }
                
                self._write_command_file_fast(command)
                
                # Invalidate cache to force refresh
                with self.cache_lock:
                    self.last_cache_update = 0
                
                return {
                    'status': 'success',
                    'message': f'Close request submitted: {operation_type}',
                    'request_id': request_id,
                    'estimated_positions': self._estimate_positions_affected(operation_type),
                    'timestamp': datetime.now().isoformat()
                }
                
            finally:
                conn.close()
                
        except Exception as e:
            logger.error(f"Error in fast position close request: {str(e)}")
            return {
                'status': 'error',
                'error': str(e)
            }

    def _estimate_positions_affected(self, operation_type: str) -> int:
        """Estimate number of positions that will be affected by operation"""
        try:
            positions_data = self.get_positions_summary_fast()
            positions = positions_data['positions']
            
            if operation_type == 'profit':
                return len([p for p in positions if p['profit'] > 0])
            elif operation_type == 'loss':
                return len([p for p in positions if p['profit'] < 0])
            elif operation_type == 'all':
                return len(positions)
            else:  # single
                return 1
                
        except Exception:
            return 0

    def _write_command_file_fast(self, command: Dict[str, Any]):
        """Write command file with optimized I/O"""
        try:
            project_root = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
            commands_dir = os.path.join(project_root, 'commands')
            os.makedirs(commands_dir, exist_ok=True)
            
            command_file = os.path.join(commands_dir, f"cmd_{command['id']}.json")
            
            # Write atomically to prevent partial reads
            temp_file = command_file + '.tmp'
            with open(temp_file, 'w') as f:
                json.dump(command, f, indent=2)
            
            os.rename(temp_file, command_file)
            logger.info(f"Fast command written: {command_file}")
            
        except Exception as e:
            logger.error(f"Error writing fast command file: {str(e)}")

    def get_close_operation_status_fast(self, request_id: int) -> Dict[str, Any]:
        """Get operation status with cached optimization"""
        try:
            conn = self.get_db_connection()
            try:
                cursor = conn.execute('''
                    SELECT id, operation_type, timestamp, positions_closed, 
                           positions_failed, total_profit_closed, total_loss_closed,
                           status, error_message
                    FROM position_close_operations 
                    WHERE id = ?
                ''', (request_id,))
                
                operation = cursor.fetchone()
                if operation:
                    result = dict(operation)
                    
                    # Add estimated completion time
                    if result['status'] == 'pending':
                        result['estimated_completion'] = (
                            datetime.now() + timedelta(seconds=30)
                        ).isoformat()
                    
                    return result
                else:
                    return {'error': 'Operation not found'}
                    
            finally:
                conn.close()
                
        except Exception as e:
            logger.error(f"Error getting operation status: {str(e)}")
            return {'error': str(e)}

    def get_profit_history_optimized(self, hours: int = 24) -> List[Dict[str, Any]]:
        """Get profit history with optimized query and data points"""
        try:
            conn = self.get_db_connection()
            try:
                # Limit data points for better performance
                max_points = 100
                interval_minutes = max(1, (hours * 60) // max_points)
                
                cursor = conn.execute('''
                    SELECT timestamp, total_profit, total_loss, net_profit, 
                           balance, equity, total_positions
                    FROM profit_monitoring
                    WHERE timestamp >= datetime('now', '-' || ? || ' hours')
                    AND (
                        strftime('%s', timestamp) % (? * 60) = 0
                        OR timestamp = (
                            SELECT MAX(timestamp) FROM profit_monitoring
                            WHERE timestamp >= datetime('now', '-' || ? || ' hours')
                        )
                    )
                    ORDER BY timestamp ASC
                ''', (hours, interval_minutes, hours))
                
                history = [dict(row) for row in cursor.fetchall()]
                
                # Add trend analysis
                if len(history) >= 2:
                    latest = history[-1]
                    previous = history[-2]
                    
                    for record in history:
                        record['profit_trend'] = 'stable'
                        record['change_percent'] = 0
                        
                    # Calculate trends
                    latest['profit_trend'] = 'up' if latest['net_profit'] > previous['net_profit'] else 'down'
                    if previous['net_profit'] != 0:
                        latest['change_percent'] = round(
                            ((latest['net_profit'] - previous['net_profit']) / abs(previous['net_profit'])) * 100, 2
                        )
                
                return history
                
            finally:
                conn.close()
                
        except Exception as e:
            logger.error(f"Error getting optimized profit history: {str(e)}")
            return []

    def get_real_time_summary(self) -> Dict[str, Any]:
        """Get real-time summary for dashboard updates"""
        try:
            positions_data = self.get_positions_summary_fast()
            
            # Add performance metrics
            summary = positions_data['summary'].copy()
            account = positions_data['account'].copy()
            
            # Calculate additional metrics
            if account['positions_count'] > 0:
                account['avg_profit_per_position'] = round(
                    account['net_profit'] / account['positions_count'], 2
                )
                
                if account['profitable_count'] > 0:
                    profitable_positions = [p for p in positions_data['positions'] if p['profit'] > 0]
                    account['avg_profitable_amount'] = round(
                        sum(p['profit'] for p in profitable_positions) / len(profitable_positions), 2
                    )
                
                if account['losing_count'] > 0:
                    losing_positions = [p for p in positions_data['positions'] if p['profit'] < 0]
                    account['avg_loss_amount'] = round(
                        sum(abs(p['profit']) for p in losing_positions) / len(losing_positions), 2
                    )
            
            # Add win rate
            total_positions = account['profitable_count'] + account['losing_count']
            if total_positions > 0:
                account['win_rate'] = round(
                    (account['profitable_count'] / total_positions) * 100, 1
                )
            else:
                account['win_rate'] = 0
            
            return {
                'summary': summary,
                'account': account,
                'positions': positions_data['positions'],
                'last_update': datetime.now().isoformat(),
                'cached': positions_data.get('cached', False)
            }
            
        except Exception as e:
            logger.error(f"Error getting real-time summary: {str(e)}")
            return self._get_fallback_data(str(e))

    def clear_cache(self):
        """Clear cache to force fresh data"""
        with self.cache_lock:
            self.positions_cache = {}
            self.profit_cache = {}
            self.last_cache_update = 0
        logger.info("API cache cleared")

# Singleton instance for web interface
enhanced_api_service = EnhancedTradingAPIService() 