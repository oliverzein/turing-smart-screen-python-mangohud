#!/usr/bin/env python3
"""
Test script for MangoHudFPS custom data class.
Run this to verify the integration works before adding to themes.

Usage:
    python3 test_mangohud_fps.py

Requirements:
    - Game running with MangoHud
    - fps_socket=1 in MangoHud config
"""

import sys
import time

# Add library path
sys.path.insert(0, 'library')

try:
    from sensors.sensors_custom import (
        MangoHudFPS,
        MangoHudFPSAvg,
        MangoHudGPULoad,
        MangoHudGPUTemp,
        MangoHudGPUJunctionTemp,
        MangoHudGPUPower,
        MangoHudCPULoad,
        MangoHudCPUPower,
        MangoHudCPUTemp,
        MangoHudGPUVramUsed,
    )
except ImportError as e:
    print(f"Error: Could not import MangoHudFPS class")
    print(f"Make sure you've added the class to library/sensors/sensors_custom.py")
    print(f"Error details: {e}")
    sys.exit(1)

def main():
    print("MangoHud Metrics Test")
    print("=" * 60)
    print("This script will attempt to connect to a MangoHud FPS socket")
    print("and display real-time FPS data.\n")
    print("Requirements:")
    print("  1. Game running with MangoHud")
    print("  2. fps_socket=1 in MangoHud config")
    print("\nPress Ctrl+C to stop\n")
    
    # Create sensor instances
    fps_sensor = MangoHudFPS()
    fps_avg = MangoHudFPSAvg()
    gpu_load = MangoHudGPULoad()
    gpu_temp = MangoHudGPUTemp()
    gpu_junc = MangoHudGPUJunctionTemp()
    gpu_power = MangoHudGPUPower()
    cpu_load = MangoHudCPULoad()
    cpu_power = MangoHudCPUPower()
    cpu_temp = MangoHudCPUTemp()
    vram = MangoHudGPUVramUsed()

    print(
        f"{'Time':>8} | {'Status':>12} | {'FPS':>3} | {'1%':>3} | {'AVG':>3} | "
        f"{'GL%':>3} | {'GT':>3} | {'GJ':>3} | {'GP':>3} | "
        f"{'CL%':>3} | {'CT':>3} | {'CP':>3} | {'VRAM':>4}"
    )
    print("-" * 110)
    
    update_count = 0
    try:
        while True:
            # Get metrics (this triggers auto-discovery and connection)
            fps_numeric = fps_sensor.as_numeric()
            fps_string = fps_sensor.as_string()
            one_percent_low_fps = fps_sensor.one_percent_low_fps
            # Additional metrics
            fps_avg_v = int(round(fps_avg.as_numeric()))
            gpu_load_v = int(round(gpu_load.as_numeric()))
            gpu_temp_v = int(round(gpu_temp.as_numeric()))
            gpu_junc_v = int(round(gpu_junc.as_numeric()))
            gpu_power_v = int(round(gpu_power.as_numeric()))
            cpu_load_v = int(round(cpu_load.as_numeric()))
            cpu_temp_v = int(round(cpu_temp.as_numeric()))
            cpu_power_v = int(round(cpu_power.as_numeric()))
            vram_v = int(round(vram.as_numeric()))
            
            # Determine status
            if fps_sensor.connected:
                status = f"PID {fps_sensor.pid}"
            elif fps_sensor.pid is None:
                status = "Scanning..."
            else:
                status = "Connecting"
            
            # Display
            timestamp = time.strftime("%H:%M:%S")
            print(
                f"{timestamp:>8} | {status:>12} | {int(round(fps_numeric)):>3} | {int(round(one_percent_low_fps)):>3} | {fps_avg_v:>3} | "
                f"{gpu_load_v:>3} | {gpu_temp_v:>3} | {gpu_junc_v:>3} | {gpu_power_v:>3} | "
                f"{cpu_load_v:>3} | {cpu_temp_v:>3} | {cpu_power_v:>3} | {vram_v:>4}",
                end='\r'
            )
            
            update_count += 1
            
            # Every 10 updates, print on new line to show history
            if update_count % 10 == 0:
                print()  # New line
            
            time.sleep(1)  # Update every second
            
    except KeyboardInterrupt:
        print("\n\nTest stopped by user")
        
        # Show summary
        print("\nSummary:")
        print(f"  Updates: {update_count}")
        print(f"  Final status: {'Connected' if fps_sensor.connected else 'Disconnected'}")
        if fps_sensor.connected:
            print(f"  Game PID: {fps_sensor.pid}")
            print(f"  Last FPS: {int(round(fps_sensor.current_fps))}")
        
        # Show line graph data
        history = fps_sensor.last_values()
        valid_values = [v for v in history if not (v != v)]  # Filter out NaN
        if valid_values:
            print(f"\nFPS History Statistics:")
            print(f"  Samples: {len(valid_values)}")
            print(f"  Min FPS: {min(valid_values):.1f}")
            print(f"  Max FPS: {max(valid_values):.1f}")
            print(f"  Avg FPS: {sum(valid_values)/len(valid_values):.1f}")
        
        # Cleanup
        fps_sensor.disconnect()
        print("\nDisconnected from MangoHud socket")

if __name__ == "__main__":
    main()
