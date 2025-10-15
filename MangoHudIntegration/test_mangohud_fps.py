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
    from sensors.sensors_custom import MangoHudFPS
except ImportError as e:
    print(f"Error: Could not import MangoHudFPS class")
    print(f"Make sure you've added the class to library/sensors/sensors_custom.py")
    print(f"Error details: {e}")
    sys.exit(1)

def main():
    print("MangoHud FPS Test")
    print("=" * 60)
    print("This script will attempt to connect to a MangoHud FPS socket")
    print("and display real-time FPS data.\n")
    print("Requirements:")
    print("  1. Game running with MangoHud")
    print("  2. fps_socket=1 in MangoHud config")
    print("\nPress Ctrl+C to stop\n")
    
    # Create FPS sensor instance
    fps_sensor = MangoHudFPS()
    
    print(f"{'Time':>8} | {'Status':>12} | {'FPS':>8} | {'Frametime':>10} | {'Frames':>10}")
    print("-" * 70)
    
    update_count = 0
    try:
        while True:
            # Get FPS data (this triggers auto-discovery and connection)
            fps_numeric = fps_sensor.as_numeric()
            fps_string = fps_sensor.as_string()
            
            # Get additional data
            frametime = fps_sensor.current_frametime
            frame_count = fps_sensor.frame_count
            
            # Determine status
            if fps_sensor.connected:
                status = f"PID {fps_sensor.pid}"
            elif fps_sensor.pid is None:
                status = "Scanning..."
            else:
                status = "Connecting"
            
            # Display
            timestamp = time.strftime("%H:%M:%S")
            print(f"{timestamp:>8} | {status:>12} | {fps_numeric:>8.1f} | {frametime:>8.2f} ms | {frame_count:>10d}", end='\r')
            
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
            print(f"  Last FPS: {fps_sensor.current_fps:.1f}")
        
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
