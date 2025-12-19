#!/usr/bin/env python3
"""
Simple Flight Computer Ground Station
Displays attitude data from Arduino in terminal
"""

import serial
import serial.tools.list_ports  # Import this at the top! 
import time
import math
import sys

from helpers import parse_telemetry_line

# Configuration
BAUD_RATE = 115200

def find_serial_port():
    """Helper to find Arduino port on Mac"""
    ports = serial.tools.list_ports.comports()
    
    print("Available serial ports:")
    for i, port in enumerate(ports):
        print(f"  {i}: {port.device} - {port.description}")
    
    if ports:
        choice = input(f"\nSelect port (0-{len(ports)-1}) or press Enter for port 0: ")
        idx = int(choice) if choice else 0
        return ports[idx]. device
    else:
        print("No serial ports found!")
        return None

def draw_attitude_indicator(roll, pitch, yaw):
    """Draw a simple ASCII attitude indicator"""
    width = 40
    height = 20
    
    # Clear screen (works on Mac/Linux)
    print("\033[2J\033[H")
    
    print("=" * 60)
    print(" " * 15 + "FLIGHT COMPUTER TELEMETRY")
    print("=" * 60)
    print()
    
    # Attitude display
    print(f"  Roll:   {roll:+7.2f}°  ", end="")
    print("[" + draw_bar(roll, -45, 45, 20) + "]")
    
    print(f"  Pitch: {pitch:+7.2f}°  ", end="")
    print("[" + draw_bar(pitch, -45, 45, 20) + "]")
    
    print(f"  Yaw:   {yaw:+7.2f}°  ", end="")
    print("[" + draw_bar(yaw, -180, 180, 20) + "]")
    
    print()
    print("=" * 60)
    
    # Simple horizon indicator
    draw_horizon(roll, pitch)

def draw_bar(value, min_val, max_val, width):
    """Draw a horizontal bar graph"""
    # Clamp value
    value = max(min_val, min(max_val, value))
    
    # Normalize to 0-1
    normalized = (value - min_val) / (max_val - min_val)
    
    # Create bar
    filled = int(normalized * width)
    bar = "█" * filled + "░" * (width - filled)
    
    return bar

def draw_horizon(roll, pitch):
    """Draw a simple artificial horizon"""
    width = 40
    height = 15
    
    print("\n  Artificial Horizon:")
    print("  " + "─" * width)
    
    center_x = width // 2
    center_y = height // 2
    
    # Calculate horizon line offset due to pitch
    pitch_offset = int((pitch / 90.0) * (height / 2))
    
    for y in range(height):
        line = "  │"
        
        for x in range(width):
            # Determine if this pixel is sky or ground
            # Account for pitch and roll
            y_relative = y - center_y + pitch_offset
            x_relative = x - center_x
            
            # Simple roll visualization
            roll_rad = math.radians(roll)
            rotated_y = (x_relative * math.sin(roll_rad) + 
                        y_relative * math.cos(roll_rad))
            
            if rotated_y < 0:
                char = "░"  # Sky
            else:
                char = "▓"  # Ground
            
            # Aircraft reference in center
            if y == center_y and abs(x - center_x) < 3:
                char = "✈" if x == center_x else "─"
            
            line += char
        
        line += "│"
        print(line)
    
    print("  " + "─" * width)

def main():
    print("Flight Computer Ground Station")
    print("=" * 60)
    
    # Find serial port
    port = find_serial_port()
    if not port:
        print("No port selected!")
        return
    
    print(f"\nConnecting to {port} at {BAUD_RATE} baud...")
    
    try:
        ser = serial.Serial(port, BAUD_RATE, timeout=1)
        time.sleep(2)  # Wait for Arduino to reset
        
        print("Connected!  Waiting for telemetry.. .\n")
        time.sleep(1)
        
        while True:
            if ser.in_waiting:
                line = ser.readline().decode('utf-8', errors='ignore').strip()
                print(f"Received: {line}")
                # Parse telemetry
                data = parse_telemetry_line(line)
                
                if data:
                    draw_attitude_indicator(
                        data['roll'],
                        data['pitch'],
                        data['yaw']
                    )
                    
                    # Show rates and accel
                    print(f"\n  Angular Rates (°/s):")
                    print(f"    Roll: {data['roll_rate']:+7.2f}  Pitch: {data['pitch_rate']:+7.2f}  Yaw: {data['yaw_rate']:+7.2f}")
                    
                    print(f"\n  Acceleration (m/s²):")
                    print(f"    X: {data['accel_x']:+7.2f}  Y: {data['accel_y']:+7.2f}  Z: {data['accel_z']:+7.2f}")
                    
                    print(f"\n  Mode: {data['mode']}  |  Time: {data['time']:.2f}s")
    
    except serial.SerialException as e:
        print(f"Error:  {e}")
        print("\nTry unplugging and replugging the Arduino")
    
    except KeyboardInterrupt:
        print("\n\nShutting down ground station...")
        ser.close()

if __name__ == "__main__":
    main()
