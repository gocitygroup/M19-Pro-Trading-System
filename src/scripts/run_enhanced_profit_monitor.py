#!/usr/bin/env python3
"""
Enhanced Profit Monitor Launcher
Runs the enhanced profit monitor with better real-time capabilities
"""

import os
import sys
import logging
from datetime import datetime

# Add project root to Python path
project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, project_root)

from src.config.config import load_config, LOGGING_CONFIG
from src.core.profit_monitor_enhanced import EnhancedProfitMonitor

def main():
    """Main function to run the enhanced profit monitor"""
    
    # Configure logging
    logging.basicConfig(
        level=logging.INFO,
        format=LOGGING_CONFIG['format'],
        handlers=[
            logging.StreamHandler(),
            logging.FileHandler(LOGGING_CONFIG['profit_monitor_log'])
        ]
    )
    
    logger = logging.getLogger(__name__)
    
    logger.info("=" * 60)
    logger.info("ENHANCED PROFIT MONITOR STARTING")
    logger.info("=" * 60)
    logger.info(f"Start Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    logger.info("Enhanced Features:")
    logger.info("- Real-time profit/loss calculations")
    logger.info("- Fast parallel position closing")
    logger.info("- Optimized database operations")
    logger.info("- Smart caching for better performance")
    logger.info("- Asynchronous command processing")
    logger.info("")
    
    try:
        # Load configuration
        config = load_config()
        logger.info(f"Configuration loaded successfully")
        
        # Create enhanced monitor instance
        monitor = EnhancedProfitMonitor()
        
        if not monitor.initialized:
            logger.error("Failed to initialize enhanced profit monitor")
            return 1
        
        logger.info("Enhanced Profit Monitor initialized successfully")
        logger.info("Starting real-time monitoring...")
        logger.info("Press Ctrl+C to stop")
        logger.info("")
        
        # Start enhanced monitoring
        monitor.run_enhanced()
        
    except KeyboardInterrupt:
        logger.info("")
        logger.info("Enhanced Profit Monitor stopped by user")
        return 0
    except Exception as e:
        logger.error(f"Error running enhanced profit monitor: {str(e)}")
        return 1

if __name__ == "__main__":
    sys.exit(main()) 