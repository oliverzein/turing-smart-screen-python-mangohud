# turing-smart-screen-python - a Python system monitor and library for USB-C displays like Turing Smart Screen or XuanFang
# https://github.com/mathoudebine/turing-smart-screen-python/
# Copyright (C) 2021-2023  Matthieu Houdebine (mathoudebine)
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <https://www.gnu.org/licenses/>.

# This file allows to add custom data source as sensors and display them in System Monitor themes
# There is no limitation on how much custom data source classes can be added to this file
# See CustomDataExample theme for the theme implementation part

import math
import platform
import socket
import struct
import time
from abc import ABC, abstractmethod
from typing import List, Optional


# Custom data classes must be implemented in this file, inherit the CustomDataSource and implement its 2 methods
class CustomDataSource(ABC):
    @abstractmethod
    def as_numeric(self) -> float:
        # Numeric value will be used for graph and radial progress bars
        # If there is no numeric value, keep this function empty
        pass

    @abstractmethod
    def as_string(self) -> str:
        # Text value will be used for text display and radial progress bar inner text
        # Numeric value can be formatted here to be displayed as expected
        # It is also possible to return a text unrelated to the numeric value
        # If this function is empty, the numeric value will be used as string without formatting
        pass

    @abstractmethod
    def last_values(self) -> List[float]:
        # List of last numeric values will be used for plot graph
        # If you do not want to draw a line graph or if your custom data has no numeric values, keep this function empty
        pass


# Example for a custom data class that has numeric and text values
class ExampleCustomNumericData(CustomDataSource):
    # This list is used to store the last 10 values to display a line graph
    last_val = [math.nan] * 10  # By default, it is filed with math.nan values to indicate there is no data stored

    def as_numeric(self) -> float:
        # Numeric value will be used for graph and radial progress bars
        # Here a Python function from another module can be called to get data
        # Example: self.value = my_module.get_rgb_led_brightness() / audio.system_volume() ...
        self.value = 75.845

        # Store the value to the history list that will be used for line graph
        self.last_val.append(self.value)
        # Also remove the oldest value from history list
        self.last_val.pop(0)

        return self.value

    def as_string(self) -> str:
        # Text value will be used for text display and radial progress bar inner text.
        # Numeric value can be formatted here to be displayed as expected
        # It is also possible to return a text unrelated to the numeric value
        # If this function is empty, the numeric value will be used as string without formatting
        # Example here: format numeric value: add unit as a suffix, and keep 1 digit decimal precision
        return f'{self.value:>5.1f}%'
        # Important note! If your numeric value can vary in size, be sure to display it with a default size.
        # E.g. if your value can range from 0 to 9999, you need to display it with at least 4 characters every time.
        # --> return f'{self.as_numeric():>4}%'
        # Otherwise, part of the previous value can stay displayed ("ghosting") after a refresh

    def last_values(self) -> List[float]:
        # List of last numeric values will be used for plot graph
        return self.last_val


# Example for a custom data class that only has text values
class ExampleCustomTextOnlyData(CustomDataSource):
    def as_numeric(self) -> float:
        # If there is no numeric value, keep this function empty
        pass

    def as_string(self) -> str:
        # If a custom data class only has text values, it won't be possible to display graph or radial bars
        return "Python: " + platform.python_version()

    def last_values(self) -> List[float]:
        # If a custom data class only has text values, it won't be possible to display line graph
        pass


# MangoHud FPS data class - connects to MangoHud FPS socket and displays game FPS
class MangoHudFPS(CustomDataSource):
    """
    Custom data source that reads FPS from MangoHud's FPS socket.
    
    Features:
    - Auto-discovers MangoHud FPS socket (no PID configuration needed)
    - Automatically reconnects when games start/stop
    - Supports all display types: TEXT, GRAPH, RADIAL, LINE_GRAPH
    - Singleton pattern ensures persistent connection across framework calls
    
    Requirements:
    1. MangoHud must be installed and enabled for games
    2. fps_socket=1 must be set in MangoHud config (~/.config/MangoHud/MangoHud.conf)
    3. Game must be launched with MangoHud
    
    Usage in theme.yaml:
        CUSTOM:
          INTERVAL: 1
          MangoHudFPS:
            TEXT:
              SHOW: True
              X: 10
              Y: 10
              FONT_SIZE: 20
    """
    
    # Singleton instance (per-process)
    _instance = None
    _initialized = False
    _process_id = None
    
    def __new__(cls):
        """Singleton pattern: ensure only one instance exists per process."""
        import os
        current_pid = os.getpid()
        
        # Reset singleton if we're in a different process
        if cls._process_id != current_pid:
            cls._instance = None
            cls._initialized = False
            cls._process_id = current_pid
        
        if cls._instance is None:
            cls._instance = super(MangoHudFPS, cls).__new__(cls)
        return cls._instance
    
    def __init__(self):
        """Initialize only once per process, even if __init__ is called multiple times."""
        # Skip initialization if already initialized in this process
        if MangoHudFPS._initialized:
            return
        
        MangoHudFPS._initialized = True
        
        self.sock: Optional[socket.socket] = None
        self.pid: Optional[int] = None
        self.current_fps: float = 0.0
        self.current_frametime: float = 0.0
        self.frame_count: int = 0
        self.last_val = [math.nan] * 60  # Store last 60 FPS values for line graph
        self.connected = False
        self.last_discovery_time = 0.0
        self.discovery_interval = 5.0  # Re-scan for sockets every 5 seconds when not connected
    
    def find_mangohud_socket(self) -> Optional[int]:
        """
        Auto-discover MangoHud FPS socket by scanning /proc/net/unix.
        Returns the PID of the first MangoHud game found, or None.
        """
        try:
            with open('/proc/net/unix', 'r') as f:
                for line in f:
                    if 'mangohud-fps-' in line:
                        # Extract PID from socket name
                        # Line format: "... @mangohud-fps-<pid> ..."
                        parts = line.split('mangohud-fps-')
                        if len(parts) > 1:
                            # Get the PID (first token after the prefix)
                            pid_str = parts[1].strip().split()[0]
                            try:
                                return int(pid_str)
                            except ValueError:
                                continue
        except (FileNotFoundError, PermissionError):
            pass
        return None
    
    def connect(self) -> bool:
        """Connect to MangoHud FPS socket for the current PID."""
        if self.connected or self.pid is None:
            return self.connected
        
        try:
            self.sock = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
            # Abstract namespace socket (leading null byte)
            socket_path = f"\0mangohud-fps-{self.pid}"
            self.sock.connect(socket_path)
            self.sock.setblocking(False)  # Non-blocking mode for fast buffer draining
            self.connected = True
            return True
        except (ConnectionRefusedError, FileNotFoundError, OSError):
            self.connected = False
            if self.sock:
                try:
                    self.sock.close()
                except:
                    pass
                self.sock = None
            return False
    
    def disconnect(self):
        """Disconnect from MangoHud FPS socket."""
        if self.sock:
            try:
                self.sock.close()
            except:
                pass
            self.sock = None
        self.connected = False
        self.pid = None
    
    def discover_and_connect(self):
        """
        Auto-discover MangoHud socket and connect.
        Only scans when not connected and discovery_interval has elapsed.
        """
        current_time = time.time()
        
        # Only re-scan if not connected and enough time has passed
        if not self.connected and (current_time - self.last_discovery_time) >= self.discovery_interval:
            self.last_discovery_time = current_time
            
            # Find any MangoHud socket
            pid = self.find_mangohud_socket()
            if pid:
                if pid != self.pid:
                    # New game detected, disconnect from old one
                    self.disconnect()
                    self.pid = pid
                # Try to connect
                self.connect()
    
    def read_fps_data(self) -> bool:
        """
        Read FPS data packet from socket.
        Drains the socket buffer to get the most recent packet.
        Returns True if data was successfully read, False otherwise.
        """
        if not self.connected:
            return False
        
        try:
            # Drain the socket buffer to get the most recent packet
            # MangoHud broadcasts every frame (~120 Hz), but we only read once per second
            # Socket is non-blocking, so this drains instantly
            latest_data = None
            
            while True:
                try:
                    # Non-blocking read
                    data = self.sock.recv(16)
                    if len(data) == 0:
                        # Connection closed
                        self.disconnect()
                        return False
                    elif len(data) != 16:
                        # Partial data, connection issue
                        if latest_data is None:
                            self.disconnect()
                            return False
                        break
                    latest_data = data
                except BlockingIOError:
                    # No more data available in buffer (this is normal)
                    break
            
            # If we didn't read any packets, keep last values
            if latest_data is None:
                return True
            
            # Unpack the most recent packet
            # '=' means native byte order, standard size
            fps, frametime, frame_count = struct.unpack('=dfI', latest_data)
            
            # Use FPS directly from MangoHud (already smoothed by fps_sampling_period)
            self.current_fps = fps
            self.current_frametime = frametime
            self.frame_count = frame_count
            
            # Store value for line graph history
            self.last_val.append(fps)
            self.last_val.pop(0)
            
            return True
        except (socket.error, struct.error) as e:
            # Connection error, disconnect and will retry
            self.disconnect()
            return False
    
    def as_numeric(self) -> float:
        """
        Return current FPS as numeric value for graphs and radial bars.
        This method is called by the framework on every update cycle.
        """
        # Try to discover and connect if not connected
        self.discover_and_connect()
        
        # Read FPS data if connected
        if self.connected:
            self.read_fps_data()
        
        return self.current_fps
    
    def as_string(self) -> str:
        """
        Return formatted FPS string for text display.
        Uses fixed width to prevent ghosting effect.
        """
        if not self.connected:
            # Not connected - either scanning or no game found
            if self.pid is None:
                return "No Game"  # 7 chars
            else:
                return "Connecting"  # 10 chars (will retry connection)
        
        # Connected and have FPS data
        # Format: "123 FPS" with fixed width to prevent ghosting
        # Use >3d to ensure consistent width (e.g., " 12", "123")
        return f"{int(self.current_fps):>3d} FPS"
    
    def last_values(self) -> List[float]:
        """
        Return list of last FPS values for line graph.
        Returns 60 samples (1 minute of history at 1 sample/second).
        """
        return self.last_val
