# MangoHud Integration Changelog

## 2025-10-18 - Updated to 88-byte packet format

### Changes

**Updated packet format from 84 to 88 bytes:**
- Added `gpu_junction_temp` field (4 bytes, int)
- New packet structure: 88 bytes total
  - 1 double (8 bytes): fps
  - 3 floats (12 bytes): frametime, cpu_load, cpu_power
  - **8 ints (32 bytes)**: cpu_mhz, gpu_load, cpu_temp, gpu_temp, **gpu_junction_temp**, gpu_core_clock, gpu_mem_clock, gpu_power
  - 7 floats (28 bytes): gpu_vram_used, ram_used, swap_used, process_rss, fps_1_percent_low, fps_0_1_percent_low, fps_97_percentile
  - 1 uint64 (8 bytes): elapsed_ns

### Files Modified

1. **library/sensors/sensors_custom.py**
   - Updated `recv()` size: `84` → `88` bytes
   - Updated struct format: `'=dfffiiiiiiifffffffQ'` → `'=dfffiiiiiiiifffffffQ'`
   - Updated field indices:
     - `one_percent_low_fps`: `values[15]` → `values[16]`
     - `zero_one_percent_low_fps`: `values[16]` → `values[17]`

2. **MangoHudIntegration/MANGOHUD_INTEGRATION.md**
   - Updated packet description: 16-byte → 88-byte
   - Updated documentation to reflect full metrics support

### Compatibility

**Breaking change:** Requires MangoHud with 88-byte packet format.

**To update:**
1. Rebuild and install updated MangoHud
2. Restart game to load new library
3. Client will automatically use new format

### New Metrics Available

The 88-byte format provides access to:
- ✅ FPS (current, 1% low, 0.1% low, 97th percentile)
- ✅ CPU metrics (load, temp, frequency, power)
- ✅ GPU metrics (load, temp, **junction temp**, clocks, power)
- ✅ Memory metrics (VRAM, RAM, swap, process RSS)
- ✅ Timing (elapsed time since log start)

### Testing

Run the test script to verify:
```bash
cd /path/to/turing-smart-screen-python-mangohud
python3 MangoHudIntegration/test_mangohud_fps.py
```

Expected output:
```
Time     | Status       | FPS      | 1% Low   | 0.1% Low
----------------------------------------------------------------------
12:34:56 | PID 12345    | 120.0    | 95.2     | 87.3
```
