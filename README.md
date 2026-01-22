# 📊 G-SignalX-M19-Pro-Trading-System

> **Professional Trading Management System for MetaTrader 5**

A comprehensive web-based trading application designed to help traders monitor and manage their MetaTrader 5 (MT5) trading positions in real-time. Features instant profit/loss calculations, automated position closing capabilities, detailed performance analytics, and optional G-SignalX real-time signal integration for automated trading.

---

## 📑 **Table of Contents**

- [Overview](#-overview)
- [Key Features](#-key-features)
- [Prerequisites](#-prerequisites)
- [Quick Start Guide](#-quick-start-guide)
- [Installation Methods](#-installation-methods)
- [Running the Application](#-running-the-application)
- [Configuration](#-configuration)
- [System Components](#-system-components)
- [Using the Application](#-using-the-application)
- [GSignalX Automation](#gsignalx-automation)
- [Embedding Features](#-embedding-features)
- [Troubleshooting](#-troubleshooting)
- [System Requirements](#-system-requirements)
- [Support & Maintenance](#-support--maintenance)
- [License & Disclaimer](#-license--disclaimer)

---

## 🎯 **Overview**

The **G-SignalX-M19-Pro-Trading-System** is a professional-grade trading management platform that provides:

- **Real-time monitoring** of all MT5 trading positions
- **Automated position management** with one-click controls
- **Performance analytics** with detailed metrics and charts
- **Web-based dashboard** accessible from any device on your network
- **G-SignalX integration** for automated signal-based trading
- **Multi-session support** for managing multiple trading strategies

---

## ✨ **Key Features**

🔹 **Real-Time Profit/Loss Monitoring** - Live updates every 1-2 seconds  
🔹 **One-Click Position Closing** - Close profitable, losing, or all positions instantly  
🔹 **Performance Dashboard** - Win rate, average profit/loss, margin level monitoring  
🔹 **Web-Based Interface** - Modern, responsive dashboard accessible via web browser  
🔹 **Automated Trading Management** - Background monitoring and position tracking  
🔹 **Historical Analytics** - Profit history charts and operation logs  
🔹 **Multi-Session Support** - Manage multiple trading sessions efficiently  
🔹 **G-SignalX Integration** - Automated signal-based trading with rule engine  
🔹 **Enhanced Performance** - Optimized monitoring with parallel processing (3-4x faster)  

---

## 🔐 **Licensing Requirement**

**⚠️ IMPORTANT: This application requires a valid license to use.**

The **G-SignalX-M19-Pro-Trading-System** is a professional-grade trading application that requires proper licensing for operation. 

### **License Features:**
- **Activation Required** - Application must be licensed before use
- **Professional Support** - Licensed users receive dedicated technical support
- **Regular Updates** - Access to latest features and security patches
- **Compliance** - Ensures proper usage and adherence to terms of service

### **How to Obtain a License:**
1. Contact the application provider or authorized distributor
2. Complete the licensing registration process
3. Receive your unique license key
4. Activate the application using your license credentials

**Without a valid license, the application will not function.** Please ensure you have obtained proper licensing before proceeding with installation.

---

## 📋 **Prerequisites**

Before installing, ensure you have:

- ✅ **Valid License Key** (Required - Contact provider for licensing)
- ✅ **Windows 10/11 (64-bit)**
- ✅ **Python 3.8 or higher** ([Download Python](https://www.python.org/downloads/))
- ✅ **MetaTrader 5 platform** installed and configured
- ✅ **Active trading account** with MT5 broker
- ✅ **Administrator privileges** (for first-time setup)

---

## 🚀 **Quick Start Guide**

### **Method 1: Using Batch Files (Recommended for Windows)**

The easiest way to set up and run the application on Windows. Simply double-click the batch files - no command line knowledge required!

#### **Step 1: Initial Setup (One-Time)**

Double-click **`setup_environment.bat`** to automatically:
- ✅ Check Python installation
- ✅ Create Python virtual environment (`.venv`)
- ✅ Activate virtual environment
- ✅ Upgrade pip to latest version
- ✅ Install all required dependencies from `requirements.txt`
- ✅ Create `logs` directory if it doesn't exist
- ✅ Display setup progress and completion status

**Note:** This step only needs to be run once. If you already have a `.venv` folder, the script will skip creation and proceed with dependency installation.

#### **Step 2: Choose Your Trading System**

After setup is complete, choose which system to run:

**Option A: Enhanced Trading System** ⚡ (Recommended)
- Double-click **`start_enhanced_system.bat`**
- Automatically starts 4 applications in separate terminal windows:
  1. **Web Interface** - Dashboard at http://localhost:44444
  2. **Enhanced Profit Monitor** - Optimized real-time monitoring
  3. **MarketSession Trading Bot** - Automated trading bot
  4. **Automation API Call Signal** - GSignalX automation runner

**Option B: Scouting Trading System** 🔍
- Double-click **`start_scouting_system.bat`**
- Automatically starts 4 applications in separate terminal windows:
  1. **Web Interface** - Dashboard at http://localhost:44444
  2. **Profit Scouting Bot** - Advanced profit scouting
  3. **MarketSession Trading Bot** - Automated trading bot
  4. **Automation API Call Signal** - GSignalX automation runner

**Benefits of Batch Files:**
- 🎯 No manual command-line typing required
- 🚀 Each application runs in its own window (easy to monitor)
- ✅ Automatic virtual environment activation
- 🔧 Built-in error checking and validation
- 📝 Clear status messages and progress indicators

#### **Step 3: Access the Web Interface**

Once the applications are running:
1. Open your web browser
2. Navigate to: **http://localhost:44444**
3. Login with your credentials
4. Start monitoring and managing your trades!

#### **Step 4: Stopping the Applications**

- **Individual Stop:** Close the specific terminal window for that application
- **Stop All:** Close all terminal windows or press `Ctrl+C` in each window
- **Note:** Closing the launcher window (the one that ran the .bat file) will NOT stop the applications - they run independently

---

### **Method 2: Manual Installation**

If you prefer manual setup or are using a different operating system:

#### **Step 1: Create Virtual Environment**
```bash
python -m venv .venv
```

#### **Step 2: Activate Virtual Environment**

**Windows (PowerShell):**
```powershell
.\.venv\Scripts\Activate
```

**Windows (Command Prompt):**
```cmd
.\.venv\Scripts\activate.bat
```

**Linux/Mac:**
```bash
source .venv/bin/activate
```

#### **Step 3: Install Dependencies**
```bash
python -m pip install --upgrade pip
pip install -r requirements.txt
```

#### **Step 4: Create Logs Directory**
```bash
# Windows PowerShell
mkdir -Force logs

# Windows CMD / Linux / Mac
mkdir logs
```

#### **Step 5: Initialize Database**
```bash
python database/setup_db.py
```

---

## 🖥️ **Running the Application**

### **Option 1: Batch Files (Windows - Easiest)**

#### **Enhanced System:**
```bash
start_enhanced_system.bat
```
Launches all components in separate terminal windows automatically.

#### **Scouting System:**
```bash
start_scouting_system.bat
```
Launches all components in separate terminal windows automatically.

### **Option 2: Interactive Menu (Recommended)**
```bash
python launch.py
```
Then select from the menu:
- **Option 1**: Standard Profit Monitor
- **Option 2**: Enhanced Profit Monitor (Recommended - Faster & Optimized)
- **Option 3**: Web Interface Only
- **Option 4**: Both Components (Full System)

### **Option 3: Direct Commands**
```bash
# Enhanced Profit Monitor (Recommended)
python launch.py enhanced

# Web Interface
python launch.py web

# Standard Monitor
python launch.py monitor

# Both Components
python launch.py both
```

### **Option 4: Individual Components**
```bash
# Enhanced Profit Monitor
python src/scripts/run_enhanced_profit_monitor.py

# Web Interface
python src/web/app.py

# MarketSession Trading Bot
python src/scripts/MarketSessionTradingBot.py

# Profit Scouting Bot
python src/scripts/ProfitScoutingBot.py

# Automation Runner
python src/scripts/run_gsignalx_automation_runner.py
```

---

## ⚙️ **Configuration**

### **MT5 Connection Setup**

1. **Copy Environment Template:**
   ```bash
   copy .env.example .env
   ```

2. **Edit `.env` file** and set your broker credentials:
   ```env
   MT5_SERVER=your-broker-server
   MT5_LOGIN=your-account-number
   MT5_PASSWORD=your-password
   ```

3. **Runtime Configuration:**
   - The app automatically writes UI changes to `config/runtime_config.json`
   - You can also edit this file manually if preferred

### **Database Configuration**

The application uses SQLite database located at `database/trading_sessions.db`. No additional setup required.

### **GSignalX API Configuration (Optional)**

For live API mode, add to your `.env` file:
```env
GSIGNALX_SIGNALS_URL=https://your-signals-api-url
GSIGNALX_API_KEY=your-api-key-here
```

### **Embed Token Configuration (Optional)**

For embedding features, add to your `.env` file:
```env
EMBED_TOKEN=your-secure-token-here
```

---

## ⚙️ **Configuration**

### **MT5 Connection Setup**

1. Copy `.env.example` to `.env`.
2. Set your broker credentials using the environment variables already defined in the example file (`MT5_SERVER`, `MT5_LOGIN`, `MT5_PASSWORD`).
3. To persist UI changes, the app writes to `config/runtime_config.json`; you can also edit this file manually if you prefer.

### **Database Configuration**

The application uses SQLite database located at `database/trading_sessions.db`. No additional setup required.

---

## 🌐 **Accessing the Web Interface**

Once the application is running, open your web browser and navigate to:

- **Primary URL**: http://localhost:44444
- **Alternative**: http://127.0.0.1:44444

### **Web Interface Features:**
- **Real-Time Dashboard** - Live profit/loss updates every 1-2 seconds
- **Performance Metrics** - Win rate, margins, averages, and more
- **One-Click Controls** - Close positions instantly with single clicks
- **Position Tables** - Detailed view of all open trades with sorting
- **Activity Logs** - Real-time operation feedback and history
- **Charts** - Historical profit/loss visualization with interactive graphs
- **Responsive Design** - Works on desktop, tablet, and mobile devices

---

## 🔧 **System Components**

### **Core Components**

| Component | Description | Location |
|-----------|-------------|----------|
| **Enhanced Profit Monitor** | Advanced monitoring with parallel processing (3-4x faster) | `src/core/profit_monitor_enhanced.py` |
| **Standard Profit Monitor** | Basic monitoring functionality | `src/core/profit_monitor.py` |
| **Enhanced API Service** | Fast API with smart caching (60-80% load reduction) | `src/api/enhanced_api_service.py` |
| **Web Interface** | Flask-SocketIO web application with real-time updates | `src/web/app.py` |
| **MarketSession Trading Bot** | Automated trading bot for market sessions | `src/scripts/MarketSessionTradingBot.py` |
| **Profit Scouting Bot** | Advanced profit scouting and analysis | `src/scripts/ProfitScoutingBot.py` |
| **Automation Runner** | GSignalX signal automation and rule engine | `src/scripts/run_gsignalx_automation_runner.py` |

### **Configuration & Utilities**

- **Config Manager** (`src/config/config.py`) - Centralized configuration management
- **Database Schema** (`database/schema.sql`) - SQLite database structure
- **Launcher** (`launch.py`) - Main application launcher with interactive menu
- **Batch Files** - Windows automation scripts for easy setup and execution

### **Batch Files (Windows)**

| File | Purpose |
|------|---------|
| `setup_environment.bat` | One-click environment setup (venv, dependencies, directories) |
| `start_enhanced_system.bat` | Launch Enhanced Trading System (4 components) |
| `start_scouting_system.bat` | Launch Scouting Trading System (4 components) |
| `test_batch_files.py` | Interactive test suite to verify setup and configuration |

---

## 📈 **Performance Features**

### **Enhanced Monitoring (Recommended)**

The Enhanced Profit Monitor provides significant performance improvements:

- ⚡ **1-second updates** for real-time responsiveness
- 🚀 **Parallel position closing** (3-4x faster than sequential)
- 💾 **Smart caching** reduces database load by 60-80%
- 🔄 **Thread pool execution** for non-blocking operations
- 📊 **Optimized database queries** with connection pooling
- 🎯 **Asynchronous command processing** for better responsiveness

### **Real-Time Metrics**

The dashboard displays comprehensive trading metrics:

- **Win Rate** - Percentage of profitable trades
- **Average Profit/Loss** - Per position performance analysis
- **Margin Level** - Account safety monitoring
- **Update Speed** - System performance indicator
- **Position Distribution** - Profitable vs losing ratio
- **Total Equity** - Real-time account equity tracking
- **Open Positions** - Count and status of all active trades

---

## 🎛️ **Using the Application**

### **Main Dashboard**
1. **Account Summary Cards** - Balance, equity, total profit/loss
2. **Performance Dashboard** - Win rate, averages, margin level
3. **Action Buttons** - One-click position management
4. **Positions Table** - Detailed view of all open trades
5. **Charts & Logs** - Historical data and activity feed

### **Position Management**
- **Close Profitable** - Instantly close all profitable positions
- **Close Losing** - Close all losing positions to limit losses
- **Close All** - Close all open positions immediately
- **Individual Close** - Close specific positions from the table

### **Real-Time Features**
- **Live Updates** - Positions update every 1-2 seconds
- **Operation Feedback** - Instant visual confirmation
- **Progress Tracking** - Monitor operation completion
- **Error Handling** - Graceful failure recovery

---

## 📊 **Data Management**

### **Database Storage**
- **Position Tracking** - All open positions with real-time updates
- **Profit Monitoring** - Historical profit/loss data
- **Operation History** - Record of all close operations
- **Performance Analytics** - Calculated metrics and trends

### **Backup & Recovery**
- **Database Location**: `database/trading_sessions.db`
- **Backup Recommended**: Copy database file periodically
- **Log Files**: `logs/` directory contains operation logs

---

## 🛠️ **Troubleshooting**

### **Common Issues & Solutions**

#### **1. MT5 Connection Failed**
**Symptoms:** Cannot connect to MetaTrader 5, connection errors

**Solutions:**
- ✅ Verify MT5 is running and logged in
- ✅ Check credentials in `.env` file (MT5_SERVER, MT5_LOGIN, MT5_PASSWORD)
- ✅ Ensure MT5 allows automated trading (Tools → Options → Expert Advisors)
- ✅ Verify broker server name is correct
- ✅ Check firewall settings (allow MT5 and Python)

#### **2. Web Interface Not Loading**
**Symptoms:** Cannot access http://localhost:44444, connection refused

**Solutions:**
- ✅ Check if port 44444 is available (another application may be using it)
- ✅ Verify Python dependencies are installed (`pip install -r requirements.txt`)
- ✅ Try running with administrator privileges
- ✅ Check if web interface process is running
- ✅ Verify virtual environment is activated

#### **3. Positions Not Updating**
**Symptoms:** Dashboard shows stale data, positions not refreshing

**Solutions:**
- ✅ Restart the profit monitor component
- ✅ Check MT5 connection status in the dashboard
- ✅ Verify database permissions (read/write access)
- ✅ Check log files for errors
- ✅ Ensure MT5 is connected and positions are open

#### **4. Slow Performance**
**Symptoms:** Dashboard updates slowly, laggy interface

**Solutions:**
- ✅ Use Enhanced Profit Monitor (recommended for best performance)
- ✅ Close unnecessary browser tabs
- ✅ Check system resources (CPU, RAM usage)
- ✅ Reduce number of open positions if possible
- ✅ Clear browser cache

#### **5. Batch Files Not Working**
**Symptoms:** Batch files fail to run, errors during execution

**Solutions:**
- ✅ Run `test_batch_files.py` to diagnose issues
- ✅ Ensure Python is in system PATH
- ✅ Verify virtual environment exists (run `setup_environment.bat` first)
- ✅ Check file permissions (run as administrator if needed)
- ✅ Verify all required files exist in project directory

#### **6. Virtual Environment Issues**
**Symptoms:** Python modules not found, import errors

**Solutions:**
- ✅ Run `setup_environment.bat` to recreate environment
- ✅ Verify virtual environment is activated
- ✅ Reinstall dependencies: `pip install -r requirements.txt`
- ✅ Check Python version (3.8+ required)

### **Log Files**

Log files are located in the `logs/` directory:

- **Application Logs**: `logs/profit_monitor.log` - Main application activity
- **Web Interface Logs**: `logs/web_interface.log` - Web server activity
- **Error Logs**: `logs/errors.log` - Error messages and exceptions
- **Automation Logs**: Check automation runner terminal output

### **Testing Your Setup**

Run the interactive test suite to verify everything is configured correctly:

```bash
python test_batch_files.py
```

This will check:
- ✅ Python version compatibility
- ✅ Virtual environment setup
- ✅ Batch files existence
- ✅ Application scripts availability
- ✅ Project structure integrity

---

## 🔒 **Security Considerations**

- **Local Network Only** - Web interface binds to localhost
- **No External Access** - Application runs locally on your machine
- **Credential Security** - MT5 credentials stored locally
- **Database Security** - SQLite database with local file permissions

---

## 📋 **System Requirements**

### **Minimum Requirements**
- Windows 10/11 (64-bit)
- Python 3.8+
- 4GB RAM
- 1GB free disk space
- MetaTrader 5 platform

### **Recommended Requirements**
- Windows 11 (64-bit)
- Python 3.9+
- 8GB RAM
- 2GB free disk space
- SSD storage for better performance

---

## 🆘 **Support & Maintenance**

### **Regular Maintenance**
- **Database Cleanup** - Archive old data periodically
- **Log Rotation** - Clean old log files
- **Updates** - Keep Python dependencies updated
- **Backup** - Regular database backups recommended

### **Performance Optimization**
- Use **Enhanced Profit Monitor** for best performance
- Close unnecessary applications to free system resources
- Monitor system performance during heavy trading periods

---

## 📜 **License & Disclaimer**

### **Licensing Terms**

**This is a licensed commercial software application.** Unauthorized use, distribution, or modification is strictly prohibited.

- **Licensed Software** - Valid license required for all operations
- **Proprietary Technology** - Protected intellectual property
- **Commercial Use** - Subject to licensing agreement terms
- **Support & Updates** - Available only to licensed users
- **Compliance** - Users must adhere to all licensing terms and conditions

### **Trading Disclaimer**

This application is provided for professional trading assistance purposes. Trading involves significant risk of loss. The developers and license providers are not responsible for any trading losses incurred while using this software.

**Use at your own risk and always trade responsibly.**

### **Legal Notice**

Unauthorized copying, modification, distribution, or use of this software without a valid license is prohibited and may be subject to legal action. All rights reserved.

---

## 🔧 **Technical Architecture**

- **Backend**: Python 3.8+ with Flask-SocketIO
- **Frontend**: HTML5, CSS3, JavaScript with Bootstrap 5
- **Database**: SQLite with optimized queries
- **Real-time Communication**: WebSocket via Socket.IO
- **Trading Integration**: MetaTrader 5 Python API
- **Deployment**: Standalone Windows application

---

---

## 📚 **Additional Resources**

### **Documentation Files**

- `PROJECT_STRUCTURE.md` - Detailed project architecture
- `DEPLOYMENT_GUIDE.md` - Production deployment instructions
- `QUICK_START_CONFIG.md` - Quick configuration reference
- `docs/INSTALL_WINDOWS.md` - Windows-specific installation guide
- `docs/CONFIGURATION_MANAGEMENT.md` - Configuration management details
- `docs/EMBEDDING_GUIDE.md` - Complete embedding documentation
- `docs/IMPLEMENTATION_SUMMARY.md` - Technical implementation details

### **Testing & Verification**

Run the interactive test suite to verify your setup:

```bash
python test_batch_files.py
```

This comprehensive test checks:
- ✅ Python environment compatibility
- ✅ Virtual environment configuration
- ✅ Batch files availability
- ✅ Application scripts existence
- ✅ Project structure integrity
- ✅ Requirements file presence

---

## 📋 **Quick Reference Guide**

### **Batch Files Quick Reference**

| File | When to Use | What It Does |
|------|-------------|--------------|
| `setup_environment.bat` | First-time setup or after Python update | Creates venv, installs dependencies, sets up directories |
| `start_enhanced_system.bat` | Daily trading with enhanced monitoring | Launches Enhanced Trading System (4 components) |
| `start_scouting_system.bat` | Using profit scouting features | Launches Scouting Trading System (4 components) |
| `test_batch_files.py` | Verify setup or troubleshoot issues | Interactive test suite for system validation |

### **Common Commands Quick Reference**

```bash
# Setup (one-time)
setup_environment.bat

# Run Enhanced System
start_enhanced_system.bat

# Run Scouting System
start_scouting_system.bat

# Test Setup
python test_batch_files.py

# Manual Launch (if batch files unavailable)
python launch.py

# Individual Components
python src/web/app.py
python src/scripts/run_enhanced_profit_monitor.py
python src/scripts/MarketSessionTradingBot.py
python src/scripts/ProfitScoutingBot.py
python src/scripts/run_gsignalx_automation_runner.py
```

### **Important URLs**

- **Web Interface**: http://localhost:44444
- **Alternative URL**: http://127.0.0.1:44444

### **Key File Locations**

| File/Directory | Purpose |
|----------------|---------|
| `.env` | Environment variables (MT5 credentials, API keys) |
| `.venv/` | Python virtual environment |
| `logs/` | Application log files |
| `database/trading_sessions.db` | SQLite database |
| `config/runtime_config.json` | Runtime configuration |

---

## 📝 **Version Information**

**Last Updated**: December 2024  
**Version**: 2.0 Enhanced Edition  
**Python Version**: 3.8+  
**Platform**: Windows 10/11 (64-bit)

---

## 🙏 **Acknowledgments**

This professional trading system is designed for licensed users. For support, updates, and licensing information, please contact your authorized distributor.

---

## 📞 **Getting Help**

### **Before Contacting Support**

1. ✅ Check this README for common issues
2. ✅ Run `python test_batch_files.py` to verify setup
3. ✅ Check log files in `logs/` directory
4. ✅ Review the Troubleshooting section above
5. ✅ Ensure you have a valid license

### **Support Resources**

- **Documentation**: See Additional Resources section
- **Log Files**: Check `logs/` directory for error details
- **Test Suite**: Run `test_batch_files.py` for diagnostics
- **License Provider**: Contact for licensing and support

---

**⚠️ Important Reminder:** This application requires a valid license to operate. Ensure you have proper licensing before use. 

## 🔌 **Embedding Features**

### **Quick Embed Setup**

Add this iframe to your website:
```html
<iframe 
    src="http://localhost:44444/embed/minimal?token=your-token"
    width="100%" 
    height="200px" 
    frameborder="0">
</iframe>
```

### **Available Embed Views**

1. **Full Dashboard** (`/embed`)
   ```html
   <iframe src="http://localhost:44444/embed?token=your-token"></iframe>
   ```
   - Complete trading dashboard
   - Real-time updates
   - All features in compact form

2. **Minimal View** (`/embed/minimal`)
   ```html
   <iframe src="http://localhost:44444/embed/minimal?token=your-token"></iframe>
   ```
   - Essential metrics only
   - Lightweight and fast
   - Perfect for small spaces

3. **Chart View** (`/embed/chart`)
   ```html
   <iframe src="http://localhost:44444/embed/chart?token=your-token"></iframe>
   ```
   - Profit/loss chart
   - Historical performance
   - Interactive zoom

4. **Positions Table** (`/embed/positions`)
   ```html
   <iframe src="http://localhost:44444/embed/positions?token=your-token"></iframe>
   ```
   - Active positions list
   - Real-time updates
   - Sortable columns

### **Embed Authentication**

1. **Setup**
   Add to your `.env` file:
   ```env
   EMBED_TOKEN=your-secure-token-here
   ```

2. **Usage**
   - Add `?token=your-secure-token-here` to embed URLs
   - Keep token secret and rotate regularly
   - Use environment variables for token storage

### **Parent Window Integration**

1. **Listen for Updates**
   ```javascript
   window.addEventListener('message', (event) => {
     if (event.data.type === 'forex_monitor') {
       const { event: eventType, data } = event.data;
       switch (eventType) {
         case 'metrics_update':
           console.log('New metrics:', data);
           break;
         case 'connection_status':
           console.log('Connection:', data);
           break;
       }
     }
   });
   ```

2. **Send Commands**
   ```javascript
   const iframe = document.querySelector('iframe');
   
   // Refresh the embed
   iframe.contentWindow.postMessage({
     type: 'forex_monitor_command',
     command: 'refresh'
   }, '*');
   
   // Disconnect from updates
   iframe.contentWindow.postMessage({
     type: 'forex_monitor_command',
     command: 'disconnect'
   }, '*');
   
   // Reconnect to updates
   iframe.contentWindow.postMessage({
     type: 'forex_monitor_command',
     command: 'connect'
   }, '*');
   ```

### **Events & Data**

1. **Metrics Update Event**
   ```javascript
   {
     type: 'forex_monitor',
     event: 'metrics_update',
     data: {
       total_profit: 1234.56,
       win_rate: 75.5,
       open_positions: 5,
       margin_level: 150.25
     }
   }
   ```

2. **Connection Status Event**
   ```javascript
   {
     type: 'forex_monitor',
     event: 'connection_status',
     data: {
       status: 'connected' // or 'disconnected', 'error'
     }
   }
   ```

### **Responsive Design**

The embeds automatically adapt to their container size:

1. **Default Sizes**
   - Minimal: 200px height
   - Chart: 400px height
   - Positions: 500px height
   - Full: 600px height

2. **Custom Sizing**
   ```html
   <div style="width: 300px; height: 400px;">
     <iframe 
       src="http://localhost:44444/embed/minimal?token=your-token"
       style="width: 100%; height: 100%;"
       frameborder="0">
     </iframe>
   </div>
   ```

### **Example Integration**

```html
<!DOCTYPE html>
<html>
<head>
    <title>Trading Dashboard</title>
    <style>
        .dashboard-container {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
            gap: 20px;
            padding: 20px;
            max-width: 1200px;
            margin: 0 auto;
        }
        
        .embed-wrapper {
            background: white;
            border-radius: 10px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
            overflow: hidden;
        }
    </style>
</head>
<body>
    <div class="dashboard-container">
        <!-- Minimal Metrics -->
        <div class="embed-wrapper">
            <iframe src="http://localhost:44444/embed/minimal?token=your-token"
                    width="100%" height="200px" frameborder="0">
            </iframe>
        </div>
        
        <!-- Performance Chart -->
        <div class="embed-wrapper">
            <iframe src="http://localhost:44444/embed/chart?token=your-token"
                    width="100%" height="400px" frameborder="0">
            </iframe>
        </div>
        
        <!-- Active Positions -->
        <div class="embed-wrapper">
            <iframe src="http://localhost:44444/embed/positions?token=your-token"
                    width="100%" height="500px" frameborder="0">
            </iframe>
        </div>
    </div>

    <script>
        // Handle updates from embeds
        window.addEventListener('message', (event) => {
            if (event.data.type === 'forex_monitor') {
                const { event: eventType, data } = event.data;
                
                switch (eventType) {
                    case 'metrics_update':
                        updateDashboardMetrics(data);
                        break;
                    case 'connection_status':
                        updateConnectionStatus(data.status);
                        break;
                }
            }
        });

        function updateDashboardMetrics(metrics) {
            console.log('New metrics:', metrics);
            // Update your dashboard UI here
        }

        function updateConnectionStatus(status) {
            console.log('Connection status:', status);
            // Update connection indicator
        }
    </script>
</body>
</html>
```

### **Best Practices**

1. **Security**
   - Use secure tokens
   - Implement rate limiting
   - Validate origin domains
   - Use HTTPS in production

2. **Performance**
   - Choose appropriate embed views
   - Limit number of embeds per page
   - Consider loading embeds lazily
   - Monitor resource usage

3. **User Experience**
   - Show loading states
   - Handle connection errors
   - Provide fallback content
   - Maintain responsive design

4. **Maintenance**
   - Monitor embed usage
   - Update tokens regularly
   - Keep dependencies updated
   - Back up configuration 

### **Embed Endpoints (replace host as needed)**
- Full dashboard: `http://localhost:44444/embed`
- Minimal view: `http://localhost:44444/embed/minimal`
- Chart view: `http://localhost:44444/embed/chart`
- Positions view: `http://localhost:44444/embed/positions`

---

## 🤖 **GSignalX Automation (Auto-Trading Runner + Dashboard)**

This project includes an **integrated auto-trading automation layer** that enables signal-based automated trading.

### **What It Does**

- 🔄 Continuously fetches GSignalX signals (API polling or file demo mode)
- 📋 Evaluates user-defined automation rules (bias + market_phase + timeframe alignment)
- 📊 Publishes **active pairs** into the SQLite database for `MarketSessionTradingBot` to consume
- 🎛️ Exposes a web dashboard to create/update/delete rules and view matches/status

### **Components**

The automation system consists of three main components (run as separate processes):

1. **Automation Runner** - Fetches signals and evaluates rules
   ```bash
   python src/scripts/run_gsignalx_automation_runner.py
   ```

2. **Web UI** - Dashboard for managing automation rules
   ```bash
   python src/web/app.py
   ```

3. **Trading Bot** - Executes trades based on active pairs
   ```bash
   python src/scripts/MarketSessionTradingBot.py
   ```

### **Initial Setup**

#### **Step 1: Database Migration (One-Time)**

Run the migration script to add automation tables:

```bash
python database/migrate_add_automation_tables.py
```

#### **Step 2: Configure Environment Variables**

Add to your `.env` file (for live API mode):

```env
GSIGNALX_SIGNALS_URL=https://your-signals-api-url
GSIGNALX_API_KEY=your-api-key-here
```

### **Starting the Automation Runner**

#### **Option A: Demo Mode (Uses `all_signals.json`)**

Perfect for testing without API access:

```bash
python src/scripts/run_gsignalx_automation_runner.py --source file --file-path all_signals.json --poll-seconds 10 --active-ttl-seconds 30
```

**Parameters:**
- `--source file` - Use file-based signal source
- `--file-path` - Path to signals JSON file
- `--poll-seconds` - How often to check for new signals (default: 10)
- `--active-ttl-seconds` - How long signals remain active (default: 30)

#### **Option B: Live API Mode**

Requires environment variables configured in `.env`:

```bash
python src/scripts/run_gsignalx_automation_runner.py --source api --poll-seconds 10 --active-ttl-seconds 30
```

**Parameters:**
- `--source api` - Use live API for signals
- `--poll-seconds` - Polling interval for API (default: 10)
- `--active-ttl-seconds` - Signal active duration (default: 30)

### **Using the Automation Dashboard**

1. **Start the Web Server:**
   ```bash
   python src/web/app.py
   ```

2. **Access the Dashboard:**
   - Navigate to http://localhost:44444
   - Login with your credentials
   - Click **Automation** from the user menu (top-right)

3. **Create Automation Rules:**
   - Define bias (BUY/SELL)
   - Set market phase filters
   - Configure timeframe alignment
   - Save and activate rules

### **How It Integrates with MarketSessionTradingBot**

The `MarketSessionTradingBot` **optionally** reads automation-published active pairs from the database table `automation_active_pairs`.

**Behavior:**
- ✅ If the table is missing or empty, the bot behaves exactly as before (no automation)
- ✅ If the runner is active and a rule matches, the symbol appears as an active BUY/SELL pair
- ✅ The bot trades these pairs during active market sessions
- ✅ Automation pairs are **additive** - they don't replace manual configuration

### **Automation Rule Engine**

Rules are evaluated based on:

1. **Bias** - BUY or SELL signal direction
2. **Market Phase** - Current market condition (trending, ranging, etc.)
3. **Timeframe Alignment** - Multiple timeframe confirmation
4. **Signal Strength** - Confidence level of the signal

When all conditions match, the symbol is published to the active pairs table for trading.
