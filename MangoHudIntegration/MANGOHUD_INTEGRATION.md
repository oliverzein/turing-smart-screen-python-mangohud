# MangoHud FPS Integration Guide

This guide explains how to integrate MangoHud FPS data into your Turing Smart Screen.

## Prerequisites

1. **MangoHud** must be installed with the FPS socket feature
2. **FPS socket enabled** in MangoHud config: `fps_socket=1`
3. **Game launched with MangoHud** (e.g., `mangohud <game>`)

## Installation Steps

### Step 1: Update sensors_custom.py

Open `library/sensors/sensors_custom.py` and make the following changes:

#### 1.1 Add imports (after line 25)

Add these imports after the existing imports:
```python
import socket
import struct
import time
from typing import Optional
```

The imports section should look like:
```python
import math
import platform
import socket
import struct
import time
from abc import ABC, abstractmethod
from typing import List, Optional
```

#### 1.2 MangoHudFPS class

The MangoHudFPS class is already integrated at the end of `sensors_custom.py`, after the `ExampleCustomTextOnlyData` class.

**Key features:**
- **Singleton pattern (per-process)**: One instance per process, persistent connection
- **Non-blocking I/O**: Fast buffer draining, always shows latest FPS
- **Auto-discovery**: No PID configuration needed
- **Integer display**: Clean format (e.g., "120 FPS")

### Step 2: Test the Integration

#### 2.1 Launch a game with MangoHud
```bash
mangohud <your_game>
```

#### 2.2 Verify the socket exists
```bash
ss -x | grep mangohud-fps
```

You should see output like:
```
u_str  ESTAB  0  0  @mangohud-fps-12345  *
```

#### 2.3 Test with Python
```python
from library.sensors.sensors_custom import MangoHudFPS

fps_sensor = MangoHudFPS()
print(f"FPS: {fps_sensor.as_string()}")
print(f"Numeric: {fps_sensor.as_numeric()}")
```

## Usage in Themes

### Basic TEXT Display

Add to your theme's `theme.yaml`:

```yaml
STATS:
  CUSTOM:
    INTERVAL: 1  # Update every 1 second
    MangoHudFPS:
      TEXT:
        SHOW: True
        X: 10
        Y: 10
        FONT: roboto-mono/RobotoMono-Bold.ttf
        FONT_SIZE: 24
        FONT_COLOR: 0, 255, 0
        BACKGROUND_IMAGE: background.png
```

### GRAPH Display (Horizontal Bar)

```yaml
MangoHudFPS:
  GRAPH:
    SHOW: True
    X: 10
    Y: 50
    WIDTH: 200
    HEIGHT: 20
    MIN_VALUE: 0
    MAX_VALUE: 144  # Your monitor's refresh rate
    BAR_COLOR: 0, 255, 0
    BAR_OUTLINE: True
    BACKGROUND_IMAGE: background.png
```

### RADIAL Display (Circular Progress)

```yaml
MangoHudFPS:
  RADIAL:
    SHOW: True
    X: 100
    Y: 100
    RADIUS: 50
    WIDTH: 10
    MIN_VALUE: 0
    MAX_VALUE: 144
    ANGLE_START: 120
    ANGLE_END: 60
    CLOCKWISE: True
    BAR_COLOR: 0, 255, 0
    SHOW_TEXT: True
    SHOW_UNIT: False
    FONT: roboto-mono/RobotoMono-Bold.ttf
    FONT_SIZE: 16
    FONT_COLOR: 255, 255, 255
    BACKGROUND_IMAGE: background.png
```

### LINE_GRAPH Display (Historical Trend)

```yaml
MangoHudFPS:
  LINE_GRAPH:
    SHOW: True
    X: 10
    Y: 100
    WIDTH: 200
    HEIGHT: 80
    MIN_VALUE: 0
    MAX_VALUE: 144
    HISTORY_SIZE: 60  # Last 60 samples
    AUTOSCALE: False
    LINE_COLOR: 0, 255, 0
    LINE_WIDTH: 2
    AXIS: True
    AXIS_COLOR: 100, 100, 100
    BACKGROUND_IMAGE: background.png
```

### Combined Display Example

```yaml
STATS:
  CUSTOM:
    INTERVAL: 1
    MangoHudFPS:
      # Show FPS as text
      TEXT:
        SHOW: True
        X: 10
        Y: 10
        FONT: roboto-mono/RobotoMono-Bold.ttf
        FONT_SIZE: 20
        FONT_COLOR: 0, 255, 0
      
      # Show FPS as horizontal bar
      GRAPH:
        SHOW: True
        X: 10
        Y: 40
        WIDTH: 180
        HEIGHT: 15
        MIN_VALUE: 0
        MAX_VALUE: 144
        BAR_COLOR: 0, 255, 0
        BAR_OUTLINE: True
      
      # Show FPS history as line graph
      LINE_GRAPH:
        SHOW: True
        X: 10
        Y: 70
        WIDTH: 180
        HEIGHT: 60
        MIN_VALUE: 0
        MAX_VALUE: 144
        HISTORY_SIZE: 60
        LINE_COLOR: 0, 255, 0
        LINE_WIDTH: 2
        AXIS: True
```

## How It Works

### Auto-Discovery Process

1. **Initialization**: When Turing screen starts, `MangoHudFPS` class initializes
2. **Scanning**: Every 5 seconds (when not connected), scans `/proc/net/unix` for MangoHud sockets
3. **Connection**: When socket found, extracts PID and connects automatically
4. **Data Reading**: Once connected, reads FPS data every update cycle (INTERVAL)
5. **Reconnection**: If connection lost (game closed), automatically starts scanning again

