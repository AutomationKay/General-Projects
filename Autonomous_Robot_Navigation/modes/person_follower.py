# Logic for implementing person following

import time
import logging
from typing import Tuple
from utils.data_structures import SensorData, MotorCommand, RobotState
from utils.pid_controller import PIDController
from utils.data_logger import DataLogger
from sensors.camera import CameraInterface
from sensors.ultrasonic import UltrasonicSensor
from sensors.person_detector import PersonDetector
from motors.motor_controller import MotorController
from config import *

# Safe OpenCV import (drawing & GUI) 
try:
    import cv2
    _HAS_CV2 = True
except Exception:
    _HAS_CV2 = False


class PersonFollowingMode:
    """
    Person following mode implementation
    """

    def __init__(self):
        # Initialize hardware components
        self.camera = CameraInterface()
        self.ultrasonic = UltrasonicSensor()
        self.motors = MotorController()
        self.person_detector = PersonDetector()

        # Initialize control systems
        self.steering_pid = PIDController(**PID_STEERING)
        self.distance_pid = PIDController(**PID_DISTANCE)


        # Detection throttling (to help with performance)
        self._last_det = (False, None, 0.0)
        self._next_det_time = 0.0
        self._det_period = 0.20 # Seconds -> ~5 Hz


        # Initialize data logging
        self.data_logger = DataLogger("person_following_session")

        # Robot state
        self.state = RobotState(
            mode="person_following",
            is_running=False,
            person_lost_count=0,
            last_sensor_data=None,
            last_motor_command=None
        )

        # Track whether we are showing a window
        self.display_video = False

        # Setup logging
        logging.basicConfig(level=getattr(logging, LOG_LEVEL))
        self.logger = logging.getLogger(__name__)

        self.logger.info("Person Following Mode initialized")

    def get_sensor_data(self, frame) -> SensorData:
        """
        Collect and process all sensor data
        """
        # Cache actual frame size (This is to avoid relying on constants)
        self._frame_w = frame.shape[1]
        self._frame_h = frame.shape[0]

        # Get ultrasonic distance
        distance = self.ultrasonic.get_filtered_distance()

        # Detect person in frame
        now = time.time()
        if now >= self._next_det_time:
            person_detected, bbox, confidence = self.person_detector.detect_person(frame)
            self._last_det = (person_detected, bbox, confidence)
            self._next_det_time = now + self._det_period
        else:
            person_detected, bbox, confidence = self._last_det

        # Coerce bbox to pixel ints if present
        bbox_px = self._coerce_bbox(bbox, frame.shape)
        if not bbox_px:
            # If detector gave us a weird bbox, treat as "no detection"
            person_detected = False
            confidence = 0.0

        # Calculate person center if detected
        person_center_x = None
        if person_detected and bbox_px:
            x1, y1, x2, y2 = bbox_px
            person_center_x = (x1 + x2) // 2

            # Draw visualization on frame (only if cv2 is available)
            if _HAS_CV2:
                self._draw_detection(frame, bbox_px, confidence)

        # Create sensor data object
        sensor_data = SensorData(
            timestamp=time.time(),
            ultrasonic_distance=distance,
            person_detected=bool(person_detected and bbox_px),
            person_bbox=bbox_px,
            person_center_x=person_center_x,
            confidence=confidence if confidence is not None else 0.0,
        )
        return sensor_data

    def _draw_detection(self, frame, bbox, confidence):
        """
        Draw detection visualization on frame
        """
        if not _HAS_CV2 or not bbox:
            return
        
        x1, y1, x2, y2 = bbox
        # Draw bounding box
        color = (0, 255, 0) if (confidence or 0) > 0.7 else (0, 255, 255)
        cv2.rectangle(frame, (x1, y1), (x2, y2), color, 2)

        # Draw confidence label
        label = f"Person: {confidence:.2f}" if confidence is not None else "Person"
        cv2.putText(frame, label, (x1, max(0, y1 - 10)),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.5, color, 2)

    def _coerce_bbox(self, bbox, frame_shape):
        """
        Accepts many bbox formats and returns pixel (x1,y1,x2,y2) ints or None.
        Supports:
        - (x1,y1,x2,y2) pixels
        - (ymin,xmin,ymax,xmax) normalized [0..1]
        - [[...]] nested first detection
        - dicts with x1,y1,x2,y2 keys
        """
        if bbox is None:
            return None

        # Unwrap nested list/tuple: [ [..4..], ... ] -> first
        if isinstance(bbox, (list, tuple)):
            if len(bbox) == 0:
                return None
            if len(bbox) == 1 and isinstance(bbox[0], (list, tuple)):
                bbox = bbox[0]

        # Dict style
        if isinstance(bbox, dict):
            try:
                x1 = int(bbox["x1"]); y1 = int(bbox["y1"])
                x2 = int(bbox["x2"]); y2 = int(bbox["y2"])
                return (x1, y1, x2, y2)
            except Exception:
                return None

        if not (isinstance(bbox, (list, tuple)) and len(bbox) == 4):
            return None

        h, w = frame_shape[0], frame_shape[1]
        a, b, c, d = bbox

        # If values look normalized (0..1), assume (ymin, xmin, ymax, xmax)
        def _is_norm(v): 
            try: 
                return 0.0 <= float(v) <= 1.0
            except: 
                return False

        if all(_is_norm(v) for v in (a, b, c, d)):
            y1 = int(float(a) * h); x1 = int(float(b) * w)
            y2 = int(float(c) * h); x2 = int(float(d) * w)
        else:
            # Assume already in pixels, but could be (x1,y1,x2,y2) or (y1,x1,y2,x2)
            # Heuristic: treat as (x1,y1,x2,y2)
            x1 = int(a); y1 = int(b); x2 = int(c); y2 = int(d)

        # Normalize & clip
        x1, x2 = sorted((max(0, x1), min(w - 1, x2)))
        y1, y2 = sorted((max(0, y1), min(h - 1, y2)))

        # Discard degenerate boxes
        if x2 <= x1 or y2 <= y1:
            return None
        return (x1, y1, x2, y2)

    def calculate_motor_commands(self, sensor_data: SensorData) -> Tuple[float, float, str]:
        """
        Calculate motor commands based on sensor data
        """
        left_speed = right_speed = 0.0
        action = "stop"

        # Check if person is detected
        if not sensor_data.person_detected:
            self.state.person_lost_count += 1

            if self.state.person_lost_count < MAX_PERSON_LOST_FRAMES:
                # Search behavior - slow turn
                action = "search"
                left_speed = 25
                right_speed = -25
            else:
                # Stop after searching too long
                action = "stop"
                self.steering_pid.reset()
                self.distance_pid.reset()

            return left_speed, right_speed, action

        # Too far away - stop following
        if sensor_data.ultrasonic_distance > MAX_FOLLOW_DISTANCE:
            action = "out_of_range"
            self.steering_pid.reset()
            self.distance_pid.reset()
            return left_speed, right_speed, action

        # Calculate control outputs
        frame_w = getattr(self, "_frame_w", CAMERA_WIDTH)
        frame_center = frame_w // 2
        steering_error = (sensor_data.person_center_x - frame_center
                          if sensor_data.person_center_x is not None else 0)

        # PID control for steering and distance
        steering_correction = self.steering_pid.update(steering_error)
        base_speed = self.distance_pid.update(sensor_data.ultrasonic_distance)

        # Limit base speed
        base_speed = max(-MAX_SPEED, min(MAX_SPEED, base_speed))

        # Apply differential steering
        left_speed = max(-MAX_SPEED, min(MAX_SPEED, base_speed - 0.5 * steering_correction))
        right_speed = max(-MAX_SPEED, min(MAX_SPEED, base_speed + 0.5 * steering_correction))

        # Limit final motor speeds
        # left_speed = max(-MAX_SPEED, min(MAX_SPEED, left_speed))
        # right_speed = max(-MAX_SPEED, min(MAX_SPEED, right_speed))

        action = "follow"
        return left_speed, right_speed, action

    def run_mode(self, duration: int = 60, display_video: bool = False):
        """
        Run person following mode
        """
        self.display_video = bool(display_video)
        self.state.is_running = True
        start_time = time.time()
        frame_count = 0

        self.logger.info(f"Starting person following mode for {duration} seconds")
        self.data_logger.log_event("mode_started", {"duration": duration})

        try:
            while self.state.is_running and (time.time() - start_time) < duration:
                # Get camera frame
                frame = self.camera.get_frame()
                if frame is None:
                    time.sleep(0.05)
                    continue

                frame_count += 1

                # Process sensor data
                sensor_data = self.get_sensor_data(frame)
                self.state.last_sensor_data = sensor_data

                # Calculate motor commands
                left_speed, right_speed, action = self.calculate_motor_commands(sensor_data)

                # Execute motor commands
                self.motors.set_speeds(left_speed, right_speed)

                # Create motor command object
                motor_command = MotorCommand(
                    timestamp=time.time(),
                    left_speed=left_speed,
                    right_speed=right_speed,
                    action=action
                )
                self.state.last_motor_command = motor_command

                # Log data
                self.data_logger.log_sensor_data(sensor_data)
                self.data_logger.log_motor_command(motor_command)

                # Display frame if requested (dev mode)
                if self.display_video and _HAS_CV2:
                    self._display_frame(frame, sensor_data, motor_command)
                    key = cv2.waitKey(1) & 0xFF
                    if key in (27, ord('q')):  # ESC or q to quit preview
                        break


                # Log significant events
                if action == "backup" and (not hasattr(self, '_last_action') or self._last_action != "backup"):
                    self.data_logger.log_event("safety_backup", {"distance": sensor_data.ultrasonic_distance})

                if sensor_data.person_detected and self.state.person_lost_count == 0:
                    if not hasattr(self, '_person_detected_logged') or not self._person_detected_logged:
                        self.data_logger.log_event("person_detected", {"confidence": sensor_data.confidence})
                        self._person_detected_logged = True
                elif not sensor_data.person_detected:
                    self._person_detected_logged = False

                self._last_action = action

                # Control loop timing (20 FPS)
                time.sleep(0.05)

        except KeyboardInterrupt:
            self.logger.info("Interrupted by user")
            self.data_logger.log_event("user_interrupt")

        except Exception as e:
            self.logger.error(f"Error in person following mode: {e}")
            self.data_logger.log_event("error", {"error": str(e)})

        finally:
            self.stop_mode()
            self.logger.info(f"Mode completed. Processed {frame_count} frames")

    def _display_frame(self, frame, sensor_data, motor_command):
        """
        Display frame with overlay information for debugging
        """
        if not _HAS_CV2:
            return

        h, w = frame.shape[0], frame.shape[1]

        # Add information overlay
        info_text = [
            f"Distance: {sensor_data.ultrasonic_distance:.1f}cm",
            f"Person: {'Yes' if sensor_data.person_detected else 'No'}",
            f"Action: {motor_command.action}",
            f"Motors: L={motor_command.left_speed:.1f} R={motor_command.right_speed:.1f}"
        ]

        for i, text in enumerate(info_text):
            cv2.putText(frame, text, (10, 30 + i * 25),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 2)

        # Draw center line
        cv2.line(frame, (w // 2, 0), (w // 2, h), (0, 255, 0), 1)

        cv2.imshow("Person Following Debug", frame)

    def stop_mode(self):
        """
        Stop person following mode and cleanup
        """
        self.state.is_running = False
        self.motors.stop()

        # Save session data
        self.data_logger.log_event("mode_stopped")
        self.data_logger.save_session()

        self.logger.info("Person following mode stopped")

    def cleanup(self):
        """
        Cleanup all resources
        """
        # Clean up motors first so PWM stops even if later calls fail
        try:
            self.motors.cleanup()
        except Exception as e:
            self.logger.warning(f"Motor cleanup warning: {e}")

        # Release camera
        try:
            self.camera.release()
        except Exception as e:
            self.logger.warning(f"Camera release warning: {e}")

        # Close windows only if they were opened and cv2 is available
        if self.display_video and _HAS_CV2:
            try:
                cv2.destroyAllWindows()
            except Exception as e:
                self.logger.warning(f"cv2.destroyAllWindows warning: {e}")

        self.logger.info("Cleanup completed")
