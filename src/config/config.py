"""
Configuration file for the Forex Market Session Trading Bot
"""
import os
from typing import Dict, Any, List, Tuple
import pytz
from datetime import datetime, time, timedelta

# Database Configuration
DB_CONFIG = {
    'path': 'database/trading_sessions.db'
}

# Trading Sessions Configuration (All times in UTC)
TRADING_SESSIONS = [
    {
        'name': 'Tokyo & Sydney',
        'start_time': '21:00',
        'end_time': '08:00',
        'volatility_factor': 1.2
    },
    {
        'name': 'Tokyo-London Overlap',
        'start_time': '08:00',
        'end_time': '09:00',
        'volatility_factor': 1.5  # Higher volatility during overlap
    },
    {
        'name': 'London',
        'start_time': '08:00',
        'end_time': '17:00',
        'volatility_factor': 1.3
    },
    {
        'name': 'London-NY Overlap',
        'start_time': '13:00',
        'end_time': '17:00',
        'volatility_factor': 1.6  # Highest volatility during major overlap
    },
    {
        'name': 'New York',
        'start_time': '13:00',
        'end_time': '21:00',
        'volatility_factor': 1.3
    }
]

# Time Zone Configuration
TIMEZONE_CONFIG = {
    'local_timezone': os.getenv('LOCAL_TIMEZONE', 'UTC'),  # Set your local timezone
    'trading_timezone': 'UTC',  # MetaTrader uses UTC
    'session_display_format': '%H:%M %Z',
    'supported_timezones': {
        'Italy': 'Europe/Rome',
        'Nigeria': 'Africa/Lagos',
        'UK': 'Europe/London',
        'US/NY': 'America/New_York',
        'Japan': 'Asia/Tokyo',
        'Australia/Sydney': 'Australia/Sydney'
    }
}

# Market Session Trading Bot Parameters
TRADING_BOT_CONFIG = {
    'max_positions': 4,
    'volume': 0.05,
    'scalp_multiplier': 0.5,
    'base_entry_pips': 1,
    'min_spread_multiplier': 1.0,
    'order_expiry_minutes': 30,
    'session_check_interval': 2  # seconds between session checks
}

# Profit Monitor Parameters
PROFIT_MONITOR_CONFIG = {
    'min_profit_percent': 0.5,
    'trailing_stop_percent': 0.2,
    'check_interval': 1800,
    'partial_close_enabled': True,
    'partial_close_threshold': 1.0,
    'partial_close_percent': 50,
    'max_retries': 3,
    'retry_delay': 1,
    'enable_market_check': True,
    'log_level': 'INFO'
}

# Profit Scouting Bot Parameters
PROFIT_SCOUTING_CONFIG = {
    'target_profit_pair': 10.0,
    'target_profit_position': 5.0,
    'total_target_profit': 20.0,
    'order_deviation': 20,
    'magic_number': 10001,
    'check_interval': 5,
    'max_retries': 3,
    'retry_delay': 1
}

# MT5 Configuration
MT5_CONFIG = {
    'server': os.getenv('MT5_SERVER', ''),
    'login': int(os.getenv('MT5_LOGIN', 0)),
    'password': os.getenv('MT5_PASSWORD', '')
}

# Logging Configuration
LOGGING_CONFIG = {
    'format': '%(asctime)s - %(levelname)s - %(message)s',
    'market_sessions_log': 'logs/market_sessions.log',
    'profit_monitor_log': 'logs/profit_monitor.log'
}

def get_session_times(local_tz: str) -> List[Dict]:
    """Convert session times from UTC to local timezone"""
    try:
        local_timezone = pytz.timezone(local_tz)
        utc = pytz.UTC
        today = datetime.now(utc).date()
        
        adjusted_sessions = []
        for session in TRADING_SESSIONS:
            # Convert session times to datetime
            start_time = datetime.strptime(session['start_time'], '%H:%M').time()
            end_time = datetime.strptime(session['end_time'], '%H:%M').time()
            
            # Create full datetime objects in UTC
            start_dt = datetime.combine(today, start_time).replace(tzinfo=utc)
            end_dt = datetime.combine(today, end_time).replace(tzinfo=utc)
            
            # Handle sessions that cross midnight
            if end_time < start_time:
                if datetime.now(utc).time() < end_time:
                    # We're in yesterday's session
                    start_dt = start_dt - timedelta(days=1)
                else:
                    # We're in today's session
                    end_dt = end_dt + timedelta(days=1)
            
            # Convert to local timezone
            local_start = start_dt.astimezone(local_timezone)
            local_end = end_dt.astimezone(local_timezone)
            
            adjusted_sessions.append({
                'name': session['name'],
                'start_time': local_start.strftime('%H:%M'),
                'end_time': local_end.strftime('%H:%M'),
                'volatility_factor': session['volatility_factor'],
                'utc_start': session['start_time'],
                'utc_end': session['end_time']
            })
            
        return adjusted_sessions
    except Exception as e:
        print(f"Error converting session times: {str(e)}")
        return TRADING_SESSIONS

