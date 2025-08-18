# Data structures and types to be used throughout the project

from dataclasses import dataclass
from typing import Optional, Tuple

@dataclass
class SensorData:
    """
    Data structure for sensor readings

    """
    timestamp: float
    ultrasonic_distance: float
    person_detected: bool
    person_bbox: Optional[Tuple[int, int, int, int]]
    person_center_x: Optional[int]
    confidence: Optional[float]


@dataclass
class MotorCommand:
    """
    Data structure for motor commands

    """
    timestamp: float
    left_speed: float
    right_speed :float
    action: str # Actions such as follow, stop, search, maintan_dance, backup

@dataclass
class RobotState:
    """
    Data structure for robot state and information

    """
    mode: str
    is_running: bool
    person_lost_count: int
    last_sensor_data: Optional[SensorData]
    last_motor_command: Optional[MotorCommand]

@dataclass
class LineData:
    """
    Data structure for line detection results
    
    """
    timestamp: float
    line_detected: bool
    line_center_x: Optional[int]
    line_angle: Optional[float]
    line_width: Optional[int]
    confidence: float
    contour_area: Optional[float]
    