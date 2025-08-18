# Implementation of the PID Controller for the robot

import time

class PIDController:
    """
    PID controller for smooth operation of robot

    """

    def __init__(self, kp: float, ki: float, kd: float, setpoint: float = 0):
        self.kp = kp
        self.ki = ki
        self.kd = kd
        self.setpoint = setpoint
        self.previous_error = 0
        self.integral = 0
        self.last_time = time.time()
        self.output_limits = (-100, 100) # Setting default limits

    
    def update(self, current_value: float) -> float:
        """
        
        Update PID controller and return control output
        
        
        """
        current_time = time.time()
        dt = current_time - self.last_time

        if dt <= 0:
            dt = 1e-6 
        
        error = self.setpoint - current_value
        self.integral += error * dt
        derivative = (error - self.previous_error) / dt

        # Calculate PID output
        output = (self.kp * error) + (self.ki * self.integral) + (self.kd * derivative)

        # Apply output limits
        output = max(self.output_limits[0], min(self.output_limits[1], output))

        # Update for next iteration
        self.previous_error = error
        self.last_time = current_time

        return output
    
    def set_limits(self, min_output: float, max_output: float):
        """
        
        Set output limits for the PID controller
        
        """

        self.output_limits = (min_output, max_output)
    
    def reset(self):
        """
        
        To reset the controller state
        
        """
        self.previous_error = 0
        self.integral = 0
        self.last_time = time.time()
    
