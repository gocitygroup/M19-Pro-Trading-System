#!/usr/bin/env python3
"""
Test Script for Configuration Management System
Tests dynamic configuration updates and propagation
"""
import sys
import os
import time
import json

# Add project root to Python path
project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, project_root)

from src.config import get_config_manager, initialize_from_static_config
from src.config.config import load_config, PROFIT_MONITOR_CONFIG

def print_section(title):
    """Print a formatted section header"""
    print("\n" + "=" * 60)
    print(f"  {title}")
    print("=" * 60)

def test_config_manager_initialization():
    """Test configuration manager initialization"""
    print_section("Test 1: Configuration Manager Initialization")
    
    try:
        config = load_config()
        initialize_from_static_config(config)
        
        config_manager = get_config_manager()
        print("✓ Configuration manager initialized successfully")
        
        # Get current config
        profit_config = config_manager.get_profit_monitor_config()
        print(f"✓ Retrieved profit monitor config with {len(profit_config)} parameters")
        
        return True
    except Exception as e:
        print(f"✗ Error: {str(e)}")
        return False

def test_config_update():
    """Test configuration updates"""
    print_section("Test 2: Configuration Updates")
    
    try:
        config_manager = get_config_manager()
        
        # Get original value
        original_value = config_manager.get('profit_monitor', 'min_profit_percent')
        print(f"Original min_profit_percent: {original_value}")
        
        # Update configuration
        new_value = 1.5
        success = config_manager.set('profit_monitor', 'min_profit_percent', new_value)
        
        if success:
            print(f"✓ Updated min_profit_percent to {new_value}")
            
            # Verify update
            updated_value = config_manager.get('profit_monitor', 'min_profit_percent')
            if updated_value == new_value:
                print(f"✓ Configuration update verified: {updated_value}")
            else:
                print(f"✗ Configuration mismatch: expected {new_value}, got {updated_value}")
                return False
            
            # Restore original value
            config_manager.set('profit_monitor', 'min_profit_percent', original_value)
            print(f"✓ Restored original value: {original_value}")
            
            return True
        else:
            print("✗ Failed to update configuration")
            return False
            
    except Exception as e:
        print(f"✗ Error: {str(e)}")
        return False

def test_bulk_update():
    """Test bulk configuration updates"""
    print_section("Test 3: Bulk Configuration Updates")
    
    try:
        config_manager = get_config_manager()
        
        # Save originals
        original_config = config_manager.get_profit_monitor_config().copy()
        
        # Bulk update
        updates = {
            'min_profit_percent': 2.0,
            'trailing_stop_percent': 0.5,
            'max_retries': 5,
            'check_interval': 900
        }
        
        success = config_manager.update_profit_monitor_config(updates)
        
        if success:
            print(f"✓ Bulk update successful for {len(updates)} parameters")
            
            # Verify each update
            for key, value in updates.items():
                current = config_manager.get('profit_monitor', key)
                if current == value:
                    print(f"  ✓ {key}: {value}")
                else:
                    print(f"  ✗ {key}: expected {value}, got {current}")
                    return False
            
            # Restore originals
            config_manager.set_section('profit_monitor', original_config)
            print("✓ Restored original configuration")
            
            return True
        else:
            print("✗ Bulk update failed")
            return False
            
    except Exception as e:
        print(f"✗ Error: {str(e)}")
        return False

def test_persistence():
    """Test configuration persistence"""
    print_section("Test 4: Configuration Persistence")
    
    try:
        config_manager = get_config_manager()
        
        # Update a value
        test_value = 3.14
        config_manager.set('profit_monitor', 'min_profit_percent', test_value)
        print(f"✓ Set test value: {test_value}")
        
        # Check if config file exists
        config_file = config_manager.config_file
        if os.path.exists(config_file):
            print(f"✓ Configuration file exists: {config_file}")
            
            # Read the file
            with open(config_file, 'r') as f:
                saved_config = json.load(f)
            
            if 'profit_monitor' in saved_config:
                print("✓ Profit monitor section exists in saved config")
                
                if saved_config['profit_monitor'].get('min_profit_percent') == test_value:
                    print(f"✓ Test value persisted correctly: {test_value}")
                    return True
                else:
                    print(f"✗ Persisted value mismatch")
                    return False
            else:
                print("✗ Profit monitor section not in saved config")
                return False
        else:
            print(f"✗ Configuration file not found: {config_file}")
            return False
            
    except Exception as e:
        print(f"✗ Error: {str(e)}")
        return False

