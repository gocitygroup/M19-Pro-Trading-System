# Quick Start Guide - Profit Monitor Configuration

## 🚀 Getting Started in 3 Minutes

### Prerequisites
- Install dependencies and create a virtual environment (see README quick start).
- Copy `.env.example` to `.env` and set `MT5_SERVER`, `MT5_LOGIN`, `MT5_PASSWORD`.
- Ensure the working directory is the repository root before running commands.

### Step 1: Start the Web Interface

```bash
cd d:\GocityGroup\GSignalX\SignallingSystem\GocityTradingProfitMonitoring\GocityTradingProfitMonitoring
python src\web\app.py
```

Access the interface at: **http://localhost:44444**

### Step 2: Log In and Access Settings

1. Log in with your credentials
2. Click **Settings** in the navigation
3. Navigate to the **Profit Monitor** tab

### Step 3: Adjust Parameters

You'll see 11 configurable parameters organized in 5 groups:

#### 🎯 Profit Thresholds
- **Min Profit %**: When to auto-close positions (default: 0.5%)
- **Trailing Stop %**: Protection from profit drawdown (default: 0.2%)

#### 📊 Partial Close Settings
- **Enable Partial Close**: Toggle feature on/off
- **Threshold**: Profit % to trigger partial close (default: 1.0%)
- **Close %**: How much to close (default: 50%)

#### ⏰ Monitoring Settings
- **Check Interval**: How often to check positions in seconds (default: 1800)
- **Log Level**: Detail level of logging (default: INFO)

#### 🔄 Retry & Error Handling
- **Max Retries**: Failed operation retry attempts (default: 3)
- **Retry Delay**: Wait time between retries in seconds (default: 1)

#### ⚙️ Additional Options
- **Market Hours Check**: Verify market is open (default: Enabled)

### Step 4: Save Changes

1. Enter your **current password** (security requirement)
2. Click **"Save Profit Monitor Settings"**
3. ✅ Changes take effect immediately and persist to `config/runtime_config.json`

## 📋 Common Configuration Scenarios

### Scenario 1: More Aggressive Profit Taking
**Goal**: Close positions faster at lower profit levels

```
Min Profit %: 0.3% (instead of 0.5%)
Partial Close Enabled: Yes
Partial Close Threshold: 0.6%
Partial Close %: 50%
```

### Scenario 2: Conservative, Let Profits Run
**Goal**: Hold positions longer for bigger gains

```
Min Profit %: 2.0% (instead of 0.5%)
Trailing Stop %: 0.5% (instead of 0.2%)
Partial Close Enabled: No
```

### Scenario 3: High-Frequency Monitoring
**Goal**: React faster to market changes

```
Check Interval: 300 seconds (5 minutes instead of 30)
Max Retries: 5
Retry Delay: 0.5 seconds
```

### Scenario 4: Debug Mode
**Goal**: Troubleshoot issues with detailed logs

```
Log Level: DEBUG (instead of INFO)
Enable Market Check: Yes
Max Retries: 5
```

## 🔍 How to Verify Changes Are Working

### Method 1: Check Web Interface
- Save settings and refresh the page
- Verify your changes are still there
- ✅ If they persist, configuration is saved

### Method 2: Check Monitor Logs
Look for this message in the profit monitor logs:
```
Configuration reloaded from runtime config: ['min_profit_percent', 'check_interval', ...]
```

### Method 3: Check Config File
Open `config/runtime_config.json`:
```json
{
  "profit_monitor": {
    "min_profit_percent": 1.5,
    "trailing_stop_percent": 0.2,
    ...
  }
}
```

### Method 4: Use API
```bash
curl http://localhost:44444/api/config/profit_monitor
```

## ⚠️ Important Notes

### When Running Multiple Monitors
If you're running both standard and enhanced monitors:
- ✅ Both will pick up configuration changes
- ✅ Changes apply to all running instances
- ✅ No need to restart either monitor

### Configuration Precedence
1. **Runtime Config** (web interface changes) - Highest priority
2. **Environment Variables** (if set)
3. **Static Config** (defaults in config.py) - Lowest priority

### Password Requirement
**Why?** Security! Configuration changes can significantly impact trading behavior.
- All configuration changes require your password
- This prevents unauthorized modifications
- Protects your trading strategy

## 🧪 Test Your Setup

### Quick Test Procedure

1. **Run Test Suite** (optional but recommended):
```bash
python src\scripts\test_config_updates.py
```

Expected output: `🎉 All tests passed successfully!`

2. **Make a Test Change**:
   - Open Settings → Profit Monitor
   - Change "Check Interval" to 60 seconds
   - Save with your password
   - Check if `config/runtime_config.json` was created

3. **Verify Monitor Detects Change**:
   - Watch profit monitor logs
   - You should see: "Configuration reloaded..."
   - Within 3-5 seconds of saving

## 🆘 Troubleshooting

### Problem: Changes Don't Save
**Solution**: 
- Check if you entered the correct password
- Verify values are within allowed ranges (see tooltips)
- Check browser console for errors

### Problem: Monitor Doesn't Apply Changes
**Solution**:
- Confirm monitor is actually running (not stopped)
- Check `config/config_changed.signal` file is created
- Review monitor logs for errors
- Restart monitor if necessary

### Problem: Settings Reset After Restart
**Solution**:
- Check `config/runtime_config.json` exists and is readable
- Verify file permissions
- Ensure configuration manager initializes (check logs)

### Problem: Can't Access Settings Page
**Solution**:
- Confirm you're logged in
- Try clearing browser cache
- Check if web server is running on port 44444

## 📚 Need More Information?

- **Full Documentation**: See `docs/CONFIGURATION_MANAGEMENT.md`
- **Implementation Details**: See `IMPLEMENTATION_SUMMARY.md`
- **API Reference**: See API Endpoints section in documentation

## 💡 Pro Tips

1. **Start Conservative**: Begin with defaults, adjust gradually
2. **Test in Demo**: Try new settings in demo account first
3. **Document Changes**: Keep notes on what you changed and why
4. **Monitor Results**: Watch how changes affect performance
5. **Use Reset**: If things go wrong, reset to defaults

## ✅ Checklist for First-Time Setup

- [ ] Web interface is running
- [ ] Logged in successfully
- [ ] Navigated to Settings → Profit Monitor tab
- [ ] Reviewed all parameter tooltips
- [ ] Made desired changes
- [ ] Entered password and saved
- [ ] Verified changes in config file
- [ ] Confirmed monitor logs show reload
- [ ] Tested monitoring behavior with new settings

## 🎉 You're All Set!

Your profit monitor is now configured with dynamic settings that can be adjusted anytime through the web interface. No more code editing or restarts required!

### Quick Access
- **Web Interface**: http://localhost:44444
- **Settings Page**: http://localhost:44444/settings
- **Config File**: `config/runtime_config.json`
- **Test Script**: `python src\scripts\test_config_updates.py`

Enjoy hassle-free configuration management! 🚀
