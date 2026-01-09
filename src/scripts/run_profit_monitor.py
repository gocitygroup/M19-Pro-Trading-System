#!/usr/bin/env python3
"""
Standalone Profit Monitor Runner
Runs the profit monitor independently from the web interface
"""

import sys
import os
import logging
import signal
import time
from datetime import datetime

# Add project root to path for imports
project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, project_root)

from src.core.profit_monitor import ProfitMonitor
from src.config.config import load_config, LOGGING_CONFIG

# Configure logging
def setup_logging():
    """Setup logging configuration"""
    logging.basicConfig(
        level=logging.INFO,
        format=LOGGING_CONFIG['format'],
        handlers=[
            logging.StreamHandler(),
            logging.FileHandler(LOGGING_CONFIG['profit_monitor_log'])
        ]
    )

class ProfitMonitorService:
    """Service wrapper for the profit monitor"""
    
    def __init__(self):
        self.monitor = None
        self.running = False
        
    def start(self):
        """Start the profit monitor service"""
        try:
            setup_logging()
            logger = logging.getLogger(__name__)
            
            logger.info("="*60)
            logger.info("STARTING AUTONOMOUS PROFIT MONITOR SERVICE")
            logger.info("="*60)
            logger.info(f"Start time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
            
            # Load configuration
            config = load_config()
            logger.info(f"Configuration loaded from: {config.get('config_file', 'default')}")
            
            # Initialize profit monitor
            self.monitor = ProfitMonitor()
            logger.info("Profit monitor initialized")
            
            # Setup signal handlers for graceful shutdown
            signal.signal(signal.SIGINT, self._signal_handler)
            signal.signal(signal.SIGTERM, self._signal_handler)
            
            self.running = True
            logger.info("Signal handlers registered")
            
            # Print configuration summary
            self._print_config_summary(config)
            
            # Start monitoring
            logger.info("Starting monitoring loop...")
            self.monitor.run()
            
        except KeyboardInterrupt:
            logger.info("Received keyboard interrupt")
            self._shutdown()
        except Exception as e:
            logger.error(f"Fatal error in profit monitor service: {str(e)}")
            self._shutdown()
    
    def _signal_handler(self, signum, frame):
        """Handle shutdown signals"""
        logger = logging.getLogger(__name__)
        logger.info(f"Received signal {signum}, initiating shutdown...")
        self._shutdown()
    
    def _shutdown(self):
        """Graceful shutdown"""
        logger = logging.getLogger(__name__)
        
        if self.running:
            logger.info("Shutting down profit monitor service...")
            self.running = False
            
            if self.monitor:
                # Any cleanup needed for the monitor
                logger.info("Profit monitor cleanup completed")
            
            logger.info("="*60)
            logger.info("PROFIT MONITOR SERVICE STOPPED")
            logger.info("="*60)
            logger.info(f"Stop time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        
        sys.exit(0)
    
    def _print_config_summary(self, config):
        """Print configuration summary"""
        logger = logging.getLogger(__name__)
        
        logger.info("-" * 40)
        logger.info("CONFIGURATION SUMMARY")
        logger.info("-" * 40)
        
        # MT5 Configuration
        mt5_config = config.get('mt5', {})
        logger.info(f"MT5 Server: {mt5_config.get('server', 'Not configured')}")
        logger.info(f"MT5 Login: {mt5_config.get('login', 'Not configured')}")
        logger.info(f"MT5 Password: {'***' if mt5_config.get('password') else 'Not configured'}")
        
        # Profit Monitor Configuration
        pm_config = config.get('profit_monitor', {})
        logger.info(f"Check Interval: {pm_config.get('check_interval', 'Not configured')} seconds")
        logger.info(f"Min Profit %: {pm_config.get('min_profit_percent', 'Not configured')}%")
        logger.info(f"Partial Close Enabled: {pm_config.get('partial_close_enabled', 'Not configured')}")
        
        if pm_config.get('partial_close_enabled'):
            logger.info(f"Partial Close Threshold: {pm_config.get('partial_close_threshold', 'Not configured')}%")
            logger.info(f"Partial Close Percent: {pm_config.get('partial_close_percent', 'Not configured')}%")
        
        # Database Configuration
        db_config = config.get('db', {})
        logger.info(f"Database Path: {db_config.get('path', 'Not configured')}")
        
        logger.info("-" * 40)

def main():
    """Main entry point"""
    print("Forex Profit Monitor - Autonomous Service")
    print("Press Ctrl+C to stop")
    print()
    
    service = ProfitMonitorService()
    service.start()

if __name__ == "__main__":
    main() 