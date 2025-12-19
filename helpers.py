"""Helpers for telemetry parsing and processing
"""

import numpy as np

TELEMETRY_KEYS = [
    "time", "roll", "pitch", "yaw",
    "roll_rate", "pitch_rate", "yaw_rate",
    "accel_x", "accel_y", "accel_z", "mode"
]
def parse_telemetry_human(line) -> dict:
    """Parse a telemetry line into a dictionary
    Data Format:
        Time(s) | Roll   | Pitch  | Yaw    | RRate  | PRate  | YRate  | Ax     | Ay     | Az     | Mode
    """
    print(line)
    try:
        parts = line.split('|')
        data = {}
        for i, part in enumerate(parts):
            key = TELEMETRY_KEYS[i]
            value = part.strip()
            cast_type = float if key != "mode" else str
            data[key] = cast_type(value) if value else (0.0 if cast_type == float else "")
        return data if len(data) == len(TELEMETRY_KEYS) else None
    except Exception as e:
        print(f"Error parsing line: {line} - {e}")
        return None


def parse_telemetry_line(line, mode:str = "human_readable") -> dict:
    """Parse a telemetry line into a dictionary
    Data Format:
        time,roll,pitch,yaw,roll_rate,pitch_rate,yaw_rate,accel_x,accel_y,accel_z,mode
    """
    if mode == "human_readable":
        return parse_telemetry_human(line)
    else:
        raise Exception(f"Unknown telemetry parsing mode: {mode}")

def compute_position_from_telemetry(telemetry, prev_position, prev_velocity, constant_speed=1.0, dt=None):
    """
    Convert telemetry (roll, pitch, yaw, accel) to x, y, z position
    
    Args:
        telemetry: dict with 'time', 'roll', 'pitch', 'yaw', 'accel_x', 'accel_y', 'accel_z'
        prev_position: (x, y, z) tuple of previous position
        prev_velocity: (vx, vy, vz) tuple of previous velocity
        constant_speed: assumed forward speed in m/s
        dt: time delta (if None, computed from telemetry timestamps)
    
    Returns:
        new_position: (x, y, z) tuple
        new_velocity: (vx, vy, vz) tuple
    """
    # Convert angles to radians
    roll = np.radians(telemetry.get('roll', 0))
    pitch = np.radians(telemetry.get('pitch', 0))
    yaw = np.radians(telemetry.get('yaw', 0))
    
    # Direction vector based on orientation (assuming forward is +X in body frame)
    # Convert body-frame forward direction to world frame
    dx = constant_speed * np.cos(pitch) * np.cos(yaw)
    dy = constant_speed * np.cos(pitch) * np.sin(yaw)
    dz = constant_speed * np.sin(pitch)
    
    # Update position
    if dt is None:
        dt = 0.05  # default 50ms
    
    new_x = prev_position[0] + dx * dt
    new_y = prev_position[1] + dy * dt
    new_z = prev_position[2] + dz * dt
    
    return (new_x, new_y, new_z), (dx, dy, dz)