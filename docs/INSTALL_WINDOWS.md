# 🪟 Windows Installation Guide

## 📋 **Prerequisites Check**

Before installing the Forex Profit Monitoring System, ensure you have:

1. **Windows 10 or 11** (64-bit) - Check by pressing `Win + X` → System
2. **MetaTrader 5** installed and working with your broker
3. **Administrator privileges** on your computer
4. **Internet connection** for downloading dependencies

---

## 🔧 **Step 1: Install Python**

1. **Download Python 3.9+** from [python.org](https://www.python.org/downloads/)
2. **Run the installer** and **IMPORTANT**: Check "Add Python to PATH"
3. **Verify installation** by opening Command Prompt and typing:
   ```cmd
   python --version
   ```
   You should see: `Python 3.9.x` or higher

---

## 📂 **Step 2: Download and Extract Application**

1. **Download** the Forex Profit Monitoring System zip file
2. **Extract** to a folder like `C:\ForexProfitMonitor\`
3. **Open Command Prompt** as Administrator
4. **Navigate** to the application folder:
   ```cmd
   cd C:\ForexProfitMonitor
   ```

---

## 📦 **Step 3: Install Dependencies**

Run the following command to install required Python packages:

```cmd
pip install -r requirements.txt
```

**If you see errors:**
- Try: `python -m pip install -r requirements.txt`
- Or: `py -m pip install -r requirements.txt`

---

## ⚙️ **Step 4: Configure MT5 Connection**

1. **Open** `src/config/config.json` in any text editor
2. **Replace** the example values with your MT5 credentials:

```json
{
  "mt5": {
    "server": "YourBrokerServer-Demo",
    "login": 12345678,
    "password": "YourPassword"
  },
  "profit_monitor": {
    "update_interval": 1.0,
    "max_positions": 100
  },
  "db": {
    "path": "database/trading_sessions.db"
  }
}
```

**Finding your MT5 details:**
- **Server**: In MT5, go to `Tools` → `Options` → `Server`
- **Login**: Your account number
- **Password**: Your account password

---

## 🚀 **Step 5: First Run**

1. **Make sure MetaTrader 5 is running** and logged in
2. **Open Command Prompt** in the application folder
3. **Run the application**:
   ```cmd
   python launch.py
   ```

4. **Select Option 2** (Enhanced Profit Monitor) for best performance
5. **In a new browser window**, go to: http://localhost:44444

---

## 🎯 **Step 6: Create Desktop Shortcuts**

### **Option A: Create Batch Files (Recommended)**

Create these `.bat` files in your application folder:

**1. Start_Enhanced_Monitor.bat**
```batch
@echo off
cd /d "%~dp0"
python launch.py enhanced
pause
```

**2. Start_Web_Interface.bat**
```batch
@echo off
cd /d "%~dp0"
python launch.py web
pause
```

**3. Start_Full_System.bat**
```batch
@echo off
cd /d "%~dp0"
python launch.py both
pause
```

### **Option B: Create Desktop Shortcuts**

1. **Right-click** on desktop → New → Shortcut
2. **Enter target**:
   ```
   cmd /c "cd /d C:\ForexProfitMonitor && python launch.py enhanced"
   ```
3. **Name it**: "Forex Profit Monitor"
4. **Set icon**: Right-click → Properties → Change Icon

---

## 🔥 **Windows Firewall Configuration**

If Windows Firewall blocks the application:

1. **Open Windows Defender Firewall** (search in Start menu)
2. **Click** "Allow an app through firewall"
3. **Click** "Change settings" → "Allow another app"
4. **Browse** to your Python installation (usually `C:\Python39\python.exe`)
5. **Check both** Private and Public networks
6. **Click** OK

---

## 🛠️ **Windows-Specific Troubleshooting**

### **Issue: "Python is not recognized"**
**Solution:**
1. Reinstall Python with "Add to PATH" checked
2. Or manually add Python to PATH:
   - Search "Environment Variables" in Start menu
   - Add Python installation folder to PATH

### **Issue: "Access Denied" errors**
**Solution:**
- Run Command Prompt as Administrator
- Check folder permissions
- Move application to a different folder (like Documents)

### **Issue: Port 44444 is already in use**
**Solution:**
1. **Find what's using the port**:
   ```cmd
   netstat -ano | findstr :44444
   ```
2. **Kill the process** or change port in config

### **Issue: MetaTrader 5 not connecting**
**Solution:**
- Ensure MT5 is running and logged in
- Check MT5 allows automated trading (Tools → Options → Expert Advisors)
- Verify credentials in config.json

---

## 📊 **Performance Optimization for Windows**

### **1. Antivirus Exclusions**
Add these folders to your antivirus exclusions:
- Application folder (e.g., `C:\ForexProfitMonitor\`)
- Python installation folder
- MetaTrader 5 folder

### **2. Windows Power Settings**
- Set power plan to "High Performance"
- Disable "USB selective suspend"
- Disable sleep/hibernate during trading hours

### **3. System Resources**
- Close unnecessary programs
- Ensure 4GB+ RAM available
- Use SSD storage for better performance

---

## 🔄 **Auto-Start Configuration**

### **Option A: Windows Task Scheduler**
1. **Open Task Scheduler** (search in Start menu)
2. **Create Basic Task**
3. **Set trigger**: At startup or specific time
4. **Set action**: Start program
5. **Program**: `python`
6. **Arguments**: `launch.py enhanced`
7. **Start in**: Application folder path

### **Option B: Windows Startup Folder**
1. **Press** `Win + R` → type `shell:startup`
2. **Copy** your batch file to this folder
3. **Application starts** with Windows

---

## 🔐 **Security Best Practices**

### **1. Credential Security**
- Use demo accounts for testing
- Keep config.json secure
- Don't share credentials

### **2. Network Security**
- Application only accepts local connections
- Firewall rules restrict external access
- No remote access by default

### **3. Data Backup**
- **Database**: Copy `database/trading_sessions.db` regularly
- **Configuration**: Backup `src/config/config.json`
- **Logs**: Archive `logs/` folder monthly

---

## 🆘 **Windows Support**

### **Common Windows Commands**
```cmd
# Check Python version
python --version

# Install packages
pip install -r requirements.txt

# Check running processes
tasklist | findstr python

# Check port usage
netstat -ano | findstr :44444

# Kill process by PID
taskkill /PID 1234 /F
```

### **Log File Locations**
- **Application Logs**: `logs\profit_monitor.log`
- **Web Interface**: `logs\web_interface.log`
- **Windows Event Viewer**: Search for Python-related errors

---

## 📱 **Mobile Access (Optional)**

To access from mobile devices on same network:

1. **Find your PC's IP address**:
   ```cmd
   ipconfig
   ```
2. **Note the IPv4 address** (e.g., 192.168.1.100)
3. **Access from mobile**: http://192.168.1.100:44444

**Note:** Ensure Windows Firewall allows this connection.

---

## 🔧 **Deployment Checklist**

- [ ] Python 3.9+ installed with PATH
- [ ] Dependencies installed (`pip install -r requirements.txt`)
- [ ] MT5 configured and running
- [ ] Config.json updated with credentials
- [ ] Application tested with `python launch.py`
- [ ] Web interface accessible at http://localhost:44444
- [ ] Batch files created for easy access
- [ ] Desktop shortcuts configured
- [ ] Antivirus exclusions added
- [ ] Firewall rules configured
- [ ] Backup strategy implemented

---

**Support**: If you encounter issues, check the main README.md file for detailed troubleshooting or review the log files for specific error messages.

**Last Updated**: December 2024  
**Windows Version**: 10/11 Compatible 