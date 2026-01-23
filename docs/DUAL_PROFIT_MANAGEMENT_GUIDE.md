# Dual Profit Management System Guide

## Overview

This guide explains how to run **Enhanced Profit Monitor** and **Profit Scouting Bot** together for a comprehensive profit management strategy.

## ✅ Can They Run Together?

**YES!** Both scripts can run simultaneously. They complement each other:

- **Enhanced Profit Monitor**: Handles loss prevention, profit locking, and dollar cost averaging (DCA)
- **Profit Scouting Bot**: Takes profits at specific dollar targets

## 🎯 Strategy Overview

### Enhanced Profit Monitor Role
- **Loss Prevention**: Closes losing positions early using percentage-based thresholds
- **Profit Locking**: Partially closes profitable positions to lock in gains
- **DCA Management**: Uses partial closing for dollar cost averaging strategy
- **Real-time Monitoring**: Fast updates (1-second cache) for responsive management

### Profit Scouting Bot Role
- **Dollar Profit Targets**: Automatically closes positions when dollar targets are met
- **Category-Specific Targets**: Different targets for currency, commodity, and crypto
- **Multi-Level Targets**: Individual position, pair, and total profit targets
- **Autonomous Operation**: Runs independently, checking every 5 seconds

## ⚙️ Recommended Configuration

### Enhanced Profit Monitor Settings

```python
PROFIT_MONITOR_CONFIG = {
    'min_profit_percent': 0.5,           # Early profit/loss detection
    'trailing_stop_percent': 0.2,        # Protect profits while allowing growth
    'check_interval': 60,                 # Check every 60 seconds
    'partial_close_enabled': True,       # Enable DCA
    'partial_close_threshold': 1.0,       # Trigger at 1% profit
    'partial_close_percent': 40,         # Close 40% for DCA
    'enable_market_check': True          # Only act when market is open
}
```

**Why These Settings:**
- Lower thresholds catch issues early
- Partial closing enables DCA before Profit Scouting takes full profit
- Faster checks (60s) for responsive loss prevention

### Profit Scouting Bot Settings

```python
PROFIT_SCOUTING_CONFIG = {
    'profit_targets_mode': 'by_category',  # Use category-specific targets
    
    # Currency (Forex) - Moderate targets
    'target_profit_position_currency': 6.0,   # $6 per position
    'target_profit_pair_currency': 12.0,      # $12 per symbol
    'total_target_profit_currency': 25.0,     # $25 total
    
    # Commodity - Higher targets
    'target_profit_position_commodity': 10.0,
    'target_profit_pair_commodity': 20.0,
    'total_target_profit_commodity': 40.0,
    
    # Crypto - Highest targets
    'target_profit_position_crypto': 15.0,
    'target_profit_pair_crypto': 30.0,
    'total_target_profit_crypto': 60.0,
    
    'check_interval': 5,  # Check every 5 seconds
    'magic_number': 10001
}
```

**Why These Settings:**
- Dollar amounts provide precise profit targets
- Higher than Enhanced Monitor triggers to allow DCA first
- Category-specific for different asset volatilities
- Fast checks (5s) for responsive profit taking

## 🔄 How They Work Together

### Example Scenario:

1. **Position Opens**: EURUSD position with $1000 value
2. **Enhanced Monitor (60s check)**:
   - At 0.5% profit ($5): Monitors, no action yet
   - At 1.0% profit ($10): Triggers partial close (40% = $400), locks $4 profit
   - Position continues with $600 remaining
3. **Profit Scouting Bot (5s check)**:
   - Monitors remaining position
   - When position profit reaches $6: Closes entire position
   - Total profit: $4 (from partial) + $6 (from full) = $10

### Conflict Prevention:

Both scripts can safely run together because:
- **Enhanced Monitor**: Uses percentage thresholds, partial closes, focuses on loss prevention
- **Profit Scouting**: Uses dollar thresholds, full closes, focuses on profit taking
- **Different Triggers**: Enhanced Monitor triggers earlier (percentage-based), Profit Scouting triggers later (dollar-based)
- **MT5 Safety**: MT5 handles concurrent close requests gracefully (one will succeed, other will see position already closed)

## 📊 Configuration Matrix

| Setting | Enhanced Monitor | Profit Scouting | Purpose |
|---------|----------------|-----------------|---------|
| **Trigger Type** | Percentage | Dollar Amount | Different measurement prevents conflicts |
| **Check Interval** | 60 seconds | 5 seconds | Both responsive, different priorities |
| **Close Type** | Partial + Full | Full Only | DCA vs. Profit Taking |
| **Focus** | Loss Prevention | Profit Taking | Complementary roles |
| **Threshold** | Lower (0.5-1%) | Higher ($6-$15) | Staged profit management |

## 🚀 Starting Both Scripts

### Option 1: Enhanced System (Recommended)

```bash
start_enhanced_system.bat
```

This launches:
1. Web Interface
2. **Enhanced Profit Monitor** ← Loss prevention & DCA
3. MarketSession Trading Bot
4. Automation Runner

**Then manually start Profit Scouting Bot:**
```bash
python src/scripts/ProfitScoutingBot.py
```

### Option 2: Scouting System

```bash
start_scouting_system.bat
```

This launches:
1. Web Interface
2. **Profit Scouting Bot** ← Dollar profit targets
3. MarketSession Trading Bot
4. Automation Runner