def test_signal_file_creation():
    """Test configuration change signal file creation"""
    print_section("Test 5: Configuration Change Signaling")
    
    try:
        project_root = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
        signal_file = os.path.join(project_root, 'config', 'config_changed.signal')
        
        # Remove signal file if exists
        if os.path.exists(signal_file):
            os.remove(signal_file)
            print("✓ Cleaned up existing signal file")
        
        # Simulate config change notification
        with open(signal_file, 'w') as f:
            f.write(time.strftime('%Y-%m-%d %H:%M:%S'))
        
        if os.path.exists(signal_file):
            print(f"✓ Signal file created: {signal_file}")
            
            # Check modification time
            mtime = os.path.getmtime(signal_file)
            if time.time() - mtime < 5:  # Within last 5 seconds
                print("✓ Signal file timestamp is recent")
                return True
            else:
                print("✗ Signal file timestamp is not recent")
                return False
        else:
            print("✗ Signal file not created")
            return False
            
    except Exception as e:
        print(f"✗ Error: {str(e)}")
        return False

def test_reset_to_defaults():
    """Test resetting configuration to defaults"""
    print_section("Test 6: Reset to Defaults")
    
    try:
        config_manager = get_config_manager()
        
        # Make some changes
        config_manager.set('profit_monitor', 'min_profit_percent', 9.99)
        config_manager.set('profit_monitor', 'max_retries', 10)
        print("✓ Made test modifications")
        
        # Reset to defaults
        success = config_manager.reset_to_defaults('profit_monitor', PROFIT_MONITOR_CONFIG)
        
        if success:
            print("✓ Reset to defaults successful")
            
            # Verify defaults
            current_config = config_manager.get_profit_monitor_config()
            mismatches = []
            
            for key, default_value in PROFIT_MONITOR_CONFIG.items():
                current_value = current_config.get(key)
                if current_value != default_value:
                    mismatches.append(f"{key}: {current_value} != {default_value}")
            
            if not mismatches:
                print("✓ All values match defaults")
                return True
            else:
                print("✗ Some values don't match defaults:")
                for mismatch in mismatches:
                    print(f"  {mismatch}")
                return False
        else:
            print("✗ Reset to defaults failed")
            return False
            
    except Exception as e:
        print(f"✗ Error: {str(e)}")
        return False

def display_current_config():
    """Display current configuration"""
    print_section("Current Profit Monitor Configuration")
    
    try:
        config_manager = get_config_manager()
        profit_config = config_manager.get_profit_monitor_config()
        
        print("\nConfiguration Parameters:")
        print("-" * 60)
        
        # Group parameters
        groups = {
            'Profit Thresholds': ['min_profit_percent', 'trailing_stop_percent'],
            'Partial Close': ['partial_close_enabled', 'partial_close_threshold', 'partial_close_percent'],
            'Monitoring': ['check_interval', 'log_level'],
            'Retry & Error Handling': ['max_retries', 'retry_delay'],
            'Additional Options': ['enable_market_check']
        }
        
        for group_name, params in groups.items():
            print(f"\n{group_name}:")
            for param in params:
                value = profit_config.get(param, 'N/A')
                print(f"  {param:30s}: {value}")
        
        # Display metadata if exists
        if '_metadata' in profit_config:
            print("\nRecent Changes:")
            print("-" * 60)
            for key, meta in profit_config['_metadata'].items():
                if isinstance(meta, dict):
                    print(f"  {key}:")
                    print(f"    Updated: {meta.get('updated_at', 'N/A')}")
                    print(f"    Old: {meta.get('old_value', 'N/A')} → New: {meta.get('new_value', 'N/A')}")
        
    except Exception as e:
        print(f"Error displaying config: {str(e)}")

def main():
    """Run all tests"""
    print("\n" + "=" * 60)
    print("  PROFIT MONITOR CONFIGURATION SYSTEM TEST SUITE")
    print("=" * 60)
    print("\nThis script tests the dynamic configuration management system")
    print("for the profit monitor.\n")
    
    tests = [
        ("Initialization", test_config_manager_initialization),
        ("Single Update", test_config_update),
        ("Bulk Update", test_bulk_update),
        ("Persistence", test_persistence),
        ("Signaling", test_signal_file_creation),
        ("Reset Defaults", test_reset_to_defaults)
    ]
    
    results = []
    
    for test_name, test_func in tests:
        try:
            result = test_func()
            results.append((test_name, result))
            time.sleep(0.5)  # Brief pause between tests
        except Exception as e:
            print(f"\n✗ Test '{test_name}' crashed: {str(e)}")
            results.append((test_name, False))
    
    # Display current configuration
    display_current_config()
    
    # Summary
    print_section("Test Summary")
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    print(f"\nTests Passed: {passed}/{total}")
    print("\nDetailed Results:")
    
    for test_name, result in results:
        status = "✓ PASS" if result else "✗ FAIL"
        print(f"  {status}: {test_name}")
    
    if passed == total:
        print("\n🎉 All tests passed successfully!")
        return 0
    else:
        print(f"\n⚠️  {total - passed} test(s) failed")
        return 1

if __name__ == "__main__":
    sys.exit(main())
