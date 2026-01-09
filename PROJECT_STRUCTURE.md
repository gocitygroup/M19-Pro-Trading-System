# Project Structure

## Organized Autonomous Forex Trading System

This document describes the organized folder structure of the autonomous forex trading system.

## Directory Structure

```
ForexMarketSession/
├── src/                          # Source code
│   ├── __init__.py
│   ├── core/                     # Core trading logic
│   │   ├── __init__.py
│   │   └── profit_monitor.py     # Main profit monitoring logic
│   ├── web/                      # Web interface
│   │   ├── __init__.py
│   │   ├── app.py                # Flask-SocketIO web application
│   │   └── templates/            # HTML templates
│   │       └── index.html        # Main dashboard
│   ├── api/                      # API service layer
│   │   ├── __init__.py
│   │   └── api_service.py        # Communication layer
│   ├── scripts/                  # Executable scripts
│   │   ├── __init__.py
│   │   └── run_profit_monitor.py # Standalone profit monitor runner
│   └── config/                   # Configuration
│       ├── __init__.py
│       ├── config.py             # Configuration loader
│       └── config.json           # Configuration file
├── database/                     # Database files
│   ├── schema.sql               # Database schema
│   ├── setup_db.py              # Database initialization
│   └── trading_sessions.db      # SQLite database
├── commands/                     # Command files for communication
│   └── errors/                  # Failed command files
├── logs/                        # Log files
│   ├── market_sessions.log      # Market session logs
│   └── profit_monitor.log       # Profit monitor logs
├── utils/                       # Utility modules
├── data/                        # Data files
├── launch.py                    # System launcher
├── test_system.py               # Test suite
├── README.md                    # Original documentation
├── README_AUTONOMOUS.md         # Autonomous architecture docs
├── PROJECT_STRUCTURE.md         # This file
├── requirements.txt             # Python dependencies
├── requirements-web.txt         # Web-specific dependencies
├── Dockerfile                   # Docker configuration
├── docker-compose.yml           # Docker Compose configuration
└── .gitignore                   # Git ignore rules
```

## Component Descriptions

### 1. Core Components (`src/core/`)
- **`profit_monitor.py`**: Main profit monitoring logic with MT5 integration
- Handles position tracking, profit calculations, and automated closing
- Processes command files from web interface
- Fully autonomous operation

### 2. Web Interface (`src/web/`)
- **`app.py`**: Flask-SocketIO web application
- **`templates/index.html`**: Real-time dashboard with WebSocket client
- Provides real-time position monitoring and control interface
- No direct MT5 access - uses API service layer

### 3. API Service Layer (`src/api/`)
- **`api_service.py`**: Communication bridge between web and core
- Handles database operations
- Creates command files for profit monitor
- Manages operation status tracking

### 4. Scripts (`src/scripts/`)
- **`run_profit_monitor.py`**: Standalone profit monitor service
- Can run independently from web interface
- Includes proper logging and signal handling

### 5. Configuration (`src/config/`)
- **`config.py`**: Configuration loader and management
- **`config.json`**: Main configuration file
- Centralized configuration for all components

### 6. Database (`database/`)
- **`schema.sql`**: Complete database schema
- **`setup_db.py`**: Database initialization script
- **`trading_sessions.db`**: SQLite database file

## Key Features

### Autonomous Operation
- Profit monitor runs independently
- Web interface communicates via API service
- File-based command system for operations
- Complete separation of concerns

### Communication Flow
```
Web Interface → API Service → Command File → Profit Monitor → Database → API Service → Web Interface
```

### Running the System

#### Option 1: Interactive Launcher
```bash
python launch.py
```

#### Option 2: Direct Component Launch
```bash
# Start profit monitor only
python launch.py monitor

# Start web interface only
python launch.py web

# Start both components
python launch.py both
```

#### Option 3: Manual Launch
```bash
# Terminal 1: Start profit monitor
python src/scripts/run_profit_monitor.py

# Terminal 2: Start web interface
python src/web/app.py
```

### Testing
```bash
# Run comprehensive test suite
python test_system.py

# Check system status
python launch.py status
```

## Benefits of This Structure

### 1. **Modularity**
- Clear separation of concerns
- Easy to maintain and extend
- Independent component testing

### 2. **Scalability**
- Add new interfaces easily
- Multiple web clients can connect
- Horizontal scaling possible

### 3. **Reliability**
- Web interface crashes don't affect trading
- Profit monitor operates independently
- Graceful error handling

### 4. **Development**
- Clear import structure
- Proper Python packaging
- Easy to add new features

### 5. **Deployment**
- Components can be deployed separately
- Docker support included
- Easy to set up as services

## Dependencies

### Core Dependencies
- MetaTrader5
- sqlite3
- pytz
- tzlocal

### Web Dependencies
- Flask
- Flask-SocketIO
- python-socketio
- python-engineio

### Development Dependencies
- Standard Python libraries
- No external testing frameworks needed

## Configuration

All configuration is centralized in `src/config/config.json`:

```json
{
  "mt5": {
    "server": "your-server",
    "login": 12345,
    "password": "your-password"
  },
  "profit_monitor": {
    "check_interval": 30,
    "min_profit_percent": 2.0,
    "partial_close_enabled": true
  }
}
```

## Security

- Web interface has no direct MT5 access
- All trading operations go through command queue
- Complete audit trail in database
- Secure file-based communication

This organized structure provides a clean, maintainable, and scalable foundation for the autonomous forex trading system. 