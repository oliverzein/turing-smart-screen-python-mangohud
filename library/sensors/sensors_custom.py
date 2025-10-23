# SPDX-License-Identifier: GPL-3.0-or-later
#
# turing-smart-screen-python - a Python system monitor and library for USB-C displays like Turing Smart Screen or XuanFang
# https://github.com/mathoudebine/turing-smart-screen-python/
#
# Copyright (C) 2021 Matthieu Houdebine (mathoudebine)
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
import time
import logging
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
        # Return provider FPS history (unitless)
        return self.provider.get_history('fps')


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


# Shared MangoHud metrics provider (singleton)
class MangoHudMetrics:
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(MangoHudMetrics, cls).__new__(cls)
        return cls._instance

    def __init__(self):
        if getattr(self, "_init_done", False):
            return
        self._init_done = True

        self._logger = logging.getLogger(__name__ + ".MangoHudMetrics")
        self.client = None
        self.connected = False
        self.pid = None
        self.metrics = {}
        self.last_update_ts = 0.0
        # Pre-allocate histories (60 samples)
        self.histories = {
            'fps': [math.nan] * 60,
            'gpu_load': [math.nan] * 60,
            'gpu_temp': [math.nan] * 60,
            'gpu_junction_temp': [math.nan] * 60,
            'gpu_power': [math.nan] * 60,
        }

        # Try import client lazily; tolerate absence
        try:
            from mangosocketreader.client import MangoHudClient
            self.client = MangoHudClient()
        except Exception as e:
            self._logger.debug(f"MangoHudMetrics: client import failed (lazy retry later): {e}")

    @staticmethod
    def instance():
        return MangoHudMetrics()

    def ensure_client(self) -> bool:
        if self.client is None:
            try:
                from mangosocketreader.client import MangoHudClient
                self.client = MangoHudClient()
            except Exception as e:
                self._logger.debug(f"ensure_client(): failed: {e}")
                return False
        return True

    def ensure_connected(self) -> bool:
        if not self.ensure_client():
            return False
        if self.connected:
            return True
        try:
            self.connected = bool(self.client.connect())
            if self.connected:
                try:
                    self.pid = self.client.get_pid()
                except Exception:
                    self.pid = None
        except Exception as e:
            self._logger.debug(f"ensure_connected(): connect failed: {e}")
            self.connected = False
        return self.connected

    def disconnect(self):
        try:
            if self.client is not None:
                self.client.disconnect()
        finally:
            self.connected = False
            self.pid = None

    def update(self) -> bool:
        """Fetch latest metrics once per call; update histories."""
        if not self.connected:
            return False
        # Small guard to avoid excessive reads if called multiple times per tick
        now = time.time()
        if now - self.last_update_ts < 0.01:
            return bool(self.metrics)
        self.last_update_ts = now

        try:
            m = self.client.read_metrics()
        except Exception as e:
            self._logger.debug(f"update(): read_metrics failed: {e}")
            m = None
        if not m:
            return False
        self.metrics = m

        # Append to histories if present
        for k in self.histories.keys():
            val = m.get(k)
            if val is None:
                val = math.nan
            self.histories[k].append(float(val))
            self.histories[k].pop(0)
        return True

    def get(self, field: str):
        return self.metrics.get(field)

    def get_history(self, field: str) -> List[float]:
        return self.histories.get(field, [math.nan] * 60)

    def is_connected(self) -> bool:
        return self.connected

    def get_pid(self) -> Optional[int]:
        return self.pid


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
        
        # Set safe defaults first so object always has expected attributes
        self.client = None
        self._logger = logging.getLogger(__name__ + ".MangoHudFPS")
        self.last_val = [math.nan] * 60  # Store last 60 FPS values for line graph
        self.connected = False
        self.pid: Optional[int] = None
        self.last_discovery_time = 0.0
        self.discovery_interval = 5.0  # Re-scan for sockets every 5 seconds when not connected
        # metrics
        self.current_fps: float = 0.0
        self.one_percent_low_fps: float = 0.0
        self.zero_one_percent_low_fps: float = 0.0
        # Shared provider
        self.provider = MangoHudMetrics.instance()
        MangoHudFPS._initialized = True

    def connect(self) -> bool:
        """Connect using shared MangoSocketReader client (auto-discovers)."""
        if self.connected:
            return True
        ok = self.provider.ensure_connected()
        self.connected = self.provider.is_connected()
        self.pid = self.provider.get_pid()
        return ok

    def disconnect(self):
        """Disconnect from MangoHud FPS socket."""
        self.provider.disconnect()
        self.connected = False
        self.pid = None
    
    def discover_and_connect(self):
        """
        Auto-discover MangoHud socket and connect.
        Only scans when not connected and discovery_interval has elapsed.
        """
        current_time = time.time()
        
        # Only attempt connect if not connected and enough time has passed
        if not self.connected and (current_time - self.last_discovery_time) >= self.discovery_interval:
            self.last_discovery_time = current_time
            self._logger.debug("discover_and_connect(): attempting provider.ensure_connected()")
            self.connect()
    
    def read_fps_data(self) -> bool:
        """
        Read FPS data using MangoSocketReader client.
        Drains the socket buffer via library to get the most recent packet.
        Returns True if data was successfully read, False otherwise.
        """
        if not self.connected:
            self._logger.debug("read_fps_data(): not connected")
            return False
        ok = self.provider.update()
        if not ok:
            self._logger.debug("read_fps_data(): provider has no metrics yet")
            return False
        fps = float(self.provider.get('fps') or 0.0)
        self.current_fps = fps
        self.one_percent_low_fps = float(self.provider.get('fps_1_percent_low') or 0.0)
        return True
    
    def as_numeric(self) -> float:
        """
        Return current FPS as numeric value for graphs and radial bars.
        This method is called by the framework on every update cycle.
        """
        # Try to discover and connect if not connected
        self._logger.debug("as_numeric(): tick; connected=%s pid=%s", self.connected, self.pid)
        self.discover_and_connect()
        
        # Read FPS data if connected
        if self.connected:
            ok = self.read_fps_data()
            self._logger.debug("as_numeric(): read_fps_data ok=%s fps=%.2f", ok, self.current_fps)
        
        return self.current_fps
    
    def as_string(self) -> str:
        """
        Return formatted FPS string for text display.
        Uses fixed width to prevent ghosting effect.
        """
        # If client not yet constructed (early call), try to build it; otherwise show placeholder
        # Ensure connection even if only as_string() is polled by the framework
        if not self.connected:
            self._logger.debug("as_string(): not connected -> attempting discover_and_connect()")
            self.discover_and_connect()

        if not self.provider.is_connected():
            # Not connected - either scanning or no game found
            return "---"  # 7 chars
        
        # Optionally refresh a sample so text reflects latest FPS even without as_numeric()
        try:
            if self.connected:
                ok = self.read_fps_data()
                self._logger.debug("as_string(): post-connect read ok=%s fps=%.2f", ok, self.current_fps)
        except Exception as e:
            self._logger.debug(f"as_string(): read_fps_data raised: {e}")
        
        # Connected and have FPS data
        # Format: "123 FPS" with fixed width to prevent ghosting
        # Use >3d to ensure consistent width (e.g., " 12", "123")
        return f"{round(self.current_fps):>3d}"
    
    def last_values(self) -> List[float]:
        """
        Return list of last FPS values for line graph.
        Returns 60 samples (1 minute of history at 1 sample/second).
        """
        return self.last_val


