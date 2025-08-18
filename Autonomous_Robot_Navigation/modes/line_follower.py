# Line following mode implementation code 

import cv2
import numpy as np
import time
import logging
from typing import Tuple, Optional, List
from utils.data_structures import SensorData, MotorCommand, RobotState, LineData
from utils.pid_controller import PIDController
from utils.data_logger import DataLogger
from sensors.camera import CameraInterface
from motors.motor_controller import MotorController
from config import *


class IRSensorArray:
    """
    Infrared sensor array for line detection
    """
    
    def __init__(self, sensor_pins: List[int] = None):
        if sensor_pins is None:
            sensor_pins = [IR01, IR02, IR03]  # Left, Center, Right
        
        self.sensor_pins = sensor_pins
        self.num_sensors = len(sensor_pins)
        self.sensor_values = [0] * self.num_sensors
        
        # Initialize GPIO if available
        if GPIO_AVAILABLE:
            GPIO.setmode(GPIO.BCM)
            for pin in self.sensor_pins:
                GPIO.setup(pin, GPIO.IN)
        
        # Sensor positioning weights for line center calculation
        # Assumes sensors are evenly spaced: [-1, 0, 1] for 3 sensors
        self.sensor_weights = list(range(-self.num_sensors//2 + 1, self.num_sensors//2 + 2))
        if self.num_sensors % 2 == 0:
            self.sensor_weights = [w - 0.5 for w in self.sensor_weights]
        
        self.logger = logging.getLogger(__name__)
        self.logger.info(f"IR sensor array initialized with pins: {sensor_pins}")
    
    def read_sensors(self) -> List[int]:
        """
        Read all IR sensors
        Returns: List of sensor values (1 = line detected, 0 = no line)
        """
        if GPIO_AVAILABLE:
            # Read actual GPIO pins
            # Note: IR sensors typically output LOW when line is detected (for black line)
            # Adjust the logic based on your specific IR sensor behavior
            for i, pin in enumerate(self.sensor_pins):
                # Invert reading if your IR sensors are active LOW for line detection
                self.sensor_values[i] = 1 - GPIO.input(pin)
        else:
            # Simulate sensor readings for testing without hardware
            # This would normally not be here in production code
            import random
            self.sensor_values = [random.choice([0, 1]) for _ in range(self.num_sensors)]
        
        return self.sensor_values.copy()
    
    def get_line_position(self, sensor_values: List[int] = None) -> Tuple[float, int, bool]:
        """
        Calculate line position from sensor readings
        
        Returns:
            position: Line position (-1.0 to 1.0, 0 = center)
            active_sensors: Number of sensors detecting line
            line_detected: Whether any line is detected
        """
        if sensor_values is None:
            sensor_values = self.read_sensors()
        
        active_sensors = sum(sensor_values)
        
        if active_sensors == 0:
            return 0.0, 0, False
        
        # Calculate weighted position
        weighted_sum = sum(weight * value for weight, value in zip(self.sensor_weights, sensor_values))
        position = weighted_sum / active_sensors
        
        # Normalize to -1.0 to 1.0 range
        max_position = max(abs(min(self.sensor_weights)), abs(max(self.sensor_weights)))
        normalized_position = position / max_position
        
        return normalized_position, active_sensors, True
    
    def cleanup(self):
        """Cleanup GPIO resources"""
        if GPIO_AVAILABLE:
            GPIO.cleanup()

class HybridLineData(LineData):
    """
    Extended LineData class that includes IR sensor information
    """
    
    def __init__(self, timestamp: float, line_detected: bool, line_center_x: Optional[int],
                 line_angle: Optional[float], line_width: Optional[int], confidence: float,
                 contour_area: Optional[float], ir_position: float, ir_active_sensors: int,
                 ir_line_detected: bool, sensor_values: List[int]):
        super().__init__(timestamp, line_detected, line_center_x, line_angle, 
                        line_width, confidence, contour_area)
        
        # IR sensor data
        self.ir_position = ir_position
        self.ir_active_sensors = ir_active_sensors
        self.ir_line_detected = ir_line_detected
        self.sensor_values = sensor_values.copy()
        
        # Combined detection result
        self.combined_line_detected = line_detected or ir_line_detected

class EnhancedLineDetector:
    """
    Enhanced line detector combining computer vision and IR sensors
    """
    
    def __init__(self, line_color: str = "black", min_area: int = 500, use_ir_sensors: bool = True):
        # Initialize computer vision detector
        self.cv_detector = LineDetector(line_color=line_color, min_area=min_area)
        
        # Initialize IR sensor array
        self.use_ir_sensors = use_ir_sensors
        if use_ir_sensors:
            self.ir_sensors = IRSensorArray()
        else:
            self.ir_sensors = None
        
        # Fusion parameters
        self.cv_weight = 0.7  # Weight for computer vision
        self.ir_weight = 0.3  # Weight for IR sensors
        self.ir_pixel_range = 100  # Convert IR position to pixel range
        
        self.logger = logging.getLogger(__name__)
    
    def detect_line(self, frame: np.ndarray) -> HybridLineData:
        """
        Detect line using both computer vision and IR sensors
        """
        timestamp = time.time()
        
        # Get computer vision detection
        cv_line_data = self.cv_detector.detect_line(frame)
        
        # Get IR sensor data
        ir_position = 0.0
        ir_active_sensors = 0
        ir_line_detected = False
        sensor_values = [0, 0, 0]
        
        if self.use_ir_sensors and self.ir_sensors:
            sensor_values = self.ir_sensors.read_sensors()
            ir_position, ir_active_sensors, ir_line_detected = self.ir_sensors.get_line_position(sensor_values)
        
        # Combine the two detection methods
        combined_center_x = self._fuse_line_position(cv_line_data, ir_position, frame.shape[1])
        combined_confidence = self._calculate_combined_confidence(cv_line_data, ir_active_sensors)
        
        return HybridLineData(
            timestamp=timestamp,
            line_detected=cv_line_data.line_detected,
            line_center_x=combined_center_x,
            line_angle=cv_line_data.line_angle,
            line_width=cv_line_data.line_width,
            confidence=combined_confidence,
            contour_area=cv_line_data.contour_area,
            ir_position=ir_position,
            ir_active_sensors=ir_active_sensors,
            ir_line_detected=ir_line_detected,
            sensor_values=sensor_values
        )
    
    def _fuse_line_position(self, cv_data: LineData, ir_position: float, frame_width: int) -> Optional[int]:
        """
        Fuse computer vision and IR sensor line position estimates
        """
        if cv_data.line_detected and self.ir_sensors and abs(ir_position) > 0.1:
            # Both sources available - weighted fusion
            cv_center_norm = (cv_data.line_center_x - frame_width/2) / (frame_width/2) if cv_data.line_center_x else 0
            
            # Weighted average of normalized positions
            fused_position_norm = (self.cv_weight * cv_center_norm + self.ir_weight * ir_position)
            
            # Convert back to pixel coordinates
            return int(frame_width/2 + fused_position_norm * frame_width/2)
        
        elif cv_data.line_detected:
            # Only computer vision available
            return cv_data.line_center_x
        
        elif self.ir_sensors and abs(ir_position) > 0.1:
            # Only IR sensors available
            return int(frame_width/2 + ir_position * self.ir_pixel_range)
        
        else:
            # No reliable detection
            return None
    
    def _calculate_combined_confidence(self, cv_data: LineData, ir_active_sensors: int) -> float:
        """
        Calculate combined confidence from both detection methods
        """
        cv_confidence = cv_data.confidence if cv_data.line_detected else 0.0
        ir_confidence = min(1.0, ir_active_sensors / 2.0)  # Normalize based on number of active sensors
        
        # Weighted combination
        combined_confidence = self.cv_weight * cv_confidence + self.ir_weight * ir_confidence
        
        return min(1.0, combined_confidence)
    
    def cleanup(self):
        """Cleanup resources"""
        if self.ir_sensors:
            self.ir_sensors.cleanup()

# Update the original LineDetector class to maintain compatibility
class LineDetector:
    """
    Computer vision-based line detection (original implementation)
    """
    
    def __init__(self, line_color: str = "black", min_area: int = 500):
        self.line_color = line_color.lower()
        self.min_area = min_area
        
        # Color thresholds for different line types
        self.color_ranges = {
            "black": {"lower": np.array([0, 0, 0]), "upper": np.array([180, 255, 80])},
            "white": {"lower": np.array([0, 0, 200]), "upper": np.array([180, 30, 255])},
            "red": {"lower": np.array([0, 120, 70]), "upper": np.array([10, 255, 255])},
            "blue": {"lower": np.array([100, 50, 50]), "upper": np.array([130, 255, 255])},
            "green": {"lower": np.array([40, 50, 50]), "upper": np.array([80, 255, 255])},
        }
        
        # Image processing parameters
        self.gaussian_blur_kernel = (5, 5)
        self.morphology_kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (3, 3))
        
        # Region of Interest (focus on lower portion of frame)
        self.roi_height_ratio = 0.6  # Use bottom 60% of frame
    
    def detect_line(self, frame: np.ndarray) -> LineData:
        """
        Detect line in the frame
        Returns: LineData object with detection results
        """
        timestamp = time.time()
        height, width = frame.shape[:2]
        
        # Define Region of Interest (ROI)
        roi_start_y = int(height * (1 - self.roi_height_ratio))
        roi = frame[roi_start_y:height, 0:width]
        
        # Process frame for line detection
        processed_roi = self._preprocess_frame(roi)
        
        # Find line contours
        contours, hierarchy = cv2.findContours(
            processed_roi, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE
        )
        
        # Filter and find best line contour
        best_contour = self._find_best_line_contour(contours, roi.shape)
        
        if best_contour is not None:
            # Calculate line properties
            line_center_x, line_angle, line_width, confidence, area = self._calculate_line_properties(
                best_contour, roi.shape, roi_start_y
            )
            
            # Draw visualization
            self._draw_line_detection(frame, best_contour, roi_start_y, line_center_x)
            
            return LineData(
                timestamp=timestamp,
                line_detected=True,
                line_center_x=line_center_x,
                line_angle=line_angle,
                line_width=line_width,
                confidence=confidence,
                contour_area=area
            )
        else:
            return LineData(
                timestamp=timestamp,
                line_detected=False,
                line_center_x=None,
                line_angle=None,
                line_width=None,
                confidence=0.0,
                contour_area=None
            )
    
    def _preprocess_frame(self, roi: np.ndarray) -> np.ndarray:
        """
        Preprocess frame for line detection
        """
        if self.line_color in ["black", "white"]:
            # Convert to grayscale for black/white lines
            gray = cv2.cvtColor(roi, cv2.COLOR_BGR2GRAY)
            
            if self.line_color == "black":
                # Threshold for black line on white background
                _, binary = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU)
            else:  # white line
                _, binary = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
        else:
            # Use HSV color space for colored lines
            hsv = cv2.cvtColor(roi, cv2.COLOR_BGR2HSV)
            color_range = self.color_ranges.get(self.line_color, self.color_ranges["black"])
            binary = cv2.inRange(hsv, color_range["lower"], color_range["upper"])
        
        # Apply Gaussian blur to reduce noise
        blurred = cv2.GaussianBlur(binary, self.gaussian_blur_kernel, 0)
        
        # Morphological operations to clean up the binary image
        cleaned = cv2.morphologyEx(blurred, cv2.MORPH_CLOSE, self.morphology_kernel)
        cleaned = cv2.morphologyEx(cleaned, cv2.MORPH_OPEN, self.morphology_kernel)
        
        return cleaned
    
    def _find_best_line_contour(self, contours: List, roi_shape: Tuple) -> Optional[np.ndarray]:
        """
        Find the best contour representing the line
        """
        if not contours:
            return None
        
        roi_height, roi_width = roi_shape[:2]
        best_contour = None
        best_score = 0
        
        for contour in contours:
            area = cv2.contourArea(contour)
            
            # Filter by minimum area
            if area < self.min_area:
                continue
            
            # Calculate bounding rectangle
            x, y, w, h = cv2.boundingRect(contour)
            
            # Check aspect ratio (lines should be wider than tall for horizontal lines)
            aspect_ratio = w / h if h > 0 else 0
            
            # Score based on area and aspect ratio
            # Prefer larger areas and reasonable aspect ratios
            if aspect_ratio > 1.5:  # Horizontal line preference
                score = area * min(aspect_ratio / 5.0, 1.0)  # Cap aspect ratio bonus
                
                # Bonus for lines closer to bottom of ROI (more immediate path)
                center_y = y + h / 2
                bottom_proximity = (roi_height - center_y) / roi_height
                score *= (1 + bottom_proximity * 0.5)
                
                if score > best_score:
                    best_score = score
                    best_contour = contour
        
        return best_contour
    
    def _calculate_line_properties(self, contour: np.ndarray, roi_shape: Tuple, 
                                 roi_offset_y: int) -> Tuple[int, float, int, float, float]:
        """
        Calculate line properties from contour
        """
        # Get contour moments for centroid calculation
        M = cv2.moments(contour)
        
        if M["m00"] != 0:
            # Calculate centroid in ROI coordinates
            cx_roi = int(M["m10"] / M["m00"])
            cy_roi = int(M["m01"] / M["m00"])
            
            # Convert to full frame coordinates
            line_center_x = cx_roi
        else:
            # Fallback to bounding box center
            x, y, w, h = cv2.boundingRect(contour)
            line_center_x = x + w // 2
            cy_roi = y + h // 2
        
        # Calculate line angle using fitted line
        try:
            [vx, vy, x, y] = cv2.fitLine(contour, cv2.DIST_L2, 0, 0.01, 0.01)
            line_angle = np.arctan2(vy, vx) * 180 / np.pi
        except:
            line_angle = 0.0
        
        # Calculate line width (approximate)
        x, y, w, h = cv2.boundingRect(contour)
        line_width = min(w, h)  # Use smaller dimension as width
        
        # Calculate confidence based on contour properties
        area = cv2.contourArea(contour)
        perimeter = cv2.arcLength(contour, True)
        
        if perimeter > 0:
            # Compactness measure (4π*Area/Perimeter²)
            compactness = (4 * np.pi * area) / (perimeter * perimeter)
            confidence = min(1.0, compactness * 2)  # Scale and cap at 1.0
        else:
            confidence = 0.5
        
        return line_center_x, line_angle, line_width, confidence, area
    
    def _draw_line_detection(self, frame: np.ndarray, contour: np.ndarray, 
                           roi_offset_y: int, line_center_x: int):
        """
        Draw line detection visualization on frame
        """
        height, width = frame.shape[:2]
        
        # Adjust contour coordinates to full frame
        adjusted_contour = contour.copy()
        adjusted_contour[:, :, 1] += roi_offset_y
        
        # Draw contour
        cv2.drawContours(frame, [adjusted_contour], -1, (0, 255, 0), 2)
        
        # Draw line center
        center_y = roi_offset_y + height // 4  # Draw at quarter from bottom
        cv2.circle(frame, (line_center_x, center_y), 5, (0, 255, 255), -1)
        
        # Draw center reference line
        cv2.line(frame, (width//2, 0), (width//2, height), (255, 0, 0), 1)
        
        # Draw ROI boundary
        cv2.line(frame, (0, roi_offset_y), (width, roi_offset_y), (255, 255, 0), 1)

class EnhancedLineFollowingMode:
    """
    Enhanced line following mode with IR sensor integration
    """
    
    def __init__(self, line_color: str = "black", use_ir_sensors: bool = True):
        # Initialize hardware components
        self.camera = CameraInterface()
        self.motors = MotorController()
        self.line_detector = EnhancedLineDetector(line_color=line_color, use_ir_sensors=use_ir_sensors)
        
        # Initialize control system
        # More aggressive PID for line following
        self.steering_pid = PIDController(kp=1.2, ki=0.2, kd=0.8, setpoint=CAMERA_WIDTH//2)
        
        # IR-only PID controller for when camera fails
        self.ir_steering_pid = PIDController(kp=0.8, ki=0.1, kd=0.6, setpoint=0.0)  # IR position target is 0
        
        # Initialize data logging
        self.data_logger = DataLogger("enhanced_line_following_session")
        
        # Robot state
        self.state = RobotState(
            mode="enhanced_line_following",
            is_running=False,
            person_lost_count=0,  # Reuse as line_lost_count
            last_sensor_data=None,
            last_motor_command=None
        )
        
        # Line following parameters
        self.base_speed = 40  # Base forward speed
        self.ir_only_base_speed = 35  # Slower speed when using IR only
        self.max_steering_correction = 60  # Maximum steering correction
        self.line_lost_threshold = 30  # Frames before stopping (increased for IR backup)
        self.search_speed = 25  # Speed during line search
        
        # Detection mode tracking
        self.detection_mode = "hybrid"  # "hybrid", "cv_only", "ir_only"
        self.mode_switch_threshold = 10  # Frames before switching modes
        self.cv_fail_count = 0
        self.ir_fail_count = 0
        
        # Setup logging
        logging.basicConfig(level=getattr(logging, LOG_LEVEL))
        self.logger = logging.getLogger(__name__)
        
        self.logger.info(f"Enhanced Line Following Mode initialized for {line_color} line with IR sensors: {use_ir_sensors}")
    
    def get_line_data(self, frame: np.ndarray) -> HybridLineData:
        """
        Process frame and get enhanced line detection data
        """
        return self.line_detector.detect_line(frame)
    
    def _determine_detection_mode(self, line_data: HybridLineData):
        """
        Dynamically determine which detection method to prioritize
        """
        # Track detection failures
        if not line_data.line_detected:
            self.cv_fail_count += 1
        else:
            self.cv_fail_count = 0
        
        if not line_data.ir_line_detected:
            self.ir_fail_count += 1
        else:
            self.ir_fail_count = 0
        
        # Switch detection mode based on reliability
        if self.cv_fail_count > self.mode_switch_threshold and line_data.ir_line_detected:
            self.detection_mode = "ir_only"
        elif self.ir_fail_count > self.mode_switch_threshold and line_data.line_detected:
            self.detection_mode = "cv_only"
        elif line_data.line_detected and line_data.ir_line_detected:
            self.detection_mode = "hybrid"
        # Otherwise maintain current mode
    
    def calculate_motor_commands(self, line_data: HybridLineData) -> Tuple[float, float, str]:
        """
        Calculate motor commands using enhanced line detection
        """
        left_speed = 0.0
        right_speed = 0.0
        action = "stop"
        
        # Determine detection mode
        self._determine_detection_mode(line_data)
        
        # Check if any line is detected
        line_available = line_data.combined_line_detected
        
        if not line_available:
            self.state.person_lost_count += 1  # Reusing as line_lost_count
            
            if self.state.person_lost_count < self.line_lost_threshold:
                # Search behavior - continue forward slowly and turn slightly
                action = f"search_{self.detection_mode}"
                left_speed = self.search_speed
                right_speed = self.search_speed * 0.7  # Slight right bias for search
            else:
                # Stop after searching too long
                action = "line_lost"
                self.steering_pid.reset()
                self.ir_steering_pid.reset()
            
            return left_speed, right_speed, action
        
        # Line detected - reset lost counter
        self.state.person_lost_count = 0
        
        # Calculate steering correction based on detection mode
        if self.detection_mode == "ir_only" and line_data.ir_line_detected:
            # Use IR sensors only
            steering_error = self.ir_steering_pid.update(line_data.ir_position)
            current_base_speed = self.ir_only_base_speed
            action = "following_ir"
            
        elif self.detection_mode == "cv_only" and line_data.line_detected:
            # Use computer vision only
            steering_error = self.steering_pid.update(line_data.line_center_x)
            current_base_speed = self.base_speed
            action = "following_cv"
            
        else:
            # Hybrid mode - use fused position
            if line_data.line_center_x is not None:
                steering_error = self.steering_pid.update(line_data.line_center_x)
                current_base_speed = self.base_speed
                action = "following_hybrid"
            else:
                # Fallback to IR if fused position is None
                steering_error = self.ir_steering_pid.update(line_data.ir_position)
                current_base_speed = self.ir_only_base_speed
                action = "following_ir_fallback"
        
        # Limit steering correction
        steering_correction = max(-self.max_steering_correction, 
                                min(self.max_steering_correction, steering_error))
        
        # Apply differential steering with speed reduction for sharp turns
        speed_reduction = min(0.7, abs(steering_correction) / self.max_steering_correction)
        adjusted_base_speed = current_base_speed * (1 - speed_reduction * 0.3)
        
        left_speed = adjusted_base_speed - steering_correction
        right_speed = adjusted_base_speed + steering_correction
        
        # Ensure minimum forward motion
        min_forward_speed = 15
        if left_speed < min_forward_speed and right_speed < min_forward_speed:
            left_speed = max(left_speed, min_forward_speed)
            right_speed = max(right_speed, min_forward_speed)
        
        return left_speed, right_speed, action
    
    def run_mode(self, duration: int = 60, display_video: bool = False):
        """
        Run enhanced line following mode
        """
        self.state.is_running = True
        start_time = time.time()
        frame_count = 0
        
        self.logger.info(f"Starting enhanced line following mode for {duration} seconds")
        self.data_logger.log_event("mode_started", {
            "duration": duration, 
            "line_color": self.line_detector.cv_detector.line_color,
            "base_speed": self.base_speed,
            "ir_sensors_enabled": self.line_detector.use_ir_sensors
        })
        
        try:
            while self.state.is_running and (time.time() - start_time) < duration:
                # Get camera frame
                frame = self.camera.get_frame()
                if frame is None:
                    time.sleep(0.05)
                    continue
                
                frame_count += 1
                
                # Process line detection (hybrid)
                line_data = self.get_line_data(frame)
                
                # Calculate motor commands
                left_speed, right_speed, action = self.calculate_motor_commands(line_data)
                
                # Execute motor commands
                self.motors.set_speeds(left_speed, right_speed)
                
                # Create motor command object
                motor_command = MotorCommand(
                    timestamp=time.time(),
                    left_speed=left_speed,
                    right_speed=right_speed,
                    action=action
                )
                
                # Log enhanced sensor data
                enhanced_sensor_data = SensorData(
                    timestamp=line_data.timestamp,
                    ultrasonic_distance=0,  # Not used in line following
                    person_detected=line_data.combined_line_detected,  # Combined detection result
                    person_bbox=None,
                    person_center_x=line_data.line_center_x,
                    confidence=line_data.confidence
                )
                
                self.data_logger.log_sensor_data(enhanced_sensor_data)
                self.data_logger.log_motor_command(motor_command)
                
                # Log IR-specific data
                self.data_logger.log_event("ir_sensor_data", {
                    "ir_position": line_data.ir_position,
                    "ir_active_sensors": line_data.ir_active_sensors,
                    "ir_line_detected": line_data.ir_line_detected,
                    "sensor_values": line_data.sensor_values,
                    "detection_mode": self.detection_mode
                })
                
                # Log standard line data
                self.data_logger.log_event("line_data", {
                    "cv_line_detected": line_data.line_detected,
                    "line_angle": line_data.line_angle,
                    "line_width": line_data.line_width,
                    "contour_area": line_data.contour_area,
                    "combined_confidence": line_data.confidence
                })
                
                # Display frame if requested (for development)
                if display_video and not HARDWARE_AVAILABLE:
                    self._display_frame(frame, line_data, motor_command)
                    if cv2.waitKey(1) & 0xFF == ord('q'):
                        break
                
                # Log significant events
                if action == "line_lost" and (not hasattr(self, '_last_action') or self._last_action != "line_lost"):
                    self.data_logger.log_event("line_lost", {
                        "lost_count": self.state.person_lost_count,
                        "detection_mode": self.detection_mode
                    })
                
                if line_data.combined_line_detected and self.state.person_lost_count == 0:
                    if not hasattr(self, '_line_detected_logged') or not self._line_detected_logged:
                        self.data_logger.log_event("line_reacquired", {
                            "confidence": line_data.confidence,
                            "detection_mode": self.detection_mode
                        })
                        self._line_detected_logged = True
                elif not line_data.combined_line_detected:
                    self._line_detected_logged = False
                
                # Log mode switches
                if hasattr(self, '_last_detection_mode') and self._last_detection_mode != self.detection_mode:
                    self.data_logger.log_event("detection_mode_switch", {
                        "from_mode": self._last_detection_mode,
                        "to_mode": self.detection_mode,
                        "cv_fail_count": self.cv_fail_count,
                        "ir_fail_count": self.ir_fail_count
                    })
                
                self._last_action = action
                self._last_detection_mode = self.detection_mode
                
                # Control loop timing (20 FPS)
                time.sleep(0.05)
        
        except KeyboardInterrupt:
            self.logger.info("Interrupted by user")
            self.data_logger.log_event("user_interrupt")
        
        except Exception as e:
            self.logger.error(f"Error in enhanced line following mode: {e}")
            self.data_logger.log_event("error", {"error": str(e)})
        
        finally:
            self.stop_mode()
            self.logger.info(f"Enhanced mode completed. Processed {frame_count} frames")
    
    def _display_frame(self, frame, line_data: HybridLineData, motor_command):
        """
        Display frame with enhanced overlay information for debugging
        """
        # Add information overlay
        info_text = [
            f"CV Line: {'Yes' if line_data.line_detected else 'No'}",
            f"IR Line: {'Yes' if line_data.ir_line_detected else 'No'}",
            f"Mode: {self.detection_mode}",
            f"Center X: {line_data.line_center_x or 'N/A'}",
            f"IR Pos: {line_data.ir_position:.2f}",
            f"IR Sensors: {line_data.sensor_values}",
            f"Active: {line_data.ir_active_sensors}",
            f"Confidence: {line_data.confidence:.2f}",
            f"Action: {motor_command.action}",
            f"Motors: L={motor_command.left_speed:.1f} R={motor_command.right_speed:.1f}"
        ]
        
        # Choose text color based on detection mode
        text_color = {
            "hybrid": (255, 255, 255),     # White
            "cv_only": (0, 255, 255),      # Yellow
            "ir_only": (255, 0, 255)       # Magenta
        }.get(self.detection_mode, (255, 255, 255))
        
        for i, text in enumerate(info_text):
            cv2.putText(frame, text, (10, 25 + i*22), 
                       cv2.FONT_HERSHEY_SIMPLEX, 0.5, text_color, 2)
        
        # Draw IR sensor positions (if available)
        if line_data.ir_line_detected and self.line_detector.ir_sensors:
            self._draw_ir_sensor_overlay(frame, line_data)
        
        cv2.imshow("Enhanced Line Following Debug", frame)
    
    def _draw_ir_sensor_overlay(self, frame, line_data: HybridLineData):
        """
        Draw IR sensor visualization on frame
        """
        height, width = frame.shape[:2]
        
        # Draw sensor positions at bottom of frame
        sensor_y = height - 30
        sensor_spacing = width // (len(line_data.sensor_values) + 1)
        
        for i, sensor_value in enumerate(line_data.sensor_values):
            x_pos = sensor_spacing * (i + 1)
            
            # Draw sensor circle
            color = (0, 255, 0) if sensor_value else (0, 0, 255)  # Green if active, red if inactive
            cv2.circle(frame, (x_pos, sensor_y), 8, color, -1)
            
            # Label sensors
            label = f"IR{i+1}"
            cv2.putText(frame, label, (x_pos - 15, sensor_y + 20), 
                       cv2.FONT_HERSHEY_SIMPLEX, 0.4, (255, 255, 255), 1)
        
        # Draw IR-calculated line position
        if abs(line_data.ir_position) > 0.1:
            ir_pixel_pos = int(width/2 + line_data.ir_position * 100)  # Convert to pixel position
            cv2.circle(frame, (ir_pixel_pos, sensor_y - 40), 6, (255, 0, 255), -1)
            cv2.putText(frame, "IR Line", (ir_pixel_pos - 25, sensor_y - 45), 
                       cv2.FONT_HERSHEY_SIMPLEX, 0.4, (255, 0, 255), 1)
    
    def stop_mode(self):
        """
        Stop enhanced line following mode and cleanup
        """
        self.state.is_running = False
        self.motors.stop()
        
        # Save session data
        self.data_logger.log_event("mode_stopped", {
            "final_detection_mode": self.detection_mode,
            "total_cv_failures": self.cv_fail_count,
            "total_ir_failures": self.ir_fail_count
        })
        self.data_logger.save_session()
        
        self.logger.info("Enhanced line following mode stopped")
    
    def cleanup(self):
        """
        Cleanup all resources including IR sensors
        """
        self.camera.release()
        self.motors.cleanup()
        self.line_detector.cleanup()  # This will cleanup IR sensors
        cv2.destroyAllWindows()
        self.logger.info("Enhanced cleanup completed")

# Maintain backward compatibility - create alias for original class
class LineFollowingMode(EnhancedLineFollowingMode):
    """
    Backward compatibility wrapper for the original LineFollowingMode
    """
    
    def __init__(self, line_color: str = "black"):
        # Initialize with IR sensors enabled by default
        super().__init__(line_color=line_color, use_ir_sensors=True)
        self.logger.info("LineFollowingMode initialized with IR sensor enhancement")

# Usage example and testing functions
def test_ir_sensors():
    """
    Test IR sensor array functionality
    """
    print("Testing IR Sensor Array...")
    
    # Initialize IR sensors
    ir_sensors = IRSensorArray()
    
    try:
        for i in range(10):
            # Read sensors
            values = ir_sensors.read_sensors()
            position, active, detected = ir_sensors.get_line_position(values)
            
            print(f"Iteration {i+1}:")
            print(f"  Sensor Values: {values}")
            print(f"  Line Position: {position:.2f}")
            print(f"  Active Sensors: {active}")
            print(f"  Line Detected: {detected}")
            print()
            
            time.sleep(0.5)
    
    except KeyboardInterrupt:
        print("Test interrupted by user")
    
    finally:
        ir_sensors.cleanup()

def run_enhanced_line_following():
    """
    Main function to run enhanced line following mode
    """
    # Initialize enhanced line following mode
    line_follower = EnhancedLineFollowingMode(line_color="black", use_ir_sensors=True)
    
    try:
        # Run for 60 seconds with video display for debugging
        line_follower.run_mode(duration=60, display_video=True)
    
    except KeyboardInterrupt:
        print("Program interrupted by user")
    
    finally:
        line_follower.cleanup()

if __name__ == "__main__":
    # Uncomment the function based on what's going to be ran:
    
    # Test IR sensors only
    # test_ir_sensors()
    
    # Run enhanced line following
    run_enhanced_line_following()