**Then manually start Enhanced Monitor:**
```bash
python src/scripts/run_enhanced_profit_monitor.py
```

### Option 3: Manual Launch

```bash
# Terminal 1: Enhanced Profit Monitor
python src/scripts/run_enhanced_profit_monitor.py

# Terminal 2: Profit Scouting Bot
python src/scripts/ProfitScoutingBot.py

# Terminal 3: Web Interface (optional)
python src/web/app.py
```

## 📈 Best Practices

### 1. Threshold Alignment

**Ensure Profit Scouting targets are HIGHER than Enhanced Monitor triggers:**

- If Enhanced Monitor partial closes at 1% profit
- Calculate dollar equivalent: 1% of position value
- Set Profit Scouting targets ABOVE this dollar amount
- Example: $1000 position → 1% = $10 → Set Profit Scouting at $12+

### 2. Account Size Considerations

**Small Account (< $1000):**
- Enhanced Monitor: `min_profit_percent: 0.3`, `partial_close_threshold: 0.8`
- Profit Scouting: `target_profit_position: 3.0`, `target_profit_pair: 6.0`

**Medium Account ($1000-$5000):**
- Enhanced Monitor: `min_profit_percent: 0.5`, `partial_close_threshold: 1.0`
- Profit Scouting: `target_profit_position: 6.0`, `target_profit_pair: 12.0`

**Large Account (> $5000):**
- Enhanced Monitor: `min_profit_percent: 0.5`, `partial_close_threshold: 1.0`
- Profit Scouting: `target_profit_position: 10.0+`, `target_profit_pair: 20.0+`

### 3. Market Conditions

**High Volatility Markets:**
- Increase Profit Scouting targets
- Decrease Enhanced Monitor partial close threshold
- More aggressive DCA (higher partial_close_percent)

**Low Volatility Markets:**
- Decrease Profit Scouting targets
- Increase Enhanced Monitor thresholds
- Less aggressive DCA (lower partial_close_percent)

### 4. Monitoring

**Watch for:**
- Both bots trying to close same position (normal, MT5 handles it)
- Enhanced Monitor closing too early (increase thresholds)
- Profit Scouting not triggering (decrease targets or check positions)
- Database conflicts (rare, both use WAL mode)

## ⚠️ Important Notes

### 1. Position Ownership

- Both bots monitor **ALL positions** (no magic number filtering currently)
- This is intentional - they work on all positions
- MT5 handles concurrent close requests safely

### 2. Database Access

- Both bots write to the same database
- Enhanced Monitor uses WAL mode for concurrency
- Profit Scouting uses standard SQLite
- No conflicts expected due to different update frequencies

### 3. Performance

- Enhanced Monitor: 1-second cache updates, 5-second DB updates
- Profit Scouting: 5-second position checks
- Both are optimized for parallel operation

### 4. Configuration Updates

- Both support runtime configuration updates via dashboard
- Changes take effect within 3-5 seconds
- Use dashboard to fine-tune thresholds in real-time

## 🔍 Troubleshooting

### Issue: Both bots closing same position

**Solution:** This is normal. MT5 handles it - one succeeds, other sees position already closed. No action needed.

### Issue: Enhanced Monitor closing before Profit Scouting

**Solution:** Increase Enhanced Monitor thresholds or decrease Profit Scouting targets to allow DCA first.

### Issue: Profit Scouting not triggering

**Solution:** 
- Check if targets are too high for your account size
- Verify positions are actually profitable
- Check logs for errors
- Reduce targets incrementally

### Issue: Too many partial closes

**Solution:** 
- Increase `partial_close_threshold` in Enhanced Monitor
- Decrease `partial_close_percent` to close less each time
- Increase `check_interval` to check less frequently

## 📝 Configuration Examples

### Conservative Strategy (Preserve Capital)

```python
# Enhanced Monitor
'min_profit_percent': 0.3,
'partial_close_threshold': 0.8,
'partial_close_percent': 30,

# Profit Scouting
'target_profit_position_currency': 5.0,
'target_profit_pair_currency': 10.0,
```

### Balanced Strategy (Recommended)

```python
# Enhanced Monitor
'min_profit_percent': 0.5,
'partial_close_threshold': 1.0,
'partial_close_percent': 40,

# Profit Scouting
'target_profit_position_currency': 6.0,
'target_profit_pair_currency': 12.0,
```

### Aggressive Strategy (Maximize Profits)

```python
# Enhanced Monitor
'min_profit_percent': 0.5,
'partial_close_threshold': 1.2,
'partial_close_percent': 50,

# Profit Scouting
'target_profit_position_currency': 8.0,
'target_profit_pair_currency': 15.0,
```

## 🎓 Summary

**Running both scripts together provides:**

✅ **Loss Prevention** (Enhanced Monitor)  
✅ **Profit Locking** (Enhanced Monitor DCA)  
✅ **Dollar Profit Targets** (Profit Scouting)  
✅ **Stable Dollar Cost Averaging** (Enhanced Monitor)  
✅ **Autonomous Operation** (Both bots)  
✅ **Real-time Responsiveness** (Both bots)  

**Key Principle:** Enhanced Monitor handles early-stage management (losses, small profits, DCA), while Profit Scouting handles later-stage profit taking at specific dollar targets.

---

**Last Updated:** January 2026  
**Version:** 1.0