def detect_timezone() -> str:
    """Detect the system timezone and match it to supported timezones"""
    try:
        # For Windows, use tzlocal to get the local timezone
        from tzlocal import get_localzone
        system_timezone = str(get_localzone())
        
        # Check if system timezone is in supported timezones
        for zone_name, zone_value in TIMEZONE_CONFIG['supported_timezones'].items():
            if zone_value == system_timezone:
                return zone_value
        
        # If not found, find the closest matching timezone
        system_tz = pytz.timezone(system_timezone)
        utc_offset = datetime.now(system_tz).utcoffset()
        
        closest_timezone = None
        min_difference = float('inf')
        
        for zone_value in TIMEZONE_CONFIG['supported_timezones'].values():
            try:
                tz = pytz.timezone(zone_value)
                offset_diff = abs((datetime.now(tz).utcoffset() - utc_offset).total_seconds())
                
                if offset_diff < min_difference:
                    min_difference = offset_diff
                    closest_timezone = zone_value
            except Exception:
                continue
        
        return closest_timezone or 'UTC'
        
    except Exception as e:
        print(f"Error detecting timezone: {str(e)}")
        return 'UTC'

def load_config() -> Dict[str, Any]:
    """Load configuration from environment variables if available"""
    config = {
        'db': DB_CONFIG,
        'timezone': TIMEZONE_CONFIG,
        'trading_bot': TRADING_BOT_CONFIG,
        'profit_monitor': PROFIT_MONITOR_CONFIG.copy(),  # Copy to avoid mutation
        'profit_scouting': PROFIT_SCOUTING_CONFIG.copy(),
        'mt5': MT5_CONFIG,
        'logging': LOGGING_CONFIG,
        'sessions': TRADING_SESSIONS
    }
    
    # Detect and set timezone
    detected_tz = os.getenv('LOCAL_TIMEZONE', detect_timezone())
    config['timezone']['local_timezone'] = detected_tz
    config['timezone']['local_timezone_obj'] = pytz.timezone(detected_tz)
    
    # Get timezone-adjusted sessions
    config['sessions'] = get_session_times(detected_tz)
    
    # Load from environment variables if they exist
    for section in ['trading_bot', 'profit_monitor', 'profit_scouting']:
        for key in config[section]:
            env_key = f'{section.upper()}_{key.upper()}'
            if os.getenv(env_key):
                config[section][key] = type(config[section][key])(os.getenv(env_key))
    
    # Check for runtime configuration overrides
    try:
        from src.config.config_manager import get_config_manager
        config_manager = get_config_manager()
        runtime_profit_config = config_manager.get_profit_monitor_config()
        runtime_trading_config = config_manager.get_trading_bot_config()
        runtime_profit_scouting_config = config_manager.get_profit_scouting_config()
        
        # Override with runtime config if available
        if runtime_profit_config and '_metadata' not in runtime_profit_config:
            # Only override if runtime config exists
            if runtime_profit_config:
                config['profit_monitor'].update(runtime_profit_config)
        
        if runtime_trading_config and '_metadata' not in runtime_trading_config:
            if runtime_trading_config:
                config['trading_bot'].update(runtime_trading_config)
        
        if runtime_profit_scouting_config and '_metadata' not in runtime_profit_scouting_config:
            if runtime_profit_scouting_config:
                config['profit_scouting'].update(runtime_profit_scouting_config)
    except Exception:
        # Config manager not available yet, use static config
        pass
    
    return config

# Example usage of environment variables:
"""
To override default settings, set environment variables like:
export LOCAL_TIMEZONE=Europe/Rome  # For Italy
export LOCAL_TIMEZONE=Africa/Lagos  # For Nigeria
export TRADING_BOT_MAX_POSITIONS=5
export TRADING_BOT_VOLUME=0.2
export PROFIT_MONITOR_MIN_PROFIT_PERCENT=1.0
export MT5_SERVER=your_server
export MT5_LOGIN=your_login
export MT5_PASSWORD=your_password
""" 