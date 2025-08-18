# Motor controller 

import time
from config import HARDWARE_AVAILABLE, MOTOR_LEFT_PINS, MOTOR_RIGHT_PINS, PWM_FREQUENCY

if HARDWARE_AVAILABLE:
    try:
        import RPi.GPIO as GPIO
    except ImportError:
        HARDWARE_AVAILABLE = False

class MotorController:
    """
    
    Differential drive motor controller
    
    """
    
    def __init__(self, left_pins: tuple = MOTOR_LEFT_PINS, 
                 right_pins: tuple = MOTOR_RIGHT_PINS,
                 pwm_freq: int = PWM_FREQUENCY):
        self.left_pins = left_pins
        self.right_pins = right_pins
        self.pwm_freq = pwm_freq
        
        self.left_pwm = None
        self.right_pwm = None
        
        if HARDWARE_AVAILABLE:
            self._initialize_gpio()
    
    def _initialize_gpio(self):
        """
        
        Initialize GPIO pins and PWM
        
        """
        GPIO.setmode(GPIO.BCM)
        
        # Setup motor pins
        for pin in self.left_pins + self.right_pins:
            GPIO.setup(pin, GPIO.OUT)
        
        # Initialize PWM
        self.left_pwm = GPIO.PWM(self.left_pins[0], self.pwm_freq)
        self.right_pwm = GPIO.PWM(self.right_pins[0], self.pwm_freq)
        
        # Start PWM with 0% duty cycle
        self.left_pwm.start(0)
        self.right_pwm.start(0)
        
        # Set direction pins to default
        GPIO.output(self.left_pins[1], GPIO.LOW)
        GPIO.output(self.right_pins[1], GPIO.LOW)
    
    def set_speeds(self, left_speed: float, right_speed: float):
        """

        Set motor speeds

        Args:
            left_speed: Speed from -100 to 100 (negative = reverse)
            right_speed: Speed from -100 to 100 (negative = reverse)


        """
        if not HARDWARE_AVAILABLE:
            # Print commands for debugging
            print(f"Motors: L={left_speed:.1f}, R={right_speed:.1f}")
            return
        
        # Clamp speeds to valid range
        left_speed = max(-100, min(100, left_speed))
        right_speed = max(-100, min(100, right_speed))
        
        # Set left motor
        if left_speed >= 0:
            GPIO.output(self.left_pins[1], GPIO.LOW)  # Forward
            self.left_pwm.ChangeDutyCycle(left_speed)
        else:
            GPIO.output(self.left_pins[1], GPIO.HIGH)  # Reverse
            self.left_pwm.ChangeDutyCycle(abs(left_speed))
        
        # Set right motor
        if right_speed >= 0:
            GPIO.output(self.right_pins[1], GPIO.LOW)  # Forward
            self.right_pwm.ChangeDutyCycle(right_speed)
        else:
            GPIO.output(self.right_pins[1], GPIO.HIGH)  # Reverse
            self.right_pwm.ChangeDutyCycle(abs(right_speed))
    
    def stop(self):
        """
        Stop both motors immediately
        """
        self.set_speeds(0, 0)
    
    def forward(self, speed: float = 50):
        """
        Move forward at specified speed
        """
        self.set_speeds(speed, speed)
    
    def backward(self, speed: float = 50):
        """
        Move backward at specified speed
        """
        self.set_speeds(-speed, -speed)
    
    def turn_left(self, speed: float = 50):
        """
        Turn left by running right motor forward, left motor backward
        """
        self.set_speeds(-speed, speed)
    
    def turn_right(self, speed: float = 50):
        """
        Turn right by running left motor forward, right motor backward
        """
        self.set_speeds(speed, -speed)
    
    def cleanup(self):
        """
        
        Cleanup GPIO resources
        
        """
        if HARDWARE_AVAILABLE and self.left_pwm and self.right_pwm:
            self.stop()
            time.sleep(0.1)
            self.left_pwm.stop()
            self.right_pwm.stop()
            GPIO.cleanup()