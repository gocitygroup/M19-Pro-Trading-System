#!/usr/bin/env python3
"""
Simple HTTP-only version of the web interface
No WebSockets - just regular HTTP requests
"""

import sys
import os
project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, project_root)

from flask import Flask, render_template, request, jsonify, redirect, url_for
from datetime import datetime
import logging
from src.config.config import load_config
from src.api.api_service import TradingAPIService

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize Flask app
app = Flask(__name__)
app.config['SECRET_KEY'] = 'your-secret-key-change-this'

# Global variables
config = load_config()
api_service = TradingAPIService()

@app.route('/')
def index():
    """Serve the main dashboard"""
    return render_template('index_simple.html')

@app.route('/api/positions')
def get_positions():
    """Get current positions"""
    try:
        positions_data = api_service.get_positions_summary()
        return jsonify(positions_data)
    except Exception as e:
        logger.error(f"Error getting positions: {str(e)}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/close_profitable', methods=['POST'])
def close_profitable():
    """Close all profitable positions"""
    try:
        result = api_service.request_position_close('profit')
        return jsonify(result)
    except Exception as e:
        logger.error(f"Error closing profitable positions: {str(e)}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/close_losing', methods=['POST'])
def close_losing():
    """Close all losing positions"""
    try:
        result = api_service.request_position_close('loss')
        return jsonify(result)
    except Exception as e:
        logger.error(f"Error closing losing positions: {str(e)}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/close_all', methods=['POST'])
def close_all():
    """Close all positions"""
    try:
        result = api_service.request_position_close('all')
        return jsonify(result)
    except Exception as e:
        logger.error(f"Error closing all positions: {str(e)}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/close_position', methods=['POST'])
def close_position():
    """Close single position"""
    try:
        data = request.get_json()
        ticket = data.get('ticket')
        if not ticket:
            return jsonify({'error': 'Ticket required'}), 400
            
        result = api_service.request_position_close('single', ticket)
        return jsonify(result)
    except Exception as e:
        logger.error(f"Error closing position: {str(e)}")
        return jsonify({'error': str(e)}), 500

@app.route('/health')
def health_check():
    """Health check endpoint"""
    return jsonify({'status': 'healthy', 'timestamp': datetime.now().isoformat()})

@app.errorhandler(500)
def handle_500(e):
    """Handle 500 errors"""
    logger.error(f"Internal server error: {str(e)}")
    return jsonify({'error': 'Internal server error'}), 500

if __name__ == '__main__':
    try:
        logger.info("Starting Simple HTTP Web Interface Server...")
        logger.info("✅ No WebSocket dependencies required!")
        logger.info("Server will be available at:")
        logger.info("  - http://localhost:44444")
        logger.info("  - http://127.0.0.1:44444")
        
        app.run(host='0.0.0.0', port=44444, debug=True)
        
    except KeyboardInterrupt:
        logger.info("Shutting down server...")
    except Exception as e:
        logger.error(f"Server error: {str(e)}")
    finally:
        logger.info("Server shutdown complete") 