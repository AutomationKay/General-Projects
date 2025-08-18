# Interface for Camera


import cv2
import numpy as np
import time
import logging
from typing import Optional
from config import HARDWARE_AVAILABLE, CAMERA_WIDTH, CAMERA_HEIGHT

try:
    from picamera2 import Picamera2
    PICAMERA2_AVAILABLE = True
    print("picamera2 imported successfully")
except ImportError as e:
    print(f"picamera2 import failed: {e}")
    PICAMERA2_AVAILABLE = False


class CameraInterface:
    """Camera interface supporting Pi Camera (primary) and USB webcams (fallback)."""

    def __init__(self, width: int = CAMERA_WIDTH, height: int = CAMERA_HEIGHT):
        self.width = width
        self.height = height
        self.camera = None
        self.is_pi_camera = False
        self.logger = logging.getLogger(__name__)
        self.initialize_camera()

    def initialize_camera(self):
        """Initialize Pi camera first; fallback to USB."""
        # --- Pi Camera (Picamera2) path ---
        if PICAMERA2_AVAILABLE:
            try:
                self.logger.info("Initializing Pi Camera (Picamera2)...")
                print("Picamera2 init...")
                self.camera = Picamera2()
                cfg = self.camera.create_video_configuration(
                    main={"size": (self.width, self.height), "format": "RGB888"}
                )
                self.camera.configure(cfg)
                self.camera.start()
                time.sleep(0.2)  # warm-up
                test = self.camera.capture_array("main")
                if test is not None and test.size > 0:
                    self.is_pi_camera = True
                    print(f"Pi AI Camera initialized: {test.shape}")
                    self.logger.info("Pi AI Camera initialized successfully")
                    return
                raise RuntimeError("Picamera2 test capture returned empty frame")
            except Exception as e:
                self.logger.error(f"Picamera2 failed: {e}")
                print(f"Picamera2 failed: {e}")
                if self.camera:
                    try:
                        self.camera.stop()
                        self.camera.close()
                    except Exception:
                        pass
                self.camera = None

        # --- USB camera fallback ---
        print("Falling back to USB camera...")
        try:
            self.logger.info("Attempting USB camera...")
            opened = False
            for idx in (0, 1, 2):
                cap = cv2.VideoCapture(idx, cv2.CAP_V4L2)
                if cap.isOpened():
                    self.camera = cap
                    opened = True
                    print(f"Found USB camera at index {idx}")
                    break
                cap.release()

            if not opened:
                raise RuntimeError("Could not open any USB camera")

            # Configure USB camera
            self.camera.set(cv2.CAP_PROP_FRAME_WIDTH, self.width)
            self.camera.set(cv2.CAP_PROP_FRAME_HEIGHT, self.height)
            self.camera.set(cv2.CAP_PROP_FPS, 30)
            ok, test = self.camera.read()
            if ok and test is not None:
                self.is_pi_camera = False
                print(f"USB Camera initialized: {test.shape}")
                self.logger.info("USB Camera initialized successfully")
                return
            raise RuntimeError("USB camera test capture failed")
        except Exception as e:
            self.logger.error(f"USB camera failed: {e}")
            print(f"USB Camera failed: {e}")
            if self.camera:
                self.camera.release()
            self.camera = None

        print("ERROR: No working camera found!")
        self.logger.error("No working camera found")

    def get_frame(self) -> Optional[np.ndarray]:
        """Capture a frame as BGR (OpenCV-friendly)."""
        if not self.camera:
            return None
        try:
            if self.is_pi_camera:
                rgb = self.camera.capture_array("main")
                if rgb is None or rgb.size == 0:
                    return None
                return cv2.cvtColor(rgb, cv2.COLOR_RGB2BGR)
            else:
                ok, frame = self.camera.read()
                return frame if ok and frame is not None else None
        except Exception as e:
            self.logger.error(f"Camera capture error: {e}")
            print(f"Camera capture error: {e}")
            return None

    def release(self):
        """Release camera resources."""
        if self.camera:
            try:
                if self.is_pi_camera:
                    self.camera.stop()
                    self.camera.close()
                    print("Pi AI Camera released")
                else:
                    self.camera.release()
                    print("USB Camera released")
            except Exception as e:
                self.logger.error(f"Error releasing camera: {e}")
                print(f"Error releasing camera: {e}")
            finally:
                self.camera = None

    def is_available(self) -> bool:
        return self.camera is not None

    def get_camera_info(self) -> dict:
        return {
            "available": self.is_available(),
            "type": "Pi AI Camera" if self.is_pi_camera else "USB Camera",
            "width": self.width,
            "height": self.height,
            "picamera2_available": PICAMERA2_AVAILABLE,
            "hardware_available": HARDWARE_AVAILABLE,
        }
