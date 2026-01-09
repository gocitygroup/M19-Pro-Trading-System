"""
API Service Layer for Forex Trading System
Handles communication between web interface and profit monitor
"""

import sys
import sqlite3
import json
import os
import logging
from datetime import datetime
from typing import Dict, List, Optional, Any

# Add project root to Python path
project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, project_root)

from src.config.config import load_config

logger = logging.getLogger(__name__)

class TradingAPIService:
    """API service layer for trading operations"""
    
    def __init__(self):
        self.config = load_config()
        # Get project root directory (3 levels up from api_service.py)
        project_root = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
        self.db_path = os.path.join(project_root, self.config['db']['path'])
        
    def get_db_connection(self):
        """Get database connection"""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn
    
    def get_positions_summary(self) -> Dict[str, Any]:
        """Get positions summary from database"""
        try:
            conn = self.get_db_connection()
            try:
                # Get latest position data
                cursor = conn.execute('''
                    SELECT * FROM position_tracking 
                    WHERE status = 'open' 
                    ORDER BY last_update DESC
                ''')
                positions = [dict(row) for row in cursor.fetchall()]
                
                # Get latest profit monitoring data
                cursor = conn.execute('''
                    SELECT * FROM profit_monitoring 
                    ORDER BY timestamp DESC 
                    LIMIT 1
                ''')
                summary_row = cursor.fetchone()
                
                if summary_row:
                    summary = dict(summary_row)
                else:
                    # Calculate summary from positions if no monitoring data
                    total_profit = sum(p['profit'] for p in positions if p['profit'] > 0)
                    total_loss = abs(sum(p['profit'] for p in positions if p['profit'] < 0))
                    
                    summary = {
                        'total_positions': len(positions),
                        'total_profit': total_profit,
                        'total_loss': total_loss,
                        'net_profit': total_profit - total_loss,
                        'balance': 0,
                        'equity': 0,
                        'margin': 0,
                        'free_margin': 0
                    }
                
                # Add position counts
                profitable_count = len([p for p in positions if p['profit'] > 0])
                losing_count = len([p for p in positions if p['profit'] < 0])
                
                return {
                    'positions': positions,
                    'summary': summary,
                    'account': {
                        'balance': summary.get('balance', 0),
                        'equity': summary.get('equity', 0),
                        'margin': summary.get('margin', 0),
                        'free_margin': summary.get('free_margin', 0),
                        'profitable_count': profitable_count,
                        'losing_count': losing_count,
                        'positions_count': len(positions),
                        'timestamp': datetime.now().isoformat()
                    }
                }
                
            finally:
                conn.close()
                
        except Exception as e:
            logger.error(f"Error getting positions summary: {str(e)}")
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
                    'error': str(e),
                    'timestamp': datetime.now().isoformat()
                }
            }
    
    def request_position_close(self, operation_type: str, ticket: Optional[int] = None) -> Dict[str, Any]:
        """Request position closing operation"""
        try:
            conn = self.get_db_connection()
            try:
                # Insert close request
                cursor = conn.execute('''
                    INSERT INTO position_close_operations (
                        operation_type, status, timestamp
                    ) VALUES (?, 'pending', CURRENT_TIMESTAMP)
                ''', (operation_type,))
                
                request_id = cursor.lastrowid
                conn.commit()
                
                # Create command file for profit monitor
                command = {
                    'id': request_id,
                    'type': operation_type,
                    'ticket': ticket,
                    'timestamp': datetime.now().isoformat(),
                    'status': 'pending'
                }
                
                self._write_command_file(command)
                
                return {
                    'status': 'success',
                    'message': f'Close request submitted: {operation_type}',
                    'request_id': request_id
                }
                
            finally:
                conn.close()
                
        except Exception as e:
            logger.error(f"Error requesting position close: {str(e)}")
            return {
                'status': 'error',
                'error': str(e)
            }
    
    def get_close_operation_status(self, request_id: int) -> Dict[str, Any]:
        """Get status of close operation"""
        try:
            conn = self.get_db_connection()
            try:
                cursor = conn.execute('''
                    SELECT * FROM position_close_operations 
                    WHERE id = ?
                ''', (request_id,))
                
                operation = cursor.fetchone()
                if operation:
                    return dict(operation)
                else:
                    return {'error': 'Operation not found'}
                    
            finally:
                conn.close()
                
        except Exception as e:
            logger.error(f"Error getting operation status: {str(e)}")
            return {'error': str(e)}
    
    def get_profit_history(self, hours: int = 24) -> List[Dict[str, Any]]:
        """Get profit monitoring history"""
        try:
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
        except Exception as e:
            logger.error(f"Error getting profit history: {str(e)}")
            return []
    
    def get_operations_history(self, limit: int = 50) -> List[Dict[str, Any]]:
        """Get position close operations history"""
        try:
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
        except Exception as e:
            logger.error(f"Error getting operations history: {str(e)}")
            return []
    
    def _write_command_file(self, command: Dict[str, Any]):
        """Write command to file for profit monitor to process"""
        try:
            # Get project root directory (3 levels up from api_service.py)
            project_root = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
            commands_dir = os.path.join(project_root, 'commands')
            os.makedirs(commands_dir, exist_ok=True)
            
            command_file = os.path.join(commands_dir, f"cmd_{command['id']}.json")
            
            with open(command_file, 'w') as f:
                json.dump(command, f, indent=2)
                
            logger.info(f"Command written to {command_file}")
            
        except Exception as e:
            logger.error(f"Error writing command file: {str(e)}")
    
    def get_trading_status(self) -> Dict[str, Any]:
        """Get current trading status"""
        try:
            conn = self.get_db_connection()
            try:
                # Get suspension status
                cursor = conn.execute('''
                    SELECT is_suspended, suspended_at, suspended_by, reason, updated_at
                    FROM trading_suspension
                    ORDER BY id DESC LIMIT 1
                ''')
                suspension = cursor.fetchone()
                
                return {
                    'status': 'suspended' if suspension and suspension['is_suspended'] else 'running',
                    'suspension_info': dict(suspension) if suspension else None,
                    'timestamp': datetime.now().isoformat()
                }
                
            finally:
                conn.close()
                
        except Exception as e:
            logger.error(f"Error getting trading status: {str(e)}")
            return {
                'status': 'error',
                'error': str(e),
                'timestamp': datetime.now().isoformat()
            }
    
    def set_trading_suspension(self, suspended: bool, suspended_by: str = None, reason: str = None) -> Dict[str, Any]:
        """Set trading suspension status"""
        try:
            conn = self.get_db_connection()
            try:
                if suspended:
                    conn.execute('''
                        UPDATE trading_suspension
                        SET is_suspended = 1,
                            suspended_at = CURRENT_TIMESTAMP,
                            suspended_by = ?,
                            reason = ?
                        WHERE id = (SELECT id FROM trading_suspension ORDER BY id DESC LIMIT 1)
                    ''', (suspended_by, reason))
                else:
                    conn.execute('''
                        UPDATE trading_suspension
                        SET is_suspended = 0,
                            suspended_at = NULL,
                            suspended_by = NULL,
                            reason = NULL
                        WHERE id = (SELECT id FROM trading_suspension ORDER BY id DESC LIMIT 1)
                    ''')
                
                conn.commit()
                
                return {
                    'status': 'success',
                    'message': f'Trading {"suspended" if suspended else "resumed"}'
                }
                
            finally:
                conn.close()
                
        except Exception as e:
            logger.error(f"Error setting trading suspension: {str(e)}")
            return {
                'status': 'error',
                'error': str(e)
            } 