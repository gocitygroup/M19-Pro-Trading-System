"""
Flask web interface for the Forex Profit Monitoring System.
"""
import sys
import os
from urllib.parse import urlparse
# Add project root to Python path
project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, project_root)

import MetaTrader5 as mt5
from flask import Flask, render_template, request, redirect, url_for, flash, session, make_response, jsonify
from flask_socketio import SocketIO, emit
import sqlite3
from datetime import datetime, timedelta
import pytz
import threading
import time
import logging
from functools import wraps
from src.config.config import load_config, TRADING_SESSIONS, TRADING_BOT_CONFIG, PROFIT_SCOUTING_CONFIG
from src.config.auth_config import auth_config, login_required
from src.api.api_service import TradingAPIService
from src.api.enhanced_api_service import enhanced_api_service

try:
    from flask_cors import CORS
    CORS_AVAILABLE = True
except ImportError:
    CORS_AVAILABLE = False

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize Flask app and SocketIO
app = Flask(__name__, static_folder='static', static_url_path='/static')
app.config['SECRET_KEY'] = auth_config.secret_key
app.config['PERMANENT_SESSION_LIFETIME'] = timedelta(seconds=auth_config.session_lifetime)

# Configure CORS with proper origin handling
if CORS_AVAILABLE:
    try:
        origins = auth_config.allowed_origins
        logger.info(f"Configuring CORS with origins: {origins}")
        CORS(app, 
             origins=origins,
             supports_credentials=True,
             allow_headers=['Content-Type', 'Authorization', 'X-Requested-With'],
             expose_headers=['Content-Type'],
             methods=['GET', 'POST', 'OPTIONS'],
             allow_origin_regex=None)  # Disable regex matching for better security
        logger.info("CORS configured successfully")
    except Exception as e:
        logger.error(f"Error configuring CORS: {str(e)}")
        # Don't fallback to allow all origins for security
        logger.error("CORS configuration failed, embedding will be restricted")
else:
    logger.warning("flask-cors not installed, CORS not configured")

# Configure SocketIO with proper settings
socketio = SocketIO(
    app,
    cors_allowed_origins=auth_config.allowed_origins,
    async_mode='threading',
    logger=False,
    engineio_logger=False,
    ping_timeout=60,
    ping_interval=25,
    transports=['websocket', 'polling'],
    manage_session=False,
    always_connect=True,
    max_http_buffer_size=10000000
)

# Global variables
config = load_config()
api_service = TradingAPIService()
monitoring_thread = None
monitoring_active = False
bot_status_thread = None
bot_status_active = False
last_bot_status = None

# Initialize configuration manager with current config
from src.config import get_config_manager, initialize_from_static_config
initialize_from_static_config(config)
logger.info("Configuration manager initialized with static config")


def get_db_connection():
    """Create a SQLite connection using configured database path."""
    db_path = os.path.join(project_root, config['db']['path'])
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    return conn


def _normalize_time(value: str) -> str:
    """Normalize time strings to HH:MM:SS format."""
    if len(value) == 5:
        return f"{value}:00"
    return value


# Cache for session-pair mappings to avoid repeated DB queries
_session_pair_cache = {'last_check': None, 'ttl': 300}  # 5 minute TTL

def ensure_sessions_and_pairs():
    """
    Ensure trading sessions and pair mappings exist.
    Only reads from database - never creates or modifies pairs.
    Uses caching to improve performance.
    """
    import time as time_module
    
    # Check cache first
    now = time_module.time()
    if (_session_pair_cache.get('last_check') and 
        now - _session_pair_cache['last_check'] < _session_pair_cache['ttl']):
        return  # Use cached data
    
    conn = get_db_connection()
    try:
        cursor = conn.cursor()

        # Update sessions from config (sessions can change, pairs are DB-only)
        for session in TRADING_SESSIONS:
            name = session['name']
            start_time = _normalize_time(session['start_time'])
            end_time = _normalize_time(session['end_time'])
            volatility = session.get('volatility_factor', 1.0)

            cursor.execute(
                '''
                INSERT OR IGNORE INTO trading_sessions (name, start_time, end_time, volatility_factor, is_active)
                VALUES (?, ?, ?, ?, 1)
                ''',
                (name, start_time, end_time, volatility)
            )

            cursor.execute(
                '''
                UPDATE trading_sessions
                SET start_time = ?, end_time = ?, volatility_factor = ?, is_active = 1
                WHERE name = ?
                ''',
                (start_time, end_time, volatility, name)
            )

        # Only ensure mappings for existing pairs from database
        # Never create new pairs - pairs must exist in DB first
        session_ids = [row['id'] for row in cursor.execute('SELECT id FROM trading_sessions').fetchall()]
        pair_ids = [row['id'] for row in cursor.execute('SELECT id FROM currency_pairs WHERE is_active = 1').fetchall()]

        # Batch insert for better performance
        if session_ids and pair_ids:
            mappings = [(session_id, pair_id) for session_id in session_ids for pair_id in pair_ids]
            cursor.executemany(
                '''
                INSERT OR IGNORE INTO session_pairs (session_id, pair_id, trade_direction)
                VALUES (?, ?, 'neutral')
                ''',
                mappings
            )

        conn.commit()
        _session_pair_cache['last_check'] = now
    finally:
        conn.close()


def is_session_active(start_time: str, end_time: str, current_time: datetime.time) -> bool:
    """Determine if a session is currently active using UTC times."""
    start = datetime.strptime(start_time, '%H:%M:%S').time()
    end = datetime.strptime(end_time, '%H:%M:%S').time()
    if start < end:
        return start <= current_time < end
    return current_time >= start or current_time < end

