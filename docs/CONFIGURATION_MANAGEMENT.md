# Configuration Management System

## Overview

The Profit Monitor system now includes a comprehensive configuration management system that allows you to adjust profit monitoring parameters through the web interface. Changes take effect immediately without requiring system restarts.

## Features

### 🎯 Dynamic Configuration Updates
- Real-time parameter adjustments through the web interface
- Immediate propagation to running profit monitor scripts
- No system restart required

### 💾 Persistent Storage
- Configuration changes are saved to `config/runtime_config.json`
- Settings persist across system restarts
- Automatic backup of previous values

### 🔄 Automatic Synchronization
- Running monitors check for configuration changes every 3-5 seconds
- Changes are applied seamlessly without interrupting operations
- Signal-based notification system ensures quick propagation

### 📊 Intuitive UI
- Organized settings grouped by category
- Helpful tooltips explaining each parameter
- Input validation with range constraints
- Reset to defaults option

## Configuration Parameters

### Profit Thresholds

#### Minimum Profit Percent
- **Default**: 0.5%
- **Range**: 0.1% - 10.0%
- **Description**: Minimum profit percentage required before automatically closing a position
- **Tooltip**: Set lower for quicker exits, higher for larger profits

#### Trailing Stop Percent
- **Default**: 0.2%
- **Range**: 0.1% - 5.0%
- **Description**: Trailing stop percentage to protect profits
- **Tooltip**: Position closes if profit falls by this percentage from the peak

### Partial Close Settings

#### Enable Partial Position Closing
- **Default**: Enabled
- **Type**: Boolean
- **Description**: Enable/disable partial position closing feature
- **Tooltip**: When enabled, the system can close a portion of a position to secure profits

#### Partial Close Threshold
- **Default**: 1.0%
- **Range**: 0.5% - 20.0%
- **Description**: Profit percentage threshold to trigger partial closing
- **Tooltip**: Position must reach this profit before partial close is executed

#### Partial Close Percent
- **Default**: 50%
- **Range**: 10% - 90%
- **Description**: Percentage of position to close when threshold is reached
- **Tooltip**: For example, 50% means half the position will be closed

### Monitoring Settings

#### Check Interval
- **Default**: 1800 seconds (30 minutes)
- **Range**: 1 - 3600 seconds
- **Description**: How often the profit monitor checks positions
- **Tooltip**: Lower values = more frequent checks but higher system load

#### Log Level
- **Default**: INFO
- **Options**: DEBUG, INFO, WARNING, ERROR
- **Description**: Logging detail level
- **Tooltip**: Use DEBUG for troubleshooting, ERROR for minimal logging

### Retry & Error Handling

#### Max Retries
- **Default**: 3
- **Range**: 1 - 10
- **Description**: Maximum number of retry attempts for failed operations
- **Tooltip**: Higher values = more persistent but slower failure detection

#### Retry Delay
- **Default**: 1 second
- **Range**: 0.5 - 60 seconds
- **Description**: Delay between retry attempts
- **Tooltip**: Gives the system time to recover from temporary issues

### Additional Options

#### Enable Market Hours Check
- **Default**: Enabled
- **Type**: Boolean
- **Description**: Check if market is open before executing operations
- **Tooltip**: Prevents errors during closed market hours

## How to Use

### Web Interface

1. **Access Settings Page**
   - Log in to the web interface
   - Click on "Settings" in the navigation
   - Navigate to the "Profit Monitor" tab

2. **Adjust Parameters**
   - Modify desired parameters using the input fields
   - Hover over info icons (ℹ️) to see tooltips
   - Use sliders or type values directly

3. **Save Changes**
   - Enter your current password for security verification
   - Click "Save Profit Monitor Settings"
   - Changes take effect immediately

4. **Reset to Defaults**
   - Click "Reset to Defaults" button
   - Confirm the action
   - All parameters return to original values

### API Endpoints

#### Get Current Configuration
```bash
GET /api/config/profit_monitor
```

**Response:**
```json
{
  "status": "success",
  "config": {
    "min_profit_percent": 0.5,
    "trailing_stop_percent": 0.2,
    "check_interval": 1800,
    ...
  },
  "timestamp": "2024-12-11T10:30:00"
}
```

#### Update Configuration
```bash
POST /api/config/profit_monitor
Content-Type: application/json

{
  "min_profit_percent": 1.0,
  "max_retries": 5,
  "log_level": "DEBUG"
}
```

