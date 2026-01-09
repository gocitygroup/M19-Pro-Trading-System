# Autonomous Forex Trading System

## Architecture Overview

This system is designed with **complete autonomy** between the web interface and the profit monitoring core. The components operate independently and communicate through a clean API layer and file-based command system.

## System Components

### 1. **Profit Monitor Core** (`profit_monitor.py`)
- **Autonomous Operation**: Runs independently without web interface
- **MT5 Integration**: Direct connection to MetaTrader 5
- **Command Processing**: Processes commands from file system
- **Database Updates**: Updates position and profit data
- **Self-Contained**: Can run as a standalone service

### 2. **Web Interface** (`app.py`)
- **Real-Time Dashboard**: Flask-SocketIO based web interface
- **API Communication**: Uses API service layer only
- **No Direct MT5 Access**: Completely separated from trading logic
- **Live Updates**: Real-time position monitoring via WebSocket

### 3. **API Service Layer** (`api_service.py`)
- **Communication Bridge**: Handles all communication between components
- **Database Interface**: Manages all database operations
- **Command Queue**: Creates command files for profit monitor
- **Status Polling**: Tracks operation completion

## How It Works

### Command Flow
```
Web Interface → API Service → Command File → Profit Monitor → Database → API Service → Web Interface
```

### Data Flow
```
MT5 → Profit Monitor → Database → API Service → Web Interface
```

## Running the System

### Option 1: Both Components Together
```bash
# Terminal 1: Start the profit monitor
python run_profit_monitor.py

# Terminal 2: Start the web interface
python app.py
```

### Option 2: Profit Monitor Only (Autonomous)
```bash
# Run profit monitor independently
python run_profit_monitor.py
```

### Option 3: Web Interface Only (Monitoring)
```bash
# Run web interface for monitoring existing data
python app.py
```

## Communication Protocol

### Command Files
- Location: `./commands/`
- Format: JSON files named `cmd_{id}.json`
- Processing: Profit monitor processes and removes files
- Error Handling: Failed commands moved to `./commands/errors/`

### Command Structure
```json
{
  "id": 123,
  "type": "profit|loss|all|single",
  "ticket": 12345,  // For single position closes
  "timestamp": "2024-01-01T12:00:00",
  "status": "pending"
}
```

### Database Tables
- `position_tracking`: Real-time position data
- `profit_monitoring`: Account status history
- `position_close_operations`: Command execution results

## Benefits of Autonomous Design

### 1. **Independence**
- Profit monitor can run without web interface
- Web interface can display data without affecting trading
- Components can be deployed separately

### 2. **Reliability**
- Web interface crashes don't affect trading
- Profit monitor continues operating independently
- Graceful degradation of services

### 3. **Scalability**
- Multiple web interfaces can connect to same data
- Profit monitor is isolated from web traffic
- Easy to add new interfaces or services

### 4. **Maintenance**
- Update web interface without stopping trading
- Restart components independently
- Clear separation of concerns

## Configuration

### Profit Monitor Config (`config.json`)
```json
{
  "profit_monitor": {
    "check_interval": 30,
    "min_profit_percent": 2.0,
    "partial_close_enabled": true,
    "partial_close_threshold": 5.0,
    "partial_close_percent": 50
  }
}
```

### Web Interface Config
- Uses same configuration file
- No MT5 credentials needed
- Only requires database access

## Monitoring and Logs

### Profit Monitor Logs
- File: `logs/profit_monitor.log`
- Console output available
- Detailed operation tracking

### Web Interface Logs
- Console output
- WebSocket connection status
- API operation results

## Security Considerations

### Separation of Concerns
- Web interface has no MT5 access
- API keys/credentials only in profit monitor
- Command files provide secure communication

### Access Control
- Web interface can't directly execute trades
- All operations go through command queue
- Audit trail in database

## Troubleshooting

### Profit Monitor Not Processing Commands
1. Check `./commands/` directory exists
2. Verify file permissions
3. Check logs for processing errors
4. Look in `./commands/errors/` for failed commands

### Web Interface Not Updating
1. Check database connection
2. Verify profit monitor is running
3. Check WebSocket connection status
4. Review API service logs

### Database Issues
1. Ensure database file exists and is writable
2. Check schema is up to date
3. Verify connection string in config
4. Check disk space and permissions

## Development

### Adding New Commands
1. Update `api_service.py` to create command
2. Update `profit_monitor.py` to process command
3. Add WebSocket handler in `app.py`
4. Update frontend to trigger command

### Adding New Data
1. Update database schema
2. Modify profit monitor to collect data
3. Update API service to expose data
4. Add frontend display components

## Production Deployment

### Recommended Setup
1. Run profit monitor as system service
2. Use process manager (systemd/supervisor)
3. Set up log rotation
4. Monitor system resources
5. Configure database backups

### Service Files
Create systemd service for profit monitor:
```ini
[Unit]
Description=Forex Profit Monitor
After=network.target

[Service]
Type=simple
User=trading
WorkingDirectory=/path/to/trading/system
ExecStart=/usr/bin/python3 run_profit_monitor.py
Restart=always

[Install]
WantedBy=multi-user.target
```

This autonomous architecture ensures reliable, maintainable, and scalable forex trading operations. 