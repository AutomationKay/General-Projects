# Providing functionality for logging data

import json
import os
from datetime import datetime
from typing import List
from .data_structures import SensorData, MotorCommand

class DataLogger:
    """
    
    Class for logging data from the operations of the robot to be used for analysis
    
    """

    def __init__(self, session_name: str = None, log_dir: str = "data/logs"):
        self.log_dir = log_dir
        os.makedirs(log_dir, exist_ok=True) # To check if directory exists, if it doesn't create it

        if session_name is None:
            session_name = datetime.now().strftime("session_%Y%m%d_%H%M%S")
        
        self.session_name = session_name
        self.log_file = os.path.join(log_dir, f"{session_name}.json")

        self.data = {
            'session_info': {
                'name':session_name,
                'start_time':datetime.now().isoformat(),
                'end_time':None
            },
            'sensor_data':[],
            'motor_commands':[],
            'performance_metrics':{},
            'events':[]
        }
        
    def log_sensor_data(self, data: SensorData):
        """
        
        Log for sensor readings
        
        """
        sensor_dict = {
            'timestamp':data.timestamp,
            'ultrasonic_distance':data.ultrasonic_distance,
            'person_detected': data.person_detected,
            'person_bbox':data.person_center_x,
            'confidence':data.confidence
        }
        self.data['sensor_data'].append(sensor_dict)
    
    def log_motor_command(self, command: MotorCommand):
        """
        
        Log for motor commands
        
        """
        command_dict = {
            'timestamp':command.timestamp,
            'left_speed':command.left_speed,
            'right_speed':command.right_speed,
            'action':command.action
        }
        self.data['motor_commands'].append(command_dict)
    
    def log_event(self, event: str, details: dict = None):
        """
        
        Log significant events
        
        """
        event_data = {
            'timestamp': datetime.now().timestamp(),
            'event': event,
            'details': details or {}
        }
        self.data['events'].append(event_data)
    
    def calculate_performance_metrics(self):
        """
        
        Calculate session performance metrics
        
        """
        if not self.data['sensor_data']:
            return
        
        # Calculate basic metrics
        total_detections = sum(1 for d in self.data['sensor_data'] if d['person_detected'])
        total_frames = len(self.data['sensor_data'])
        detection_rate = total_detections / total_frames if total_frames > 0 else 0
        
        # Distance statistics
        distances = [d['ultrasonic_distance'] for d in self.data['sensor_data'] 
                    if d['ultrasonic_distance'] < 500]  # Filter out invalid readings
        
        metrics = {
            'total_frames': total_frames,
            'detection_rate': detection_rate,
            'total_detections': total_detections,
            'session_duration': len(self.data['sensor_data']) * 0.05,  # Adjust based on FPS (Currently assuming 20fps)
            'distance_stats': {
                'mean': sum(distances) / len(distances) if distances else 0,
                'min': min(distances) if distances else 0,
                'max': max(distances) if distances else 0
            }
        }
        
        self.data['performance_metrics'] = metrics
    
    def save_session(self):
        """
        
        Save complete session data
        
        """
        self.data['session_info']['end_time'] = datetime.now().isoformat()
        self.calculate_performance_metrics()
        
        with open(self.log_file, 'w') as f:
            json.dump(self.data, f, indent=2)
        
        print(f"Session data saved to: {self.log_file}")