**Response:**
```json
{
  "status": "success",
  "message": "Configuration updated successfully",
  "updated_fields": ["min_profit_percent", "max_retries", "log_level"],
  "timestamp": "2024-12-11T10:31:00"
}
```

#### Reset to Defaults
```bash
POST /api/config/profit_monitor/reset
```

**Response:**
```json
{
  "status": "success",
  "message": "Configuration reset to defaults",
  "config": { ... },
  "timestamp": "2024-12-11T10:32:00"
}
```

## Technical Implementation

### Architecture

```
┌─────────────────┐
│  Web Interface  │
│   (Settings)    │
└────────┬────────┘
         │
         ├─> Configuration Manager
         │   (config_manager.py)
         │
         ├─> Signal File Creation
         │   (config_changed.signal)
         │
         v
┌─────────────────┐
│ Runtime Config  │
│  (JSON File)    │
└─────────────────┘
         │
         v
┌─────────────────┐
│ Profit Monitors │
│ - Standard      │
│ - Enhanced      │
└─────────────────┘
```

### Configuration Manager

The `ConfigurationManager` class handles:
- Reading/writing configuration from JSON
- Thread-safe updates
- Change notifications
- Metadata tracking (who changed what, when)

### Signal-Based Propagation

1. Web interface updates configuration
2. Creates `config_changed.signal` file with timestamp
3. Running monitors check for signal file periodically
4. When detected, monitors reload configuration
5. Signal file is deleted after processing

### Integration Points

#### Profit Monitor (Standard)
- Checks for config changes every 5 seconds
- Reloads configuration mid-operation
- Updates logging level dynamically

#### Profit Monitor (Enhanced)
- Checks for config changes every 3 seconds
- Adjusts update intervals on-the-fly
- Optimized for real-time operations

## Testing

### Run Configuration Tests
```bash
python src/scripts/test_config_updates.py
```

**Tests include:**
- Configuration manager initialization
- Single parameter updates
- Bulk updates
- Configuration persistence
- Signal file creation
- Reset to defaults

### Manual Testing Checklist

1. **Update via Web Interface**
   - [ ] Change a parameter in settings
   - [ ] Verify change is saved
   - [ ] Check running monitor picks up change
   - [ ] Verify behavior matches new setting

2. **Reset to Defaults**
   - [ ] Click reset button
   - [ ] Confirm all values return to defaults
   - [ ] Verify monitors apply default settings

3. **API Updates**
   - [ ] Send POST request to update config
   - [ ] Verify response indicates success
   - [ ] Check monitors apply new settings

4. **Persistence**
   - [ ] Update configuration
   - [ ] Restart profit monitor
   - [ ] Verify settings are retained

## Best Practices

### Parameter Tuning

1. **Start Conservative**
   - Begin with default settings
   - Make small incremental changes
   - Monitor results before further adjustments

2. **Test in Demo Environment**
   - Test parameter changes with demo account first
   - Verify expected behavior
   - Then apply to live trading

3. **Document Changes**
   - Keep notes on what parameters you changed
   - Record the reason for changes
   - Track performance impact

### Security Considerations

1. **Password Protection**
   - All configuration changes require password verification
   - Prevents unauthorized modifications
   - Audit trail maintained in metadata

2. **Input Validation**
   - All parameters have defined ranges
   - Invalid values are rejected
   - Helpful error messages guide corrections

3. **Backup Configuration**
   - Previous values stored in metadata
   - Easy rollback if needed
   - Change history preserved

## Troubleshooting

### Configuration Not Updating

**Problem**: Changes in web interface don't affect running monitors

**Solutions:**
1. Check signal file exists: `config/config_changed.signal`
2. Verify monitors are running (not stopped)
3. Check monitor logs for config reload messages
4. Ensure file permissions allow reading signal file

### Settings Reset After Restart

**Problem**: Configuration reverts to defaults after system restart

**Solutions:**
1. Check `config/runtime_config.json` file exists
2. Verify file permissions (read/write access)
3. Ensure configuration manager initializes properly
4. Check logs for initialization errors

### Invalid Parameter Values

**Problem**: Can't save configuration with desired values

**Solutions:**
1. Verify values are within allowed ranges
2. Check input field tooltips for constraints
3. Use API to see detailed error messages
4. Refer to parameter documentation above

## Support

For issues or questions:
1. Check this documentation
2. Review system logs
3. Run test suite to verify functionality
4. Contact system administrator

## Changelog

### Version 1.0 (2024-12-11)
- Initial release of configuration management system
- Web interface integration
- API endpoints for programmatic access
- Real-time synchronization with monitors
- Comprehensive parameter controls with tooltips