# MangoHud 1% Low FPS - displays the 1% low FPS metric
class MangoHud1PercentLow(CustomDataSource):
    """
    Custom data source that displays 1% low FPS from MangoHud data.
    
    1% low FPS represents the average FPS of the worst 1% of frames,
    which is a better indicator of stuttering and frame drops than average FPS.
    
    This class uses the singleton MangoHudFPS instance to access the calculated
    1% low FPS value.
    
    Usage in theme.yaml:
        CUSTOM:
          INTERVAL: 1
          MangoHud1PercentLow:
            TEXT:
              SHOW: True
              X: 10
              Y: 40
              FONT_SIZE: 16
              FONT_COLOR: 255, 200, 0
    """
    
    def as_numeric(self) -> float:
        """Return 1% low FPS as numeric value."""
        # Get the singleton MangoHudFPS instance
        fps_instance = MangoHudFPS()
        return fps_instance.one_percent_low_fps
    
    def as_string(self) -> str:
        """Return formatted 1% low FPS string."""
        fps_instance = MangoHudFPS()
        
        if not fps_instance.connected:
            return "---"

        # Format: "1%: 95 FPS"
        #return f"1%: {int(fps_instance.one_percent_low_fps):>3d} FPS"
        return f"{round(fps_instance.one_percent_low_fps):>3d}"
    
    def last_values(self) -> List[float]:
        """Not implemented for 1% low - would need history tracking."""
        return [math.nan] * 60


