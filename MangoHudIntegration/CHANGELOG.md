# MangoHud Integration Changelog

## 2025-10-23 - Migrate to shared MangoSocketReader (48-byte v1.0)

### Summary

- Replaced bespoke MangoHud socket reader with the shared `MangoSocketReader` library.
- Protocol standardized to 48-byte payload (`'=dfffiiiiiff'`, version `1.0`).
- Updated `library/sensors/sensors_custom.py` to use `mangosocketreader.client.MangoHudClient` with robust lazy init and logging.
- Updated service setup instructions to install the shared library into the service venv.

### Changes

1. **library/sensors/sensors_custom.py**
   - Removed manual `/proc/net/unix` scanning and raw `recv(88)` parsing.
   - Added `MangoHudClient` usage for auto-discovery and non-blocking reads.
   - Ensured safe defaults and lazy client construction in `__init__()`, `connect()`, `read_fps_data()`, and `as_string()`.
   - Added debug logs to trace client initialization, connection, and reads.
   - Exposes `connected` and `pid` for compatibility with `test_mangohud_fps.py`.

2. **Service dependency**
   - Ensure the service interpreter can import the library:
     ```bash
     sudo -u <user> /path/to/.venv/bin/python3 -m pip install -e /path/to/MangoSocketReader
     # Verify
     sudo -u <user> /path/to/.venv/bin/python3 -c "import mangosocketreader, struct; import mangosocketreader.protocol as p; print(p.PACKET_VERSION, struct.calcsize(p.PACKET_FORMAT))"
     # Expect: 1.0 48
     ```
   - Optionally pin in `requirements.txt`:
     ```
     mangosocketreader @ file:///absolute/path/to/MangoSocketReader
     ```

3. **Docs**
   - This changelog supersedes prior references to the 88-byte format for this integration.
   - Note: The 48-byte payload includes `fps` and `fps_1_percent_low`. `0.1% low` is not present in this payload and will show as 0 or `---` unless added by the server in a future version.

### Testing

Run the included test script (works with the new client):

```bash
python MangoHudIntegration/test_mangohud_fps.py
```

Expected output (example):

```
Time     | Status       | FPS      | 1% Low   | 0.1% Low
----------------------------------------------------------------------
12:34:56 | PID 12345    | 120.0    | 100.5    | 0.0
```

### Notes

- If the service doesn’t show values but the test does, ensure the library is installed with the same interpreter the service uses (`python -m pip ...`).
- Optional: move `StartLimitIntervalSec`/`StartLimitBurst` to the `[Unit]` section in the systemd unit to silence warnings.

---

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
