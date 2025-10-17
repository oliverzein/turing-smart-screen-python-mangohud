# 1% Low FPS Feature

This document describes the 1% low and 0.1% low FPS tracking feature added to the MangoHud integration.

## Overview

**1% low FPS** and **0.1% low FPS** are critical metrics for gaming performance that show the worst frame drops, providing a better indicator of smoothness than average FPS alone.

- **1% low**: Average FPS of the worst 1% of frames
- **0.1% low**: Average FPS of the worst 0.1% of frames

## Implementation

### Data Collection

The implementation tracks frame times using frame count deltas from MangoHud:

```python
frames_rendered = frame_count - self.last_frame_count
time_elapsed = current_time - self.last_sample_time
avg_frametime_ms = (time_elapsed / frames_rendered) * 1000.0
```

For each update cycle (~1 second):
1. Calculate how many frames were rendered
2. Calculate average frametime for those frames
3. Add one sample per frame to the buffer (approximation)
4. Maintain a rolling window of last 1000 frame samples

### Calculation Method

```python
# Sort frame times (worst to best)
sorted_frametimes = sorted(self.frametime_samples, reverse=True)

# Calculate 1% low (worst 1% of frames)
one_percent_count = max(1, len(sorted_frametimes) // 100)
worst_1_percent = sorted_frametimes[:one_percent_count]
avg_1_percent_frametime = sum(worst_1_percent) / len(worst_1_percent)
one_percent_low_fps = 1000.0 / avg_1_percent_frametime
```

### Rolling Window

- **Buffer size**: 1000 frame samples
- **Time window**: Dynamic based on FPS
  - 30 FPS: ~33 seconds
  - 60 FPS: ~16 seconds
  - 120 FPS: ~8 seconds
  - 240 FPS: ~4 seconds

This provides a balance between:
- Statistical significance (enough samples)
- Recent performance (not ancient history)
- Memory efficiency (~8KB for buffer)

## Custom Data Classes

### MangoHud1PercentLow

Displays the 1% low FPS metric.

**Requirements:**
- Minimum 100 samples for calculation
- Shows "---" while collecting samples

**Display format:**
```
123  (integer, rounded up)
```

### MangoHudZeroOnePercentLow

Displays the 0.1% low FPS metric.

**Requirements:**
- Minimum 1000 samples for calculation
- Shows "---" while collecting samples

**Display format:**
```
115  (integer, rounded up)
```

## Usage in Theme

Add to your `theme.yaml`:

```yaml
STATS:
  CUSTOM:
    INTERVAL: 1
    MangoHudFPS:
      TEXT:
        SHOW: True
        X: 180
        Y: 340
        FONT_SIZE: 23
    MangoHud1PercentLow:
      TEXT:
        SHOW: True
        X: 180
        Y: 370
        FONT_SIZE: 23
    MangoHudZeroOnePercentLow:
      TEXT:
        SHOW: True
        X: 180
        Y: 400
        FONT_SIZE: 23
```

## Performance Characteristics

### Accuracy Timeline

| Time Elapsed | Samples Collected | Metrics Available |
|--------------|-------------------|-------------------|
| 1 second     | ~120 (at 120 FPS) | 1% low calculated |
| 8 seconds    | 1000              | Both metrics stable |
| Ongoing      | 1000 (rolling)    | Continuous updates |

### Memory Usage

- **Frame time buffer**: ~8KB (1000 floats)
- **Total overhead**: <10KB per instance
- **CPU impact**: Negligible (<0.1%)

## Technical Details

### Why Frame-Based Window?

A **fixed number of frames** (1000) rather than fixed time provides:
- ✅ Consistent statistical significance
- ✅ 1% = exactly 10 frames (easy to understand)
- ✅ Standard approach for benchmarking tools

### Why Not Session-Wide Tracking?

Rolling window (last 1000 frames) vs entire session:

**Rolling window (current implementation):**
- ✅ Reflects current performance
- ✅ Adapts to changing conditions (menu vs combat)
- ✅ Reasonable memory usage
- ❌ Doesn't track "worst ever" stutter

**Session-wide tracking:**
- ✅ Shows worst stutter of entire session
- ❌ Uses more memory
- ❌ Old stutters (loading screens) affect current metric
- ❌ Doesn't reflect current performance

### Rounding Strategy

Uses `math.ceil()` instead of `int()` for display:

```python
math.ceil(119.9) = 120  # More accurate
int(119.9) = 119        # Underreports performance
```

## Interpretation

### Good Performance Example
```
FPS:  120
1%:   115
0.1%: 110
```
- Consistent frame times
- Minimal stuttering
- Smooth gameplay

### Poor Performance Example
```
FPS:  120
1%:    45
0.1%:  30
```
- Severe frame drops
- Noticeable stuttering
- Average FPS is misleading

### What to Look For

- **1% low close to average**: Good frame time consistency
- **1% low much lower**: Frequent stutters
- **0.1% low very low**: Severe frame drops (even if rare)

## Limitations

1. **Approximation**: We calculate average frametime per update cycle, not individual frame times
2. **Sample rate**: Limited by INTERVAL setting (default 1 second)
3. **Window size**: Fixed at 1000 frames (not configurable via theme)
4. **No history**: Line graph not implemented for low FPS metrics

## Future Enhancements

Possible improvements:
- Configurable window size via theme
- Session-wide min/max tracking
- Line graph support for 1% low history
- Color-coded display based on thresholds
- Average FPS calculation from our samples (independent of MangoHud)

## References

- [CapFrameX Documentation](https://github.com/CXWorld/CapFrameX) - Industry standard for frame time analysis
- [MangoHud FPS Socket](https://github.com/flightlessmango/MangoHud) - Data source
- [Frame Time Analysis](https://www.pcgamer.com/what-is-one-percent-low-fps/) - Understanding 1% low metrics
