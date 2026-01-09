# Forex Profit Monitor - Embedding Guide

## Table of Contents
1. [Introduction](#introduction)
2. [Getting Started](#getting-started)
3. [Authentication](#authentication)
4. [Available Views](#available-views)
5. [Integration Examples](#integration-examples)
6. [API Reference](#api-reference)
7. [Troubleshooting](#troubleshooting)
8. [Best Practices](#best-practices)

## Introduction

The Forex Profit Monitor can be embedded into any web application using iframes. This allows you to:
- Display real-time trading metrics
- Show profit/loss charts
- List active positions
- Monitor account status

## Getting Started

### 1. Basic Setup

Add this to your HTML:
```html
<iframe 
    src="http://localhost:44444/embed/minimal?token=your-token"
    width="100%" 
    height="200px" 
    frameborder="0">
</iframe>
```

### 2. Environment Configuration

Create or update your `.env` file:
```env
# Required for embedding
EMBED_TOKEN=your-secure-token-here

# Optional embed settings
EMBED_ALLOWED_ORIGINS=https://your-domain.com,https://another-domain.com
EMBED_RATE_LIMIT=100  # Requests per minute
EMBED_CACHE_DURATION=5  # Seconds
```

## Authentication

### Token-Based Security

1. **Generate a Secure Token**
   ```bash
   # Using Python
   python -c "import secrets; print(secrets.token_hex(32))"
   ```

2. **Configure the Token**
   Add to `.env`:
   ```env
   EMBED_TOKEN=your-generated-token
   ```

3. **Use in Embed URLs**
   ```html
   <iframe src="http://localhost:44444/embed/minimal?token=your-generated-token"></iframe>
   ```

### Origin Validation

Restrict which domains can embed your dashboard:
```env
EMBED_ALLOWED_ORIGINS=https://app1.com,https://app2.com
```

## Available Views

### 1. Minimal View (`/embed/minimal`)
- Essential metrics only
- Lightweight (< 50KB)
- Real-time updates
- Height: 200px recommended

```html
<iframe src="http://localhost:44444/embed/minimal?token=your-token"
        width="100%" height="200px"></iframe>
```

### 2. Chart View (`/embed/chart`)
- Interactive profit/loss chart
- Historical data
- Customizable timeframes
- Height: 400px recommended

```html
<iframe src="http://localhost:44444/embed/chart?token=your-token"
        width="100%" height="400px"></iframe>
```

### 3. Positions Table (`/embed/positions`)
- Active positions list
- Sortable columns
- Real-time updates
- Height: 500px recommended

```html
<iframe src="http://localhost:44444/embed/positions?token=your-token"
        width="100%" height="500px"></iframe>
```

### 4. Full Dashboard (`/embed`)
- Complete functionality
- All features included
- Responsive layout
- Height: 600px recommended

```html
<iframe src="http://localhost:44444/embed?token=your-token"
        width="100%" height="600px"></iframe>
```

## Integration Examples

### Basic Integration
```html
<div class="forex-monitor">
    <iframe src="http://localhost:44444/embed/minimal?token=your-token"
            width="100%" height="200px"></iframe>
</div>
```

### Advanced Integration with Event Handling
```html
<div class="forex-monitor">
    <div id="status-indicator"></div>
    <div id="metrics-display"></div>
    <iframe id="forex-frame" 
            src="http://localhost:44444/embed/minimal?token=your-token"
            width="100%" height="200px"></iframe>
</div>

<script>
// Listen for updates
window.addEventListener('message', (event) => {
    if (event.data.type === 'forex_monitor') {
        handleForexUpdate(event.data);
    }
});

function handleForexUpdate(data) {
    switch (data.event) {
        case 'metrics_update':
            updateMetricsDisplay(data.data);
            break;
        case 'connection_status':
            updateStatusIndicator(data.data.status);
            break;
    }
}

function updateMetricsDisplay(metrics) {
    const display = document.getElementById('metrics-display');
    display.innerHTML = `
        <div>Profit: ${metrics.total_profit}</div>
        <div>Win Rate: ${metrics.win_rate}%</div>
        <div>Positions: ${metrics.open_positions}</div>
    `;
}

function updateStatusIndicator(status) {
    const indicator = document.getElementById('status-indicator');
    indicator.className = `status-${status}`;
}
</script>

<style>
.forex-monitor {
    position: relative;
    background: white;
    border-radius: 8px;
    box-shadow: 0 2px 4px rgba(0,0,0,0.1);
    padding: 10px;
}

#status-indicator {
    position: absolute;
    top: 10px;
    right: 10px;
    width: 10px;
    height: 10px;
    border-radius: 50%;
}

.status-connected { background: #28a745; }
.status-disconnected { background: #dc3545; }
.status-error { background: #ffc107; }
</style>
```

## API Reference

### Events from Embed

1. **Metrics Update**
   ```javascript
   {
     type: 'forex_monitor',
     event: 'metrics_update',
     data: {
       total_profit: number,
       win_rate: number,
       open_positions: number,
       margin_level: number
     }
   }
   ```

2. **Connection Status**
   ```javascript
   {
     type: 'forex_monitor',
     event: 'connection_status',
     data: {
       status: 'connected' | 'disconnected' | 'error'
     }
   }
   ```

### Commands to Embed

1. **Refresh Data**
   ```javascript
   {
     type: 'forex_monitor_command',
     command: 'refresh'
   }
   ```

2. **Connection Control**
   ```javascript
   {
     type: 'forex_monitor_command',
     command: 'connect' | 'disconnect'
   }
   ```

## Troubleshooting

### Common Issues

1. **Embed Not Loading**
   - Verify token is correct
   - Check allowed origins
   - Ensure server is running
   - Check browser console for errors

2. **No Real-time Updates**
   - Verify WebSocket connection
   - Check network connectivity
   - Ensure browser supports WebSocket
   - Verify no firewall blocking

3. **Performance Issues**
   - Reduce number of embeds
   - Use appropriate view type
   - Check network latency
   - Monitor browser resources

## Best Practices

### Security
- Rotate embed tokens regularly
- Use HTTPS in production
- Validate all origins
- Implement rate limiting

### Performance
- Load embeds lazily
- Use minimal view when possible
- Limit concurrent connections
- Cache data appropriately

### User Experience
- Show loading states
- Handle errors gracefully
- Provide fallback content
- Maintain responsive design

### Maintenance
- Monitor usage metrics
- Keep dependencies updated
- Regular security audits
- Backup configuration 