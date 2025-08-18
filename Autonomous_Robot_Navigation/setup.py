from picamera2 import Picamera2
import time, numpy as np

cam = Picamera2()
cfg = cam.create_video_configuration(main={"size": (640, 480), "format": "RGB888"})
cam.configure(cfg)
cam.start()
time.sleep(0.5)

for i in range(5):
    arr = cam.capture_array("main")
    print(i, arr.shape, arr.dtype, np.min(arr), np.max(arr))
cam.stop(); cam.close()