### Display States

- **"No Game"** - No MangoHud socket found (no game running or fps_socket not enabled)
- **"Connecting"** - Socket found, attempting to connect
- **"120 FPS"** - Connected and receiving FPS data (integer display)

### Data Flow

```
Game with MangoHud (fps_socket=1)
       ↓
Unix Domain Socket (@mangohud-fps-<pid>)
       ↓
Auto-discovery via /proc/net/unix
       ↓
MangoHudFPS class connects
       ↓
Reads 16-byte packets (fps, frametime, frame_count)
       ↓
Updates display every INTERVAL seconds
```

## Troubleshooting

### "No Game" displayed

**Check:**
1. Is the game running with MangoHud? (`mangohud <game>`)
2. Is `fps_socket=1` in MangoHud config?
3. Verify socket exists: `ss -x | grep mangohud-fps`
4. Check MangoHud logs for errors

### FPS not updating

**Check:**
1. Is INTERVAL set in theme.yaml? (should be 1 or less)
2. Is the game actually rendering frames? (not paused/minimized)
3. Check Turing screen logs for connection errors

### Wrong FPS displayed

**Check:**
1. Multiple games running? (will connect to first one found)
2. Old game socket still exists? (restart Turing screen)

### Connection keeps dropping

**Check:**
1. Game stability (crashes will disconnect socket)
2. MangoHud version (ensure FPS socket feature is present)
3. System resources (low memory can cause issues)

## Advanced Configuration

### Adjust Discovery Interval

By default, the class scans for new sockets every 5 seconds when not connected. To change this, modify the class:

```python
self.discovery_interval = 2.0  # Scan every 2 seconds
```

### Change History Size

By default, stores 60 FPS samples for line graph. To change:

```python
self.last_val = [math.nan] * 120  # Store 120 samples (2 minutes at 1/sec)
```

### Custom Display Format

Modify the `as_string()` method to change text format:

```python
def as_string(self) -> str:
    if not self.connected:
        return "No Game  "
    # Custom format: show frametime instead of FPS
    return f"{self.current_frametime:>5.2f} ms"
```

## Performance Impact

- **CPU Usage**: Negligible (<0.1% on modern systems)
- **Memory**: ~1KB for FPS history buffer
- **Network**: None (local Unix socket only)
- **Game Performance**: Zero impact (non-blocking socket reads)
- **Buffer Draining**: Microseconds (non-blocking mode)

## Implementation Details

### Singleton Pattern (Per-Process)

The MangoHudFPS class uses a per-process singleton pattern:
- **One instance per process**: Persistent socket connection
- **No socket leaks**: Proper resource management
- **No reconnection overhead**: Connection maintained across framework calls
- **Independent instances**: Test scripts and main.py have separate instances
- **Automatic reset**: Singleton resets when process changes

### Buffer Draining Strategy

MangoHud broadcasts FPS data every frame (~120 Hz), but we only read once per second:

**Problem**: Socket buffer fills with ~120 packets per second. Reading once per second would give stale data.

**Solution**: Non-blocking buffer draining
1. **Non-blocking socket**: `setblocking(False)` for instant reads
2. **Drain loop**: Reads all available packets in tight loop
3. **Latest packet only**: Discards old data, keeps most recent
4. **BlockingIOError**: Signals buffer is empty (normal operation)
5. **No delays**: Buffer draining completes in microseconds

**Result**: Displayed FPS is always current, not stale data from 1 second ago.

```python
# Simplified buffer draining logic
latest_data = None
while True:
    try:
        data = sock.recv(16)  # Non-blocking
        latest_data = data    # Keep latest
    except BlockingIOError:
        break  # Buffer empty, done
# Use latest_data
```

## Security Notes

- Unix Domain sockets are local only (no network exposure)
- Abstract namespace sockets respect user permissions
- Read-only access to FPS data (cannot control MangoHud)
- No authentication needed (same-user processes only)

## Future Enhancements

Possible additions:
- Display frametime instead of/in addition to FPS
- Show frame count or session duration
- Calculate 1% low / 0.1% low FPS (requires frame-by-frame tracking)
- Multiple game monitoring with game name display
- Configurable color based on FPS thresholds
- Decimal precision option (currently integer only)
- Configurable averaging window (currently uses MangoHud's built-in)

## Technical Notes

### Why Non-Blocking I/O?

Initially, the implementation used a 100ms timeout, but this caused issues:
- Reading once per second with 100ms timeout = 100ms delay per update
- Socket buffer filled with ~120 packets between reads
- First packet read was 1 second old (stale data)

Non-blocking I/O solves this:
- Instant reads (no timeout delay)
- Drain entire buffer in microseconds
- Always get the most recent packet

### Why Singleton Pattern?

The framework creates a new instance on every update cycle:
```python
custom_stat_class = getattr(sensors_custom, str(custom_stat))()
```

Without singleton:
- New socket connection every second
- Socket leaks (old connections not closed immediately)
- Connection overhead and instability

With singleton:
- One persistent connection
- No socket leaks
- Stable, efficient operation

## License

This integration follows the same license as both projects:
- MangoHud: MIT License
- turing-smart-screen-python: GNU GPL v3

## Support

For issues:
- MangoHud FPS socket: https://github.com/flightlessmango/MangoHud
- Turing Smart Screen: https://github.com/mathoudebine/turing-smart-screen-python
