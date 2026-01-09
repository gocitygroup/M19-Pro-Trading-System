# 📊 G-SignalX-M19-Pro-Trading-System

## 🎯 **What This Application Does**

The **G-SignalX-M19-Pro-Trading-System** is a comprehensive web based trading application designed to help traders monitor trading, and manage their MetaTrader 5 (MT5) trading positions in real-time. It provides instant profit/loss calculations, automated position closing capabilities, and detailed performance analytics, Optional G-SignalX real-time signal integration for automated trading.

### **Key Features:**

🔹 **Real-Time Profit/Loss Monitoring** - Live updates every 1-2 seconds  
🔹 **One-Click Position Closing** - Close profitable, losing, or all positions instantly  
🔹 **Performance Dashboard** - Win rate, average profit/loss, margin level monitoring  
🔹 **Web-Based Interface** - Modern, responsive dashboard accessible via web browser  
🔹 **Automated Trading Management** - Background monitoring and position tracking  
🔹 **Historical Analytics** - Profit history charts and operation logs  
🔹 **Multi-Session Support** - Manage multiple trading sessions efficiently  

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

## 🚀 **Quick Start Guide**

### **Prerequisites**
- **Valid License Key** (Required - Contact provider for licensing)
- Windows 10/11 (64-bit)
- Python 3.8 or higher
- MetaTrader 5 platform installed and configured
- Active trading account with MT5 broker

### **Installation Steps**

1. **Download and Extract** the application to your desired folder.
2. **Create a Virtual Environment & Install Dependencies** (PowerShell):
   ```bash
   python -m venv .venv
   .\.venv\Scripts\Activate
   python -m pip install --upgrade pip
   pip install -r requirements.txt
   mkdir -Force logs
   python database/setup_db.py
   ```
3. **Configure MT5 Connection** (see Configuration section below).
4. **Run the Application**:
   ```bash
   python launch.py
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

## 🖥️ **How to Run the Application**

### **Option 1: Interactive Menu (Recommended)**
```bash
python launch.py
```
Then select from the menu:
- **Option 1**: Standard Profit Monitor
- **Option 2**: Enhanced Profit Monitor (Recommended - Faster & Optimized)
- **Option 3**: Web Interface Only
- **Option 4**: Both Components (Full System)

### **Option 2: Direct Commands**
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

### **Option 3: Individual Components**
```bash
# Enhanced Profit Monitor
python src/scripts/run_enhanced_profit_monitor.py
python src/scripts/MarketSessionTradingBot.py

# Web Interface
python src/web/app.py

# Standard Monitor
python src/scripts/run_profit_monitor.py
```

---

## 🌐 **Accessing the Web Interface**

Once running, open your web browser and navigate to:
- **Primary URL**: http://localhost:44444
- **Alternative**: http://127.0.0.1:44444

### **Web Interface Features:**
- **Real-Time Dashboard** - Live profit/loss updates
- **Performance Metrics** - Win rate, margins, averages
- **One-Click Controls** - Close positions instantly
- **Position Tables** - Detailed view of all open trades
- **Activity Logs** - Real-time operation feedback
- **Charts** - Historical profit/loss visualization

---

## 🔧 **System Components**

### **Core Components**
- **Enhanced Profit Monitor** (`src/core/profit_monitor_enhanced.py`) - Advanced monitoring with parallel processing
- **Standard Profit Monitor** (`src/core/profit_monitor.py`) - Basic monitoring functionality
- **Enhanced API Service** (`src/api/enhanced_api_service.py`) - Fast API with caching
- **Web Interface** (`src/web/app.py`) - Flask-SocketIO web application

### **Configuration**
- **Config Manager** (`src/config/config.py`) - Centralized configuration
- **Database Schema** (`database/schema.sql`) - Database structure

### **Utilities**
- **Config Watcher** (`utils/config_watcher.py`) - Dynamic configuration updates
- **Launcher** (`launch.py`) - Main application launcher

---

## 📈 **Performance Features**

### **Enhanced Monitoring (Recommended)**
- **1-second updates** for real-time responsiveness
- **Parallel position closing** (3-4x faster than sequential)
- **Smart caching** reduces database load by 60-80%
- **Thread pool execution** for non-blocking operations
- **Optimized database queries** with connection pooling

### **Real-Time Metrics**
- **Win Rate** - Percentage of profitable trades
- **Average Profit/Loss** - Per position performance
- **Margin Level** - Account safety monitoring
- **Update Speed** - System performance indicator
- **Position Distribution** - Profitable vs losing ratio

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

### **Common Issues**

**1. MT5 Connection Failed**
- Verify MT5 is running and logged in
- Check credentials in `config.json`
- Ensure MT5 allows automated trading

**2. Web Interface Not Loading**
- Check if port 44444 is available
- Verify Python dependencies are installed
- Try running with administrator privileges

**3. Positions Not Updating**
- Restart the profit monitor
- Check MT5 connection status
- Verify database permissions

**4. Slow Performance**
- Use Enhanced Profit Monitor (Option 2)
- Close unnecessary browser tabs
- Check system resources

### **Log Files**
- **Application Logs**: `logs/profit_monitor.log`
- **Web Interface Logs**: `logs/web_interface.log`
- **Error Logs**: `logs/errors.log`

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

**Last Updated**: December 2024  
**Version**: 2.0 Enhanced Edition 

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