# Additional MangoHud sensors using provider (unitless, integer formatting)
class _MangoHudBaseSensor(CustomDataSource):
    def __init__(self, field: str, history: bool = False):
        self.provider = MangoHudMetrics.instance()
        self.field = field
        self.use_history = history
        self._last_values = [math.nan] * 60 if history else None

    def _ensure(self):
        self.provider.ensure_connected()
        self.provider.update()

    def as_numeric(self) -> float:
        self._ensure()
        v = self.provider.get(self.field)
        try:
            return float(v) if v is not None else 0.0
        except Exception:
            return 0.0

    def as_string(self) -> str:
        v = self.as_numeric()
        try:
            return f"{int(round(v)):>3d}"
        except Exception:
            return "---"

    def last_values(self) -> List[float]:
        if not self.use_history:
            return [math.nan] * 60
        return self.provider.get_history(self.field)


class MangoHudFPSAvg(_MangoHudBaseSensor):
    def __init__(self):
        super().__init__('fps_avg', history=False)


class MangoHudGPULoad(_MangoHudBaseSensor):
    def __init__(self):
        super().__init__('gpu_load', history=True)


class MangoHudGPUTemp(_MangoHudBaseSensor):
    def __init__(self):
        super().__init__('gpu_temp', history=True)


class MangoHudGPUJunctionTemp(_MangoHudBaseSensor):
    def __init__(self):
        super().__init__('gpu_junction_temp', history=True)


class MangoHudGPUPower(_MangoHudBaseSensor):
    def __init__(self):
        super().__init__('gpu_power', history=True)


class MangoHudCPULoad(_MangoHudBaseSensor):
    def __init__(self):
        super().__init__('cpu_load', history=False)


class MangoHudCPUPower(_MangoHudBaseSensor):
    def __init__(self):
        super().__init__('cpu_power', history=False)


class MangoHudCPUTemp(_MangoHudBaseSensor):
    def __init__(self):
        super().__init__('cpu_temp', history=False)


class MangoHudGPUVramUsed(_MangoHudBaseSensor):
    def __init__(self):
        super().__init__('gpu_vram_used', history=False)


# MangoHud 0.1% Low FPS - displays the 0.1% low FPS metric
class MangoHudZeroOnePercentLow(CustomDataSource):
    """
    Custom data source that displays 0.1% low FPS from MangoHud data.
    
    0.1% low FPS represents the average FPS of the worst 0.1% of frames,
    showing the absolute worst frame drops.
    
    This class uses the singleton MangoHudFPS instance to access the calculated
    0.1% low FPS value.
    
    Usage in theme.yaml:
        CUSTOM:
          INTERVAL: 1
          MangoHudZeroOnePercentLow:
            TEXT:
              SHOW: True
              X: 10
              Y: 60
              FONT_SIZE: 16
              FONT_COLOR: 255, 100, 0
    """
    
    def as_numeric(self) -> float:
        """Return 0.1% low FPS as numeric value."""
        fps_instance = MangoHudFPS()
        return fps_instance.zero_one_percent_low_fps
    
    def as_string(self) -> str:
        """Return formatted 0.1% low FPS string."""
        fps_instance = MangoHudFPS()
        
        if not fps_instance.connected:
            return "---"
        
        # Format: "0.1%: 85 FPS"
        #return f"0.1%: {int(fps_instance.zero_one_percent_low_fps):>2d} FPS"
        return f"{math.ceil(fps_instance.zero_one_percent_low_fps):>3d}"
    
    def last_values(self) -> List[float]:
        """Not implemented for 0.1% low - would need history tracking."""
        return [math.nan] * 60
