# Person Following Robot - Mode 1

## Project Structure
```
robot_controller/
├── config.py              # Configuration and constants
├── main.py                 # Main application entry point
├── sensors/
│   ├── camera.py          # Camera interface
│   ├── ultrasonic.py      # Ultrasonic sensor
│   └── person_detector.py # Person detection
├── motors/
│   └── motor_controller.py # Motor control
├── modes/
│   └── person_follower.py  # Person following logic
├── utils/
│   ├── pid_controller.py   # PID controller
│   ├── data_structures.py  # Data structures
│   └── data_logger.py      # Data logging
├── models/                 # ML models directory
└── data/
    └── logs/              # Session logs
```

## Installation
```bash
pip install -r requirements.txt

# For Raspberry Pi:
pip install picamera2 RPi.GPIO
```

## Usage
```bash
python main.py
```

## Features
- Modular, testable architecture
- TensorFlow Lite person detection with fallback
- PID-controlled smooth following
- Comprehensive data logging for analysis
- Safety mechanisms and error handling
- Development mode for testing without hardware
""" action
        
        # Person detected - reset lost counter
        self.state.person_lost_count = 0
        
        # Safety check - too close
        if sensor_data.ultrasonic_distance < MIN_SAFE_DISTANCE:
            action = "backup"
            left_speed = -40
            right_speed = -40
            return left_speed, right_speed,