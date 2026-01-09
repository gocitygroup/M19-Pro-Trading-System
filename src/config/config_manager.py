"""
Configuration Manager for Dynamic Settings Updates
Handles runtime configuration changes with persistence and notifications
"""
import os
import json
import logging
from typing import Dict, Any, Optional, List, Callable
from datetime import datetime
import threading
from pathlib import Path

logger = logging.getLogger(__name__)


class ConfigurationManager:
    """Manages dynamic configuration updates with persistence and change notifications"""
    
    def __init__(self, config_file: Optional[str] = None):
        """
        Initialize configuration manager
        
        Args:
            config_file: Path to JSON config file for persistence
        """
        # Get project root
        self.project_root = Path(__file__).parent.parent.parent
        
        # Default config file location
        if config_file is None:
            config_file = self.project_root / 'config' / 'runtime_config.json'
        
        self.config_file = Path(config_file)
        self.config_file.parent.mkdir(parents=True, exist_ok=True)
        
        # Configuration storage
        self._config = {}
        self._lock = threading.Lock()
        
        # Change notification callbacks
        self._callbacks: List[Callable[[str, Any, Any], None]] = []
        
        # Load existing configuration
        self._load_config()
        
        logger.info(f"Configuration manager initialized with config file: {self.config_file}")
    
    def _load_config(self):
        """Load configuration from file"""
        try:
            if self.config_file.exists():
                with open(self.config_file, 'r') as f:
                    self._config = json.load(f)
                logger.info(f"Loaded configuration from {self.config_file}")
            else:
                logger.info("No existing configuration file, using defaults")
        except Exception as e:
            logger.error(f"Error loading configuration: {str(e)}")
            self._config = {}
    
    def _save_config(self):
        """Save configuration to file"""
        try:
            with self._lock:
                with open(self.config_file, 'w') as f:
                    json.dump(self._config, f, indent=4)
                logger.info(f"Saved configuration to {self.config_file}")
        except Exception as e:
            logger.error(f"Error saving configuration: {str(e)}")
    
    def get(self, section: str, key: Optional[str] = None, default: Any = None) -> Any:
        """
        Get configuration value
        
        Args:
            section: Configuration section (e.g., 'profit_monitor')
            key: Configuration key within section (optional)
            default: Default value if not found
            
        Returns:
            Configuration value or default
        """
        with self._lock:
            if key is None:
                return self._config.get(section, default)
            return self._config.get(section, {}).get(key, default)
    
    def set(self, section: str, key: str, value: Any, notify: bool = True) -> bool:
        """
        Set configuration value
        
        Args:
            section: Configuration section
            key: Configuration key
            value: New value
            notify: Whether to notify callbacks of change
            
        Returns:
            True if successful
        """
        try:
            with self._lock:
                # Get old value
                old_value = self._config.get(section, {}).get(key)
                
                # Create section if it doesn't exist
                if section not in self._config:
                    self._config[section] = {}
                
                # Set new value
                self._config[section][key] = value
                
                # Add timestamp
                if '_metadata' not in self._config[section]:
                    self._config[section]['_metadata'] = {}
                
                self._config[section]['_metadata'][key] = {
                    'updated_at': datetime.now().isoformat(),
                    'old_value': old_value,
                    'new_value': value
                }
            
            # Save to file
            self._save_config()
            
            # Notify callbacks
            if notify:
                self._notify_change(section, key, old_value, value)
            
            logger.info(f"Updated config: {section}.{key} = {value}")
            return True
            
        except Exception as e:
            logger.error(f"Error setting configuration: {str(e)}")
            return False
    
    def set_section(self, section: str, values: Dict[str, Any], notify: bool = True) -> bool:
        """
        Set multiple values in a section
        
        Args:
            section: Configuration section
            values: Dictionary of key-value pairs
            notify: Whether to notify callbacks
            
        Returns:
            True if successful
        """
        try:
            for key, value in values.items():
                if key != '_metadata':  # Skip metadata
                    self.set(section, key, value, notify=False)
            
            # Notify once for all changes
            if notify:
                self._notify_change(section, None, None, values)
            
            return True
        except Exception as e:
            logger.error(f"Error setting section: {str(e)}")
            return False
    
    def register_callback(self, callback: Callable[[str, Any, Any], None]):
        """
        Register a callback for configuration changes
        
        Args:
            callback: Function(section, old_value, new_value)
        """
        self._callbacks.append(callback)
        logger.info(f"Registered configuration change callback: {callback.__name__}")
    
    def _notify_change(self, section: str, key: Optional[str], old_value: Any, new_value: Any):
        """Notify all callbacks of configuration change"""
        for callback in self._callbacks:
            try:
                callback(section, old_value, new_value)
            except Exception as e:
                logger.error(f"Error in config change callback: {str(e)}")
    
    def get_all_config(self) -> Dict[str, Any]:
        """Get all configuration"""
        with self._lock:
            return self._config.copy()
    
    def get_profit_monitor_config(self) -> Dict[str, Any]:
        """Get profit monitor configuration with metadata"""
        return self.get('profit_monitor', default={})
    
    def update_profit_monitor_config(self, updates: Dict[str, Any]) -> bool:
        """
        Update profit monitor configuration
        
        Args:
            updates: Dictionary of configuration updates
            
        Returns:
            True if successful
        """
        return self.set_section('profit_monitor', updates)

    def get_trading_bot_config(self) -> Dict[str, Any]:
        """Get trading bot configuration with metadata"""
        return self.get('trading_bot', default={})

    def update_trading_bot_config(self, updates: Dict[str, Any]) -> bool:
        """
        Update trading bot configuration

        Args:
            updates: Dictionary of configuration updates

        Returns:
            True if successful
        """
        return self.set_section('trading_bot', updates)
    
    def reset_to_defaults(self, section: str, defaults: Dict[str, Any]) -> bool:
        """
        Reset a section to default values
        
        Args:
            section: Configuration section
            defaults: Default values
            
        Returns:
            True if successful
        """
        try:
            with self._lock:
                self._config[section] = defaults.copy()
            
            self._save_config()
            self._notify_change(section, None, None, defaults)
            
            logger.info(f"Reset {section} to defaults")
            return True
        except Exception as e:
            logger.error(f"Error resetting to defaults: {str(e)}")
            return False


# Global configuration manager instance
_config_manager = None


def get_config_manager() -> ConfigurationManager:
    """Get or create global configuration manager instance"""
    global _config_manager
    
    if _config_manager is None:
        _config_manager = ConfigurationManager()
    
    return _config_manager


def initialize_from_static_config(static_config: Dict[str, Any]):
    """
    Initialize runtime config from static configuration
    
    Args:
        static_config: Static configuration dictionary
    """
    manager = get_config_manager()
    
    # Initialize profit monitor config if not exists
    if not manager.get('profit_monitor'):
        profit_config = static_config.get('profit_monitor', {})
        manager.set_section('profit_monitor', profit_config, notify=False)
        logger.info("Initialized profit monitor config from static config")
    
    # Initialize other sections as needed
    if not manager.get('trading_bot'):
        trading_config = static_config.get('trading_bot', {})
        manager.set_section('trading_bot', trading_config, notify=False)
        logger.info("Initialized trading bot config from static config")
