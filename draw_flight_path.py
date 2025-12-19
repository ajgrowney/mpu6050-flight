"""Generate a 3D flight path visualization based on telemetry data
Canvas: 3d scatter plot with time-based color gradient
    Each point holds (x, y, z) coordinates from telemetry
    Color gradient from blue (start) to red (end) based on time
"""
import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d import Axes3D
import matplotlib.animation as animation
from collections import deque
import numpy as np
import serial
import json

from helpers import parse_telemetry_line, compute_position_from_telemetry

class FlightPathVisualizer:
    def __init__(self, serial_port='/dev/ttyUSB0', baud_rate=9600, max_points=1000, constant_speed=1.0):
        """
        Initialize the 3D flight path visualizer
        
        Args:
            serial_port: Serial port path (e.g., '/dev/ttyUSB0' or 'COM3')
            baud_rate: Serial baud rate
            max_points:  Maximum number of points to display
        """
        self.max_points = max_points
        self.constant_speed = constant_speed
        self.position = (0.0, 0.0, 0.0)
        self.velocity = (0.0, 0.0, 0.0)
        self.last_time = None
        
        # Data storage with sliding window
        self.x_data = deque(maxlen=max_points)
        self.y_data = deque(maxlen=max_points)
        self.z_data = deque(maxlen=max_points)
        self.timestamps = deque(maxlen=max_points)
        
        # Initialize serial connection
        try:
            self.ser = serial.Serial(serial_port, baud_rate, timeout=0.1)
        except Exception as e:
            print(f"Warning: Could not open serial port:  {e}")
            self.ser = None
        
        # Setup 3D plot
        self.fig = plt.figure(figsize=(12, 9))
        self.ax = self.fig.add_subplot(111, projection='3d')
        self.scatter = None
        
        # Configure plot aesthetics
        self.ax.set_xlabel('X Position (m)', fontsize=10)
        self.ax.set_ylabel('Y Position (m)', fontsize=10)
        self.ax.set_zlabel('Altitude (m)', fontsize=10)
        self.ax.set_title('Real-Time 3D Flight Path', fontsize=14, fontweight='bold')
        
        # Set initial limits (will auto-adjust)
        self.ax.set_xlim(-10, 10)
        self.ax.set_ylim(-10, 10)
        self.ax.set_zlim(0, 20)
        
        self.frame_count = 0

    def read_serial_data(self):
        """Read and parse data from serial port"""
        if self.ser and self.ser.in_waiting > 0:
            try:
                line = self.ser.readline().decode('utf-8').strip()
                return parse_telemetry_line(line, mode = "human_readable")
            except Exception as e:
                print(f"Serial read error: {e}")
        return dict()

    def update(self, frame):
        """Animation update function"""
        # Read new telemetry data
        full_data_packet = self.read_serial_data()
        
        if not full_data_packet:
            return self.scatter,
        
        # Compute dt from telemetry timestamps
        current_time = full_data_packet.get('time', 0)
        dt = (current_time - self.last_time) if self.last_time else 0.05
        self.last_time = current_time
        
        # Convert telemetry to position
        self.position, self.velocity = compute_position_from_telemetry(
            full_data_packet, 
            self.position, 
            self.velocity,
            self.constant_speed,
            dt
        )
        
        x, y, z = self.position

        # Add new data point
        self.x_data.append(x)
        self.y_data.append(y)
        self.z_data.append(z)
        self.timestamps.append(self.frame_count)
        self.frame_count += 1
        
        # Clear previous scatter plot
        if self.scatter:
            self.scatter.remove()
        
        # Create color gradient from blue (start) to red (end)
        if len(self.x_data) > 0:
            # Normalize timestamps for color mapping
            colors = np.array(self.timestamps)
            if len(colors) > 1:
                colors = (colors - colors.min()) / (colors.max() - colors.min())
            else:
                colors = np.array([0.0])
            
            # Create RGB color array:  blue -> red
            color_array = np.zeros((len(colors), 4))
            color_array[:, 0] = colors  # Red channel increases
            color_array[:, 2] = 1 - colors  # Blue channel decreases
            color_array[:, 3] = 1.0  # Alpha channel
            
            # Plot scatter with color gradient
            self.scatter = self.ax.scatter(
                self.x_data, 
                self.y_data, 
                self.z_data,
                c=color_array,
                s=20,
                marker='o',
                depthshade=True
            )
            
            # Auto-adjust plot limits with padding
            if len(self.x_data) > 2:
                x_arr, y_arr, z_arr = np.array(self.x_data), np.array(self.y_data), np.array(self.z_data)
                
                x_padding = (x_arr.max() - x_arr.min()) * 0.1 or 1
                y_padding = (y_arr.max() - y_arr.min()) * 0.1 or 1
                z_padding = (z_arr.max() - z_arr.min()) * 0.1 or 1
                
                self.ax.set_xlim(x_arr.min() - x_padding, x_arr.max() + x_padding)
                self.ax.set_ylim(y_arr.min() - y_padding, y_arr.max() + y_padding)
                self.ax.set_zlim(z_arr.min() - z_padding, z_arr.max() + z_padding)
        
        # Update title with current point count
        self.ax.set_title(f'Real-Time 3D Flight Path ({len(self.x_data)} points)', 
                         fontsize=14, fontweight='bold')
        
        return self.scatter,
    
    def start(self, interval=50):
        """
        Start the real-time visualization
        
        Args:
            interval: Update interval in milliseconds (default: 50ms = 20 FPS)
        """
        ani = animation.FuncAnimation(
            self.fig, 
            self.update, 
            interval=interval,
            blit=False,  # blit=False for 3D plots
            cache_frame_data=False
        )
        plt.show()
    
    def __del__(self):
        """Cleanup serial connection"""
        if self.ser: 
            self.ser.close()


# Usage
if __name__ == "__main__":
    # For Linux/Mac
    visualizer = FlightPathVisualizer(serial_port='/dev/cu.usbmodem1421201', baud_rate=115200)
    visualizer.start(interval=50)  # Update every 50ms