def allow_iframe(f):
    """Decorator to allow iframe embedding for specific routes with proper security headers"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        response = make_response(f(*args, **kwargs))
        
        # Get origin from request
        origin = request.headers.get('Origin')
        if origin and origin in auth_config.allowed_origins:
            # Modern approach: Use frame-ancestors instead of X-Frame-Options
            response.headers['Content-Security-Policy'] = f"frame-ancestors {origin}; default-src 'self' {origin}; script-src 'self' 'unsafe-inline' 'unsafe-eval' {origin}; style-src 'self' 'unsafe-inline'; img-src 'self' data:; connect-src 'self' {origin} ws: wss:;"
            # Keep X-Frame-Options as fallback for older browsers
            response.headers['X-Frame-Options'] = f'ALLOW-FROM {origin}'
        else:
            # Fallback to deny if origin not in allowed list
            response.headers['Content-Security-Policy'] = "frame-ancestors 'none'; default-src 'self'"
            response.headers['X-Frame-Options'] = 'DENY'
            
        # Add other security headers
        response.headers['X-Content-Type-Options'] = 'nosniff'
        response.headers['X-XSS-Protection'] = '1; mode=block'
        response.headers['Referrer-Policy'] = 'strict-origin-when-cross-origin'
        # Add cache control headers to prevent caching of sensitive data
        response.headers['Cache-Control'] = 'no-store, no-cache, must-revalidate, max-age=0'
        response.headers['Pragma'] = 'no-cache'
        response.headers['Expires'] = '0'
        
        return response
    return decorated_function

def check_embed_token():
    """Verify embed authentication token and return permissions"""
    token = request.args.get('token')
    if not token:
        return None
        
    try:
        # Get request domain
        origin = request.headers.get('Origin')
        if not origin:
            logger.warning("No origin header in embed request")
            return None
            
        request_domain = urlparse(origin).netloc
        
        # Validate token and get permissions
        permissions = auth_config.validate_embed_token(token, request_domain)
        return permissions
        
    except ValueError as e:
        logger.warning(f"Token validation failed: {str(e)}")
        return None

def check_embed_permissions(permissions, required_view=None, required_features=None):
    """Check if the embed token has required permissions"""
    if not permissions:
        return False
        
    if required_view and required_view not in permissions.get('views', []):
        return False
        
    if required_features:
        token_features = permissions.get('features', [])
        if not all(feature in token_features for feature in required_features):
            return False
            
    return True

# Embed-specific routes
@app.route('/embed')
@allow_iframe
def embed():
    """Embedded dashboard view"""
    permissions = check_embed_token()
    if not permissions or not check_embed_permissions(permissions, required_view='full'):
        return "Unauthorized", 401
    return render_template('embed.html', permissions=permissions)

@app.route('/embed/minimal')
@allow_iframe
def embed_minimal():
    """Minimal embedded view with just essential metrics"""
    permissions = check_embed_token()
    if not permissions or not check_embed_permissions(permissions, required_view='minimal'):
        return "Unauthorized", 401
    return render_template('embed_minimal.html', permissions=permissions)

@app.route('/embed/chart')
@allow_iframe
def embed_chart():
    """Embedded chart view"""
    permissions = check_embed_token()
    if not permissions or not check_embed_permissions(permissions, required_view='chart'):
        return "Unauthorized", 401
    return render_template('embed_chart.html', permissions=permissions)

@app.route('/embed/positions')
@allow_iframe
def embed_positions():
    """Embedded positions table view"""
    permissions = check_embed_token()
    if not permissions or not check_embed_permissions(permissions, required_view='positions'):
        return "Unauthorized", 401
    return render_template('embed_positions.html', permissions=permissions)

@app.route('/embed/token', methods=['POST'])
@login_required
def generate_embed_token():
    """Generate a new embed token"""
    data = request.get_json()
    if not data or 'domain' not in data:
        return jsonify({'error': 'Domain is required'}), 400
        
    try:
        permissions = data.get('permissions')
        token = auth_config.generate_embed_token(data['domain'], permissions)
        return jsonify({
            'token': token,
            'domain': data['domain'],
            'permissions': permissions
        })
    except ValueError as e:
        return jsonify({'error': str(e)}), 400

# Original routes with iframe support option
@app.route('/')
@login_required
def index():
    """Serve the main dashboard"""
    permissions = check_embed_token()
    if permissions and check_embed_permissions(permissions, required_view='full'):
        return render_template('index.html', embed=True, permissions=permissions)
    return render_template('index.html', embed=False)


@app.route('/manual')
@login_required
def manual():
    """Serve the trader user manual (responsive help page)."""
    return render_template('manual.html')


@app.route('/automation')
@login_required
def automation_dashboard():
    """Serve the GSignalX automation dashboard."""
    return render_template('automation.html')

def background_monitoring():
    """Enhanced background thread for real-time monitoring"""
    global monitoring_active
    logger.info("Enhanced background monitoring started")
    
    while monitoring_active:
        try:
            # Get real-time data from enhanced API service
            positions_data = enhanced_api_service.get_real_time_summary()
            
            # Emit optimized real-time updates to all connected clients
            try:
                with app.app_context():
                    socketio.emit('positions_update', {
                        'positions': positions_data.get('positions', []),
                        'summary': positions_data.get('summary', {}),
                        'account': positions_data.get('account', {}),
                        'timestamp': positions_data.get('last_update', datetime.now().isoformat()),
                        'cached': positions_data.get('cached', False),
                        'performance': {
                            'win_rate': positions_data.get('account', {}).get('win_rate', 0),
                            'avg_profit_per_position': positions_data.get('account', {}).get('avg_profit_per_position', 0)
                        }
                    }, namespace='/')
            except Exception as emit_error:
                logger.error(f"Error emitting positions update: {str(emit_error)}")
            
            # Enhanced update frequency: 2 seconds for real-time feel
            time.sleep(2)
            
        except Exception as e:
            logger.error(f"Error in enhanced background monitoring: {str(e)}")
            try:
                with app.app_context():
                    socketio.emit('error', {
                        'message': f'Enhanced monitoring error: {str(e)}',
                        'timestamp': datetime.now().isoformat()
                    }, namespace='/')
            except Exception as emit_error:
                logger.error(f"Error emitting error message: {str(emit_error)}")
            time.sleep(5)  # Shorter wait on error for faster recovery

def start_monitoring():
    """Start background monitoring thread"""
    global monitoring_thread, monitoring_active
    
    if monitoring_thread is None or not monitoring_thread.is_alive():
        monitoring_active = True
        monitoring_thread = threading.Thread(target=background_monitoring)
        monitoring_thread.daemon = True
        monitoring_thread.start()
        logger.info("Monitoring thread started")

def monitor_bot_status():
    """Monitor MarketSessionTradingBot status and emit events"""
    global last_bot_status, bot_status_active
    import json
    
    bot_status_file = os.path.join(project_root, 'bot_status.json')
    
    while bot_status_active:
        try:
            if os.path.exists(bot_status_file):
                with open(bot_status_file, 'r') as f:
                    status = json.load(f)
                    
                # Check if this is a MarketSessionTradingBot status
                if status.get('bot_type') == 'MarketSessionTradingBot':
                    current_connected = status.get('is_connected', False)
                    current_message = status.get('message', '')
                    last_updated = status.get('last_updated', '')
                    
                    # Only emit if status changed
                    if last_bot_status is None or last_bot_status.get('is_connected') != current_connected:
                        try:
                            with app.app_context():
                                if current_connected:
                                    socketio.emit('bot_status', {
                                        'bot': 'MarketSessionTradingBot',
                                        'status': 'connected',
                                        'message': current_message,
                                        'timestamp': last_updated
                                    }, namespace='/')
                                    logger.info(f"MarketSessionTradingBot connected: {current_message}")
                                else:
                                    socketio.emit('bot_status', {
                                        'bot': 'MarketSessionTradingBot',
                                        'status': 'disconnected',
                                        'message': current_message,
                                        'timestamp': last_updated
                                    }, namespace='/')
                                    logger.info(f"MarketSessionTradingBot disconnected: {current_message}")
                        except Exception as emit_error:
                            logger.error(f"Error emitting bot status: {str(emit_error)}")
                        
                        last_bot_status = {
                            'is_connected': current_connected,
                            'message': current_message,
                            'last_updated': last_updated
                        }
            
            time.sleep(2)  # Check every 2 seconds
            
        except Exception as e:
            logger.error(f"Error monitoring bot status: {str(e)}")
            time.sleep(5)

def start_bot_status_monitoring():
    """Start bot status monitoring thread"""
    global bot_status_thread, bot_status_active
    
    if bot_status_thread is None or not bot_status_thread.is_alive():
        bot_status_active = True
        bot_status_thread = threading.Thread(target=monitor_bot_status)
        bot_status_thread.daemon = True
        bot_status_thread.start()
        logger.info("Bot status monitoring thread started")

def stop_bot_status_monitoring():
    """Stop bot status monitoring thread"""
    global bot_status_active
    bot_status_active = False

def stop_monitoring():
    """Stop background monitoring thread"""
    global monitoring_active
    monitoring_active = False
    logger.info("Monitoring thread stopped")

# Authentication routes
@app.route('/login', methods=['GET', 'POST'])
def login():
    """Handle user login."""
    # Redirect if already logged in
    if 'user_id' in session:
        logger.debug(f"Already logged in user {session['user_id']} redirected to index")
        return redirect(url_for('index'))
        
    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        password = request.form.get('password', '').strip()
        remember = request.form.get('remember') == 'on'
        
        logger.debug(f"Login attempt for username: {username}")
        
        if not username or not password:
            flash('Username and password are required.', 'danger')
            return render_template('login.html')
        
        if username == auth_config.username and auth_config.verify_password(password):
            session['user_id'] = username
            if remember:
                # Set session to last longer
                session.permanent = True
                app.permanent_session_lifetime = timedelta(seconds=auth_config.remember_me_lifetime)
                logger.info(f"Extended session created for user {username}")
            else:
                # Standard session lifetime
                session.permanent = True
                app.permanent_session_lifetime = timedelta(seconds=auth_config.session_lifetime)
                logger.info(f"Standard session created for user {username}")
            
            return redirect(url_for('index'))
            
            flash('Login successful!', 'success')
            next_page = request.args.get('next')
            return redirect(next_page if next_page else url_for('index'))
        else:
            logger.warning(f"Failed login attempt for username: {username}")
            flash('Invalid username or password.', 'danger')
    
    return render_template('login.html')

@app.route('/logout')
def logout():
    """Handle user logout."""
    if 'user_id' in session:
        logger.info(f"User {session['user_id']} logged out")
    session.clear()
    flash('You have been logged out.', 'info')
    return redirect(url_for('login'))

@app.route('/settings', methods=['GET', 'POST'])
@login_required
def settings():
    """Handle user settings."""
    from src.config import get_config_manager, initialize_from_static_config
    
    # Initialize config manager if needed
    config_manager = get_config_manager()
    if (not config_manager.get('profit_monitor') or not config_manager.get('trading_bot')
            or not config_manager.get('profit_scouting')):
        initialize_from_static_config(config)
    
    if request.method == 'POST':
        settings_type = request.form.get('settings_type', 'account')
        current_password = request.form.get('current_password', '').strip()
        
        if not current_password:
            flash('Current password is required.', 'danger')
            return redirect(url_for('settings'))
        
        if not auth_config.verify_password(current_password):
            logger.warning(f"Invalid current password in settings update for user {session['user_id']}")
            flash('Current password is incorrect.', 'danger')
            return redirect(url_for('settings'))
        
        if settings_type == 'account':
            # Handle account settings
            new_username = request.form.get('new_username', '').strip()
            new_password = request.form.get('new_password', '').strip()
            
            if new_username or new_password:
                success = auth_config.update_credentials(
                    username=new_username if new_username else None,
                    password=new_password if new_password else None
                )
                
                if success:
                    # Update session if username changed
                    if new_username:
                        session['user_id'] = new_username
                    flash('Account settings updated successfully.', 'success')
                    logger.info(f"Account settings updated for user {session['user_id']}")
                else:
                    flash('Error updating account settings. Please try again.', 'danger')
                    logger.error(f"Failed to update account settings for user {session['user_id']}")
        
        elif settings_type == 'profit_monitor':
            # Handle profit monitor settings
            try:
                # Extract and validate profit monitor settings
                updates = {}
                
                # Numeric settings with validation
                numeric_fields = {
                    'min_profit_percent': (0.1, 10.0, float),
                    'trailing_stop_percent': (0.1, 5.0, float),
                    'check_interval': (1, 3600, int),
                    'partial_close_threshold': (0.5, 20.0, float),
                    'partial_close_percent': (10, 90, int),
                    'max_retries': (1, 10, int),
                    'retry_delay': (0.5, 60, float)
                }
                
                for field, (min_val, max_val, type_func) in numeric_fields.items():
                    value = request.form.get(field)
                    if value:
                        try:
                            value = type_func(value)
                            if min_val <= value <= max_val:
                                updates[field] = value
                            else:
                                flash(f'Invalid value for {field.replace("_", " ").title()}: must be between {min_val} and {max_val}', 'warning')
                        except ValueError:
                            flash(f'Invalid value for {field.replace("_", " ").title()}', 'warning')
                
                # Boolean settings
                updates['partial_close_enabled'] = request.form.get('partial_close_enabled') == 'on'
                updates['enable_market_check'] = request.form.get('enable_market_check') == 'on'
                
                # Log level
                log_level = request.form.get('log_level', 'INFO')
                if log_level in ['DEBUG', 'INFO', 'WARNING', 'ERROR']:
                    updates['log_level'] = log_level
                
                # Update configuration
                if config_manager.update_profit_monitor_config(updates):
                    flash('Profit monitor settings updated successfully! Changes will take effect immediately.', 'success')
                    logger.info(f"Profit monitor settings updated by user {session['user_id']}: {updates}")
                    
                    # Notify monitoring scripts to reload config
                    _notify_config_change()
                else:
                    flash('Error updating profit monitor settings.', 'danger')
                    logger.error(f"Failed to update profit monitor settings")
                
            except Exception as e:
                flash(f'Error updating profit monitor settings: {str(e)}', 'danger')
                logger.error(f"Exception updating profit monitor settings: {str(e)}")

        elif settings_type == 'trading_bot':
            try:
                updates = {}

                numeric_fields = {
                    'max_positions': (1, 20, int),
                    'volume': (0.01, 5.0, float),
                    'scalp_multiplier': (0.0, 5.0, float),
                    'base_entry_pips': (0, 50, int),
                    'min_spread_multiplier': (0.5, 10.0, float),
                    'order_expiry_minutes': (1, 240, int),
                    'session_check_interval': (1, 300, int)
                }

                for field, (min_val, max_val, type_func) in numeric_fields.items():
                    value = request.form.get(field)
                    if value is not None and value != '':
                        try:
                            value = type_func(value)
                            if min_val <= value <= max_val:
                                updates[field] = value
                            else:
                                flash(f'Invalid value for {field.replace("_", " ").title()}: must be between {min_val} and {max_val}', 'warning')
                        except ValueError:
                            flash(f'Invalid value for {field.replace("_", " ").title()}', 'warning')

                if updates and config_manager.update_trading_bot_config(updates):
                    flash('Trading bot settings updated successfully. Changes apply immediately.', 'success')
                    logger.info(f"Trading bot settings updated by user {session['user_id']}: {updates}")
                    _notify_config_change()
                else:
                    flash('No trading bot settings were changed.', 'info' if not updates else 'danger')
            except Exception as e:
                flash(f'Error updating trading bot settings: {str(e)}', 'danger')
                logger.error(f"Exception updating trading bot settings: {str(e)}")
        
        elif settings_type == 'profit_scouting':
            try:
                updates = {}

                numeric_fields = {
                    'target_profit_pair': (0.1, 10000.0, float),
                    'target_profit_position': (0.1, 10000.0, float),
                    'total_target_profit': (0.1, 100000.0, float),
                    'order_deviation': (1, 100, int),
                    'magic_number': (1, 999999, int),
                    'check_interval': (1, 3600, int),
                    'max_retries': (1, 10, int),
                    'retry_delay': (0.5, 60, float)
                }

                for field, (min_val, max_val, type_func) in numeric_fields.items():
                    value = request.form.get(field)
                    if value is not None and value != '':
                        try:
                            value = type_func(value)
                            if min_val <= value <= max_val:
                                updates[field] = value
                            else:
                                flash(f'Invalid value for {field.replace("_", " ").title()}: must be between {min_val} and {max_val}', 'warning')
                        except ValueError:
                            flash(f'Invalid value for {field.replace("_", " ").title()}', 'warning')

                if updates and config_manager.update_profit_scouting_config(updates):
                    flash('Profit scouting settings updated successfully. Changes apply immediately.', 'success')
                    logger.info(f"Profit scouting settings updated by user {session['user_id']}: {updates}")
                    _notify_config_change()
                else:
                    flash('No profit scouting settings were changed.', 'info' if not updates else 'danger')
            except Exception as e:
                flash(f'Error updating profit scouting settings: {str(e)}', 'danger')
                logger.error(f"Exception updating profit scouting settings: {str(e)}")
        
        return redirect(url_for('settings'))
    
    # GET request - render settings page with current config
    profit_config = config_manager.get_profit_monitor_config()
    trading_config = config_manager.get_trading_bot_config()
    profit_scouting_config = config_manager.get_profit_scouting_config()
    return render_template(
        'settings.html',
        profit_config=profit_config,
        trading_config=trading_config,
        trading_defaults=TRADING_BOT_CONFIG,
        profit_scouting_config=profit_scouting_config,
        profit_scouting_defaults=PROFIT_SCOUTING_CONFIG
    )

def _notify_config_change():
    """Notify running scripts/monitors that configuration has changed"""
    try:
        # Create a signal file that monitors can check
        project_root = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
        signal_file = os.path.join(project_root, 'config', 'config_changed.signal')
        
        with open(signal_file, 'w') as f:
            f.write(datetime.now().isoformat())
        
        logger.info("Configuration change signal file created")
    except Exception as e:
        logger.error(f"Error creating config change signal: {str(e)}")

@app.route('/health')
def health_check():
    """Health check endpoint"""
    return {'status': 'healthy', 'timestamp': datetime.now().isoformat()}

# Configuration API Endpoints
@app.route('/api/config/profit_monitor', methods=['GET'])
@login_required
def get_profit_monitor_config():
    """Get current profit monitor configuration"""
    try:
        from src.config import get_config_manager
        config_manager = get_config_manager()
        profit_config = config_manager.get_profit_monitor_config()
        
        return jsonify({
            'status': 'success',
            'config': profit_config,
            'timestamp': datetime.now().isoformat()
        })
    except Exception as e:
        logger.error(f"Error getting profit monitor config: {str(e)}")
        return jsonify({
            'status': 'error',
            'error': str(e)
        }), 500

@app.route('/api/config/profit_monitor', methods=['POST'])
@login_required
def update_profit_monitor_config_api():
    """Update profit monitor configuration via API"""
    try:
        from src.config import get_config_manager
        
        data = request.get_json()
        if not data:
            return jsonify({
                'status': 'error',
                'error': 'No data provided'
            }), 400
        
        config_manager = get_config_manager()
        
        # Validate and update configuration
        updates = {}
        
        # Numeric fields with validation
        numeric_fields = {
            'min_profit_percent': (0.1, 10.0, float),
            'trailing_stop_percent': (0.1, 5.0, float),
            'check_interval': (1, 3600, int),
            'partial_close_threshold': (0.5, 20.0, float),
            'partial_close_percent': (10, 90, int),
            'max_retries': (1, 10, int),
            'retry_delay': (0.5, 60, float)
        }
        
        for field, (min_val, max_val, type_func) in numeric_fields.items():
            if field in data:
                try:
                    value = type_func(data[field])
                    if min_val <= value <= max_val:
                        updates[field] = value
                    else:
                        return jsonify({
                            'status': 'error',
                            'error': f'{field} must be between {min_val} and {max_val}'
                        }), 400
                except (ValueError, TypeError):
                    return jsonify({
                        'status': 'error',
                        'error': f'Invalid value for {field}'
                    }), 400
        
        # Boolean fields
        if 'partial_close_enabled' in data:
            updates['partial_close_enabled'] = bool(data['partial_close_enabled'])
        if 'enable_market_check' in data:
            updates['enable_market_check'] = bool(data['enable_market_check'])
        
        # Log level
        if 'log_level' in data:
            if data['log_level'] in ['DEBUG', 'INFO', 'WARNING', 'ERROR']:
                updates['log_level'] = data['log_level']
            else:
                return jsonify({
                    'status': 'error',
                    'error': 'Invalid log_level'
                }), 400
        
        # Update configuration
        if config_manager.update_profit_monitor_config(updates):
            _notify_config_change()
            
            return jsonify({
                'status': 'success',
                'message': 'Configuration updated successfully',
                'updated_fields': list(updates.keys()),
                'timestamp': datetime.now().isoformat()
            })
        else:
            return jsonify({
                'status': 'error',
                'error': 'Failed to update configuration'
            }), 500
            
    except Exception as e:
        logger.error(f"Error updating profit monitor config: {str(e)}")
        return jsonify({
            'status': 'error',
            'error': str(e)
        }), 500

@app.route('/api/config/profit_monitor/reset', methods=['POST'])
@login_required
def reset_profit_monitor_config():
    """Reset profit monitor configuration to defaults"""
    try:
        from src.config import get_config_manager
        from src.config.config import PROFIT_MONITOR_CONFIG
        
        config_manager = get_config_manager()
        
        # Reset to defaults
        if config_manager.reset_to_defaults('profit_monitor', PROFIT_MONITOR_CONFIG):
            _notify_config_change()
            
            return jsonify({
                'status': 'success',
                'message': 'Configuration reset to defaults',
                'config': PROFIT_MONITOR_CONFIG,
                'timestamp': datetime.now().isoformat()
            })
        else:
            return jsonify({
                'status': 'error',
                'error': 'Failed to reset configuration'
            }), 500
            
    except Exception as e:
        logger.error(f"Error resetting profit monitor config: {str(e)}")
        return jsonify({
            'status': 'error',
            'error': str(e)
        }), 500


@app.route('/api/config/trading_bot', methods=['GET'])
@login_required
def get_trading_bot_config():
    """Get current trading bot configuration"""
    try:
        from src.config import get_config_manager
        config_manager = get_config_manager()
        trading_config = config_manager.get_trading_bot_config()

        return jsonify({
            'status': 'success',
            'config': trading_config,
            'timestamp': datetime.now().isoformat()
        })
    except Exception as e:
        logger.error(f"Error getting trading bot config: {str(e)}")
        return jsonify({
            'status': 'error',
            'error': str(e)
        }), 500


@app.route('/api/config/trading_bot', methods=['POST'])
@login_required
def update_trading_bot_config_api():
    """Update trading bot configuration via API"""
    try:
        from src.config import get_config_manager

        data = request.get_json()
        if not data:
            return jsonify({
                'status': 'error',
                'error': 'No data provided'
            }), 400

        config_manager = get_config_manager()
        updates = {}

        numeric_fields = {
            'max_positions': (1, 20, int),
            'volume': (0.01, 5.0, float),
            'scalp_multiplier': (0.0, 5.0, float),
            'base_entry_pips': (0, 50, int),
            'min_spread_multiplier': (0.5, 10.0, float),
            'order_expiry_minutes': (1, 240, int),
            'session_check_interval': (1, 300, int)
        }

        for field, (min_val, max_val, type_func) in numeric_fields.items():
            if field in data:
                try:
                    value = type_func(data[field])
                    if min_val <= value <= max_val:
                        updates[field] = value
                    else:
                        return jsonify({
                            'status': 'error',
                            'error': f'{field} must be between {min_val} and {max_val}'
                        }), 400
                except (ValueError, TypeError):
                    return jsonify({
                        'status': 'error',
                        'error': f'Invalid value for {field}'
                    }), 400

        if updates and config_manager.update_trading_bot_config(updates):
            _notify_config_change()
            return jsonify({
                'status': 'success',
                'message': 'Configuration updated successfully',
                'updated_fields': list(updates.keys()),
                'timestamp': datetime.now().isoformat()
            })

        return jsonify({
            'status': 'error',
            'error': 'No valid fields provided'
        }), 400

    except Exception as e:
        logger.error(f"Error updating trading bot config: {str(e)}")
        return jsonify({
            'status': 'error',
            'error': str(e)
        }), 500


@app.route('/api/config/trading_bot/reset', methods=['POST'])
@login_required
def reset_trading_bot_config():
    """Reset trading bot configuration to defaults"""
    try:
        from src.config import get_config_manager
        from src.config.config import TRADING_BOT_CONFIG

        config_manager = get_config_manager()

        if config_manager.reset_to_defaults('trading_bot', TRADING_BOT_CONFIG):
            _notify_config_change()
            return jsonify({
                'status': 'success',
                'message': 'Configuration reset to defaults',
                'config': TRADING_BOT_CONFIG,
                'timestamp': datetime.now().isoformat()
            })

        return jsonify({
            'status': 'error',
            'error': 'Failed to reset configuration'
        }), 500

    except Exception as e:
        logger.error(f"Error resetting trading bot config: {str(e)}")
        return jsonify({
            'status': 'error',
            'error': str(e)
        }), 500


# Trading Board Endpoints
@app.route('/api/trading_board', methods=['GET'])
@login_required
def get_trading_board():
    """Return trading sessions with active status and pair directions.
    Only returns pairs that exist in the database."""
    conn = None
    try:
        # Ensure sessions are synced (pairs are read-only from DB)
        ensure_sessions_and_pairs()
        conn = get_db_connection()
        utc_now = datetime.utcnow().time()

        cursor = conn.cursor()
        
        # Single optimized query to get all sessions
        cursor.execute(
            '''
            SELECT id, name, time(start_time) AS start_time, time(end_time) AS end_time,
                   volatility_factor, is_active
            FROM trading_sessions
            ORDER BY start_time
            '''
        )
        session_rows = cursor.fetchall()

        # Check if category column exists (for backward compatibility)
        cursor.execute("PRAGMA table_info(currency_pairs)")
        columns = [col[1] for col in cursor.fetchall()]
        has_category_column = 'category' in columns
        
        # Single optimized query to get all pairs for all sessions
        # Only returns pairs that exist in the database (cp.is_active = 1)
        # Category comes from database if column exists, otherwise defaults to 'other'
        if has_category_column:
            cursor.execute(
                '''
                SELECT ts.id AS session_id,
                       cp.id AS pair_id,
                       cp.symbol,
                       COALESCE(cp.category, 'other') AS category,
                       COALESCE(sp.trade_direction, 'neutral') AS trade_direction
                FROM trading_sessions ts
                CROSS JOIN currency_pairs cp
                LEFT JOIN session_pairs sp 
                    ON sp.pair_id = cp.id AND sp.session_id = ts.id
                WHERE cp.is_active = 1
                ORDER BY ts.id, cp.category, cp.symbol
                '''
            )
        else:
            # Fallback for databases without category column
            cursor.execute(
                '''
                SELECT ts.id AS session_id,
                       cp.id AS pair_id,
                       cp.symbol,
                       'other' AS category,
                       COALESCE(sp.trade_direction, 'neutral') AS trade_direction
                FROM trading_sessions ts
                CROSS JOIN currency_pairs cp
                LEFT JOIN session_pairs sp 
                    ON sp.pair_id = cp.id AND sp.session_id = ts.id
                WHERE cp.is_active = 1
                ORDER BY ts.id, cp.symbol
                '''
            )
        all_pairs = cursor.fetchall()

        # Group pairs by session_id for efficient lookup
        pairs_by_session = {}
        for pair_row in all_pairs:
            session_id = pair_row['session_id']
            if session_id not in pairs_by_session:
                pairs_by_session[session_id] = []
            pairs_by_session[session_id].append({
                'pair_id': pair_row['pair_id'],
                'symbol': pair_row['symbol'],
                'category': pair_row['category'],
                'direction': pair_row['trade_direction']
            })

        # Build sessions list
        sessions = []
        for row in session_rows:
            start_time = _normalize_time(row['start_time'])
            end_time = _normalize_time(row['end_time'])
            active = bool(row['is_active']) and is_session_active(start_time, end_time, utc_now)

            sessions.append({
                'id': row['id'],
                'name': row['name'],
                'start_time': start_time,
                'end_time': end_time,
                'volatility_factor': row['volatility_factor'],
                'active': active,
                'pairs': pairs_by_session.get(row['id'], [])
            })

        return jsonify({
            'status': 'success',
            'sessions': sessions,
            'utc_now': datetime.utcnow().isoformat()
        })

    except Exception as e:
        logger.error(f"Error fetching trading board data: {str(e)}")
        return jsonify({'status': 'error', 'error': str(e)}), 500
    finally:
        if conn:
            conn.close()


@app.route('/api/trading_board/direction', methods=['POST'])
@login_required
def update_trading_direction():
    """Update trade direction for a currency pair within a session.
    Only works with pairs that exist in the database."""
    conn = None
    try:
        data = request.get_json() or {}
        session_id = data.get('session_id')
        pair_id = data.get('pair_id')
        direction = (data.get('direction') or '').lower()

        if direction not in ('buy', 'sell', 'neutral'):
            return jsonify({'status': 'error', 'error': 'Invalid direction'}), 400
        if not session_id or not pair_id:
            return jsonify({'status': 'error', 'error': 'session_id and pair_id are required'}), 400

        conn = get_db_connection()
        cursor = conn.cursor()

        # Validate session and pair exist in database
        session_check = cursor.execute('SELECT 1 FROM trading_sessions WHERE id = ?', (session_id,)).fetchone()
        if not session_check:
            return jsonify({'status': 'error', 'error': 'Session not found'}), 404
        
        pair_check = cursor.execute('SELECT 1 FROM currency_pairs WHERE id = ? AND is_active = 1', (pair_id,)).fetchone()
        if not pair_check:
            return jsonify({'status': 'error', 'error': 'Currency pair not found or inactive'}), 404

        # Ensure mapping exists, then update direction (only for existing pairs)
        cursor.execute(
            '''
            INSERT OR IGNORE INTO session_pairs (session_id, pair_id, trade_direction)
            VALUES (?, ?, 'neutral')
            ''',
            (session_id, pair_id)
        )
        cursor.execute(
            '''
            UPDATE session_pairs
            SET trade_direction = ?, updated_at = CURRENT_TIMESTAMP
            WHERE session_id = ? AND pair_id = ?
            ''',
            (direction, session_id, pair_id)
        )

        conn.commit()
        
        # Invalidate cache to ensure fresh data on next request
        _session_pair_cache['last_check'] = None
        _notify_config_change()

        return jsonify({
            'status': 'success',
            'message': 'Trade direction updated',
            'session_id': session_id,
            'pair_id': pair_id,
            'direction': direction
        })

    except Exception as e:
        logger.error(f"Error updating trading direction: {str(e)}")
        return jsonify({'status': 'error', 'error': str(e)}), 500
    finally:
        if conn:
            conn.close()

@app.errorhandler(500)
def handle_500(e):
    """Handle 500 errors"""
    logger.error(f"Internal server error: {str(e)}")
    return {'error': 'Internal server error'}, 500

# WebSocket Events
@socketio.on('connect')
def handle_connect():
    """Handle client connection"""
    try:
        logger.info(f"Client connected: {request.sid}")
        
        # Start monitoring if not already running
        start_monitoring()
        start_bot_status_monitoring()
        
        # Send connection confirmation
        emit('connected', {'message': 'Connected to Profit Monitor'})
        
        # Send initial data
        try:
            positions_data = enhanced_api_service.get_real_time_summary()
            emit('positions_update', {
                'positions': positions_data.get('positions', []),
                'summary': positions_data.get('summary', {}),
                'account': positions_data.get('account', {}),
                'timestamp': datetime.now().isoformat()
            })
        except Exception as e:
            logger.error(f"Error getting initial data: {str(e)}")
            emit('error', {'message': f'Failed to get initial data: {str(e)}'})
        
    except Exception as e:
        logger.error(f"Error in connect handler: {str(e)}")
        try:
            emit('error', {'message': 'Connection error occurred'})
        except Exception as emit_error:
            logger.error(f"Error emitting connection error: {str(emit_error)}")
    
    return True  # Accept connection

@socketio.on('disconnect')
def handle_disconnect():
    """Handle client disconnection"""
    try:
        logger.info(f"Client disconnected: {request.sid}")
    except Exception as e:
        logger.error(f"Error in disconnect handler: {str(e)}")

@socketio.on('connect_error')
def handle_connect_error():
    """Handle connection errors"""
    try:
        logger.error(f"Connection error for client: {request.sid}")
        emit('error', {'message': 'Connection error occurred'})
    except Exception as e:
        logger.error(f"Error in connect_error handler: {str(e)}")
        
@app.errorhandler(404)
def handle_404(e):
    """Handle 404 errors"""
    return {'error': 'Not found'}, 404

@socketio.on_error_default
def default_error_handler(e):
    """Default error handler for SocketIO"""
    logger.error(f"SocketIO error: {str(e)}")
    try:
        emit('error', {'message': 'An error occurred while processing your request'})
    except Exception as emit_error:
        logger.error(f"Error emitting default error: {str(emit_error)}")
    
    # Don't return False to prevent disconnection
    return True

@socketio.on('get_positions')
def handle_get_positions():
    """Handle request for current positions"""
    try:
        positions_data = enhanced_api_service.get_real_time_summary()
        
        emit('positions_update', {
            'positions': positions_data.get('positions', []),
            'summary': positions_data.get('summary', {}),
            'account': positions_data.get('account', {}),
            'timestamp': datetime.now().isoformat()
        })
    except Exception as e:
        emit('error', {'message': f'Failed to get positions: {str(e)}'})

@socketio.on('get_account_status')
def handle_get_account_status():
    """Handle request for account status"""
    try:
        positions_data = enhanced_api_service.get_real_time_summary()
        emit('account_status', positions_data.get('account', {}))
    except Exception as e:
        emit('error', {'message': f'Failed to get account status: {str(e)}'})

@socketio.on('close_profitable')
def handle_close_profitable():
    """Handle request to close all profitable positions with enhanced speed"""
    try:
        emit('operation_started', {'message': 'Closing profitable positions...', 'type': 'profit'})
        
        # Use enhanced API service for faster response
        result = enhanced_api_service.request_position_close_fast('profit')
        
        if result.get('status') == 'error':
            emit('operation_error', {
                'message': f'Failed to close profitable positions: {result.get("error")}',
                'type': 'profit'
            })
        else:
            emit('operation_submitted', {
                'message': result.get('message', 'Operation submitted'),
                'type': 'profit',
                'request_id': result.get('request_id'),
                'estimated_positions': result.get('estimated_positions', 0),
                'timestamp': result.get('timestamp')
            })
            
            # Start enhanced polling for operation status
            start_operation_polling(result.get('request_id'), 'profit')
        
    except Exception as e:
        emit('operation_error', {
            'message': f'Error closing profitable positions: {str(e)}',
            'type': 'profit'
        })

@socketio.on('close_losing')
def handle_close_losing():
    """Handle request to close all losing positions with enhanced speed"""
    try:
        emit('operation_started', {'message': 'Closing losing positions...', 'type': 'loss'})
        
        # Use enhanced API service for faster response
        result = enhanced_api_service.request_position_close_fast('loss')
        
        if result.get('status') == 'error':
            emit('operation_error', {
                'message': f'Failed to close losing positions: {result.get("error")}',
                'type': 'loss'
            })
        else:
            emit('operation_submitted', {
                'message': result.get('message', 'Operation submitted'),
                'type': 'loss',
                'request_id': result.get('request_id'),
                'estimated_positions': result.get('estimated_positions', 0),
                'timestamp': result.get('timestamp')
            })
            
            # Start enhanced polling for operation status
            start_operation_polling(result.get('request_id'), 'loss')
        
    except Exception as e:
        emit('operation_error', {
            'message': f'Error closing losing positions: {str(e)}',
            'type': 'loss'
        })

@socketio.on('close_all')
def handle_close_all():
    """Handle request to close all positions with enhanced speed"""
    try:
        emit('operation_started', {'message': 'Closing all positions...', 'type': 'all'})
        
        # Use enhanced API service for faster response
        result = enhanced_api_service.request_position_close_fast('all')
        
        if result.get('status') == 'error':
            emit('operation_error', {
                'message': f'Failed to close all positions: {result.get("error")}',
                'type': 'all'
            })
        else:
            emit('operation_submitted', {
                'message': result.get('message', 'Operation submitted'),
                'type': 'all',
                'request_id': result.get('request_id'),
                'estimated_positions': result.get('estimated_positions', 0),
                'timestamp': result.get('timestamp')
            })
            
            # Start enhanced polling for operation status
            start_operation_polling(result.get('request_id'), 'all')
        
    except Exception as e:
        emit('operation_error', {
            'message': f'Error closing all positions: {str(e)}',
            'type': 'all'
        })

@socketio.on('close_position')
def handle_close_position(data):
    """Handle request to close a single position with enhanced speed"""
    try:
        ticket = data.get('ticket')
        if not ticket:
            emit('error', {'message': 'Position ticket is required'})
            return
            
        emit('operation_started', {'message': f'Closing position {ticket}...', 'type': 'single'})
        
        # Use enhanced API service for faster response
        result = enhanced_api_service.request_position_close_fast('single', ticket)
        
        if result.get('status') == 'error':
            emit('operation_error', {
                'message': f'Failed to close position {ticket}: {result.get("error")}',
                'type': 'single'
            })
        else:
            emit('operation_submitted', {
                'message': result.get('message', 'Operation submitted'),
                'type': 'single',
                'ticket': ticket,
                'request_id': result.get('request_id'),
                'estimated_positions': result.get('estimated_positions', 1),
                'timestamp': result.get('timestamp')
            })
            
            # Start enhanced polling for operation status
            start_operation_polling(result.get('request_id'), 'single')
        
    except Exception as e:
        emit('operation_error', {
            'message': f'Error closing position: {str(e)}',
            'type': 'single'
        })

def start_operation_polling(request_id, operation_type):
    """Start enhanced polling for operation completion with faster updates"""
    def poll_operation():
        max_polls = 50  # Poll for up to 50 seconds (longer for complex operations)
        poll_count = 0
        
        while poll_count < max_polls:
            try:
                # Use enhanced API service for faster status checks
                status = enhanced_api_service.get_close_operation_status_fast(request_id)
                
                if status.get('status') == 'completed':
                    try:
                        with app.app_context():
                            socketio.emit('operation_completed', {
                                'message': f'Operation completed successfully',
                                'type': operation_type,
                                'closed': status.get('positions_closed', 0),
                                'failed': status.get('positions_failed', 0),
                                'total_profit_closed': status.get('total_profit_closed', 0),
                                'total_loss_closed': status.get('total_loss_closed', 0),
                                'timestamp': datetime.now().isoformat()
                            }, namespace='/')
                            
                            # Send updated positions with enhanced API
                            positions_data = enhanced_api_service.get_real_time_summary()
                            socketio.emit('positions_update', {
                                'positions': positions_data.get('positions', []),
                                'summary': positions_data.get('summary', {}),
                                'account': positions_data.get('account', {}),
                                'timestamp': positions_data.get('last_update', datetime.now().isoformat()),
                                'cached': positions_data.get('cached', False)
                            }, namespace='/')
                    except Exception as emit_error:
                        logger.error(f"Error emitting operation completed: {str(emit_error)}")
                    break
                    
                elif status.get('status') == 'failed':
                    try:
                        with app.app_context():
                            socketio.emit('operation_error', {
                                'message': f'Operation failed: {status.get("error_message", "Unknown error")}',
                                'type': operation_type,
                                'timestamp': datetime.now().isoformat()
                            }, namespace='/')
                    except Exception as emit_error:
                        logger.error(f"Error emitting operation error: {str(emit_error)}")
                    break
                    
                # Progressive polling: start fast, then slow down
                if poll_count < 10:
                    time.sleep(0.5)  # Fast polling for first 5 seconds
                elif poll_count < 20:
                    time.sleep(1)    # Medium polling for next 10 seconds
                else:
                    time.sleep(2)    # Slower polling afterward
                    
                poll_count += 1
                
            except Exception as e:
                logger.error(f"Error polling operation status: {str(e)}")
                break
        
        if poll_count >= max_polls:
            try:
                with app.app_context():
                    socketio.emit('operation_timeout', {
                        'message': 'Operation timed out - check manually',
                        'type': operation_type,
                        'timestamp': datetime.now().isoformat()
                    }, namespace='/')
            except Exception as emit_error:
                logger.error(f"Error emitting operation timeout: {str(emit_error)}")
    
    # Start enhanced polling in background thread
    threading.Thread(target=poll_operation, daemon=True).start()


# -----------------------------
# GSignalX Automation Endpoints
# -----------------------------

@app.route('/api/automation/status', methods=['GET'])
@login_required
def api_automation_status():
    """Return last known runner status (written by automation runner)."""
    import json
    status_file = os.path.join(project_root, 'automation_status.json')
    try:
        if os.path.exists(status_file):
            with open(status_file, 'r', encoding='utf-8') as f:
                return jsonify(json.load(f))
        return jsonify({
            "runner": "GSignalXAutomationRunner",
            "status": "not_running",
            "message": "automation_status.json not found (start the runner)",
        })
    except Exception as e:
        return jsonify({"status": "error", "error": str(e)}), 500


@app.route('/api/automation/rules', methods=['GET'])
@login_required
def api_automation_list_rules():
    """List automation rules for the current user."""
    from src.automation.storage import AutomationRuleStore, get_db_connection
    user_id = session.get('user_id', 'admin')
    try:
        with get_db_connection() as conn:
            store = AutomationRuleStore(conn)
            rules = store.list_rules(user_id)
            return jsonify({
                "user_id": user_id,
                "rules": [
                    {
                        "id": r.id,
                        "name": r.name,
                        "enabled": r.enabled,
                        "symbols": r.symbols,
                        "biases": r.biases,
                        "market_phases": r.phases,
                        "timeframes": r.timeframes,
                        "created_at": r.created_at,
                        "updated_at": r.updated_at,
                    }
                    for r in rules
                ],
            })
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route('/api/automation/rules', methods=['POST'])
@login_required
def api_automation_create_rule():
    """Create an automation rule for the current user."""
    from src.automation.storage import AutomationRuleStore, get_db_connection
    user_id = session.get('user_id', 'admin')
    data = request.get_json(silent=True) or {}

    try:
        name = str(data.get("name") or "Rule")
        enabled = bool(data.get("enabled", True))
        symbols = data.get("symbols") or []
        biases = data.get("biases") or []
        market_phases = data.get("market_phases") or []
        timeframes = data.get("timeframes") or []

        if not isinstance(symbols, list) or not isinstance(biases, list) or not isinstance(market_phases, list) or not isinstance(timeframes, list):
            return jsonify({"error": "symbols/biases/market_phases/timeframes must be lists"}), 400

        with get_db_connection() as conn:
            store = AutomationRuleStore(conn)
            rule_id = store.create_rule(
                user_id=user_id,
                name=name,
                enabled=enabled,
                symbols=symbols,
                biases=biases,
                phases=market_phases,
                timeframes=timeframes,
            )
            return jsonify({"status": "success", "id": rule_id}), 201
    except Exception as e:
        return jsonify({"status": "error", "error": str(e)}), 500


@app.route('/api/automation/rules/<int:rule_id>', methods=['PUT'])
@login_required
def api_automation_update_rule(rule_id: int):
    """Update an automation rule (current user only)."""
    from src.automation.storage import AutomationRuleStore, get_db_connection
    user_id = session.get('user_id', 'admin')
    data = request.get_json(silent=True) or {}

    try:
        with get_db_connection() as conn:
            store = AutomationRuleStore(conn)
            ok = store.update_rule(
                rule_id=rule_id,
                user_id=user_id,
                name=data.get("name"),
                enabled=data.get("enabled"),
                symbols=data.get("symbols"),
                biases=data.get("biases"),
                phases=data.get("market_phases"),
                timeframes=data.get("timeframes"),
            )
            if not ok:
                return jsonify({"status": "error", "error": "Rule not found"}), 404
            return jsonify({"status": "success"})
    except Exception as e:
        return jsonify({"status": "error", "error": str(e)}), 500


@app.route('/api/automation/rules/<int:rule_id>', methods=['DELETE'])
@login_required
def api_automation_delete_rule(rule_id: int):
    """Delete an automation rule (current user only)."""
    from src.automation.storage import AutomationRuleStore, get_db_connection
    user_id = session.get('user_id', 'admin')
    try:
        with get_db_connection() as conn:
            store = AutomationRuleStore(conn)
            ok = store.delete_rule(rule_id, user_id=user_id)
            if not ok:
                return jsonify({"status": "error", "error": "Rule not found"}), 404
            return jsonify({"status": "success"})
    except Exception as e:
        return jsonify({"status": "error", "error": str(e)}), 500


@app.route('/api/automation/active_pairs', methods=['GET'])
@login_required
def api_automation_active_pairs():
    """List currently active pairs (resolved, TTL-based)."""
    from src.automation.storage import AutomationStateStore, get_db_connection
    try:
        with get_db_connection() as conn:
            state = AutomationStateStore(conn)
            return jsonify({"active_pairs": state.list_active_pairs()})
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route('/api/automation/matches', methods=['GET'])
@login_required
def api_automation_matches():
    """List rule matches (for UI transparency)."""
    from src.automation.storage import AutomationStateStore, get_db_connection
    user_id = session.get('user_id', 'admin')
    try:
        with get_db_connection() as conn:
            state = AutomationStateStore(conn)
            return jsonify({"matches": state.list_rule_matches(user_id)})
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route('/api/automation/signals', methods=['GET'])
@login_required
def api_automation_signals():
    """List last stored signal snapshots (written by runner)."""
    from src.automation.storage import AutomationStateStore, get_db_connection
    try:
        limit = int(request.args.get("limit", "200"))
    except Exception:
        limit = 200

    try:
        with get_db_connection() as conn:
            state = AutomationStateStore(conn)
            return jsonify({"signals": state.list_signal_snapshots(limit=max(1, min(1000, limit)))})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@socketio.on('get_profit_history')
def handle_get_profit_history(data):
    """Handle request for profit history"""
    try:
        hours = data.get('hours', 24)
        history = api_service.get_profit_history(hours)
        emit('profit_history', history)
    except Exception as e:
        emit('error', {'message': f'Failed to get profit history: {str(e)}'})

@socketio.on('get_operations_history')
def handle_get_operations_history(data):
    """Handle request for operations history"""
    try:
        limit = data.get('limit', 50)
        operations = api_service.get_operations_history(limit)
        emit('operations_history', operations)
    except Exception as e:
        emit('error', {'message': f'Failed to get operations history: {str(e)}'})

# Trading suspension endpoints
@socketio.on('suspend_trading')
def handle_suspend_trading(data):
    """Handle trading suspension"""
    try:
        suspended_by = data.get('suspended_by', 'WebSocket User')
        reason = data.get('reason', 'Suspended via WebSocket')
        
        result = api_service.set_trading_suspension(True, suspended_by, reason)
        
        if result.get('status') == 'success':
            emit('trading_suspended', {
                'message': result.get('message'),
                'suspended_by': suspended_by,
                'reason': reason
            })
        else:
            emit('error', {'message': f'Failed to suspend trading: {result.get("error")}'})
            
    except Exception as e:
        emit('error', {'message': f'Failed to suspend trading: {str(e)}'})

@socketio.on('resume_trading')
def handle_resume_trading():
    """Handle trading resumption"""
    try:
        result = api_service.set_trading_suspension(False)
        
        if result.get('status') == 'success':
            emit('trading_resumed', {'message': result.get('message')})
        else:
            emit('error', {'message': f'Failed to resume trading: {result.get("error")}'})
            
    except Exception as e:
        emit('error', {'message': f'Failed to resume trading: {str(e)}'})

if __name__ == '__main__':
    try:
        logger.info("Starting Flask-SocketIO Web Interface Server...")
        logger.info(f"Server will be available at:")
        logger.info(f"  - http://localhost:44444")
        logger.info(f"  - http://127.0.0.1:44444")
        
        # Start the server with proper error handling
        socketio.run(
            app, 
            host='0.0.0.0', 
            port=44444, 
            debug=False,  # Disable debug mode to prevent WebSocket issues
            use_reloader=False,  # Disable reloader to prevent threading issues
            log_output=False,  # Reduce logging noise
            allow_unsafe_werkzeug=True  # Allow WebSocket connections
        )
    except KeyboardInterrupt:
        logger.info("Shutting down server...")
        stop_monitoring()
        stop_bot_status_monitoring()
    except Exception as e:
        logger.error(f"Server error: {str(e)}")
        stop_monitoring()
        stop_bot_status_monitoring()
    finally:
        logger.info("Server shutdown complete") 