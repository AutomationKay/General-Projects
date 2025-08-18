# FIle for configuration and holding constants to be used throughout the project

import os



# Hardware configuration
HARDWARE_AVAILABLE = True   # Can be toggled between true and false. False for development, True for testing

ULTRASONIC_TRIGGER_PIN = 27
ULTRASONIC_ECHO_PIN = 22
MOTOR_LEFT_PINS = (24, 23) # PWM, Direction
MOTOR_RIGHT_PINS = (5, 6) # PWM, Direction
PWM_FREQUENCY = 1000
IR01 = 16
IR02 = 20
IR03 = 21


# Camera Fonfiguration
CAMERA_WIDTH = 640 # Setting smaller to compensate for processing power of Raspberry Pi
CAMERA_HEIGHT = 480
CAMERA_FPS = 20


# Parameters for Robot Control
PID_STEERING = {'kp':0.5, 'ki':0.1, 'kd':0.2, 'setpoint':0}
PID_DISTANCE = {'kp':1.0, 'ki':0.2, 'kd':0.3, 'setpoint':150}

# Safety parameters in centimeters
MIN_SAFE_DISTANCE = 50
MAX_FOLLOW_DISTANCE = 300
MAX_SPEED = 100
MAX_PERSON_LOST_FRAMES = 30

# Model setup
MODEL_PATH = "models/mobilenet_ssd_v2_coco.tflite"
PERSON_DETECTION_THRESHOLD = 0.5

# Logging setup
LOG_DIR = "data/logs"
LOG_LEVEL = "INFO"