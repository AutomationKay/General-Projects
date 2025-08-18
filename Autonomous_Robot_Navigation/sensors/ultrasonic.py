# Ultrasonic sensor interface 

import time
import numpy as np
from config import HARDWARE_AVAILABLE, ULTRASONIC_TRIGGER_PIN, ULTRASONIC_ECHO_PIN

# Check to see if hardware is available or in simulation mode
if HARDWARE_AVAILABLE:
    try:
        import RPi.GPIO as GPIO
    except ImportError:
        HARDWARE_AVAILABLE = False

class UltrasonicSensor:
    """
    
    HC-SR04 Ultrasonic sensor interface
    
    """
    
    def __init__(self, trigger_pin: int = ULTRASONIC_TRIGGER_PIN, 
                 echo_pin: int = ULTRASONIC_ECHO_PIN):
        self.trigger_pin = trigger_pin
        self.echo_pin = echo_pin
        
        if HARDWARE_AVAILABLE:
            GPIO.setmode(GPIO.BCM)
            GPIO.setup(self.trigger_pin, GPIO.OUT)
            GPIO.setup(self.echo_pin, GPIO.IN)
            GPIO.output(self.trigger_pin, False)
            time.sleep(0.1)  # Settle time
    
    def get_distance(self) -> float:
        """

        Get distance measurement in centimeters
        
        Returns:
             999.0 for timeout/error conditions

        """
        if not HARDWARE_AVAILABLE:
            # Simulate realistic distance readings for testing
            return max(30, np.random.normal(120, 20))
        
        try:
            # Send 10µs trigger pulse
            GPIO.output(self.trigger_pin, True)
            time.sleep(0.00001)
            GPIO.output(self.trigger_pin, False)
            
            # Measure echo duration with timeout
            timeout = time.time() + 0.1  # 100ms timeout
            
            # Wait for echo start
            while GPIO.input(self.echo_pin) == 0 and time.time() < timeout:
                pulse_start = time.time()
            
            if time.time() >= timeout:
                return 999.0
            
            # Wait for echo end
            while GPIO.input(self.echo_pin) == 1 and time.time() < timeout:
                pulse_end = time.time()
            
            if time.time() >= timeout:
                return 999.0
            
            # Calculate distance (speed of sound = 34300 cm/s)
            pulse_duration = pulse_end - pulse_start
            distance = (pulse_duration * 34300) / 2
            
            # Return reasonable values only
            return distance if 2 <= distance <= 400 else 999.0
            
        except Exception as e:
            print(f"Ultrasonic sensor error: {e}")
            return 999.0
    
    def get_filtered_distance(self, samples: int = 3) -> float:
        """
        
        Get median filtered distance reading
        
        """
        readings = []
        for _ in range(samples):
            reading = self.get_distance()
            if reading < 999.0:
                readings.append(reading)
            time.sleep(0.01)  # Small delay between readings
        
        if not readings:
            return 999.0
        
        readings.sort()
        return readings[len(readings) // 2]  # Return median