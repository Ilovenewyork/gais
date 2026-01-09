import sys
import json
import cv2
import time
import numpy as np
import mediapipe as mp
import pyautogui

# Try to import EyeTrax
try:
    from eyetrax import GazeEstimator, run_9_point_calibration
    EYETRAX_AVAILABLE = True
except ImportError:
    EYETRAX_AVAILABLE = False
    sys.stderr.write("Warning: eyetrax not found. Gaze tracking will be simulated/zeros.\n")

# Configuration
EAR_THRESHOLD = 0.22      # Eye Aspect Ratio threshold for blink
LONG_BLINK_DURATION = 0.4 # Seconds to count as a "long" blink (click)
SMOOTHING_FACTOR = 0.15   # Lower = smoother but more lag (0.1 to 0.5 recommended)
DEADZONE = 2              # Pixels to ignore for micro-movements

# Safe-fail and speed
pyautogui.FAILSAFE = False
pyautogui.PAUSE = 0

class EyeTracker:
    def __init__(self):
        # Initialize MediaPipe Face Mesh for Blink Detection
        self.mp_face_mesh = mp.solutions.face_mesh
        self.face_mesh = self.mp_face_mesh.FaceMesh(
            max_num_faces=1,
            refine_landmarks=True,
            min_detection_confidence=0.5,
            min_tracking_confidence=0.5
        )
        
        # Initialize EyeTrax
        self.estimator = None
        if EYETRAX_AVAILABLE:
            try:
                self.estimator = GazeEstimator()
            except Exception as e:
                sys.stderr.write(f"Error initializing EyeTrax: {e}\n")

        self.cap = cv2.VideoCapture(0)
        
        # State
        self.blink_start_left = 0
        self.blink_start_right = 0
        self.click_triggered_left = False
        self.click_triggered_right = False
        self.calibrated = False
        
        # Smoothing State
        self.smooth_x = 0
        self.smooth_y = 0
        self.last_mouse_x = 0
        self.last_mouse_y = 0
        
        # Control State
        self.tracking_active = False
        self.calibration_requested = False
        
        # Start Input Thread
        import threading
        self.input_thread = threading.Thread(target=self.read_input, daemon=True)
        self.input_thread.start()

    def read_input(self):
        while True:
            try:
                line = sys.stdin.readline()
                if not line:
                    break
                cmd = line.strip()
                if cmd == "CALIBRATE":
                    self.calibration_requested = True
                elif cmd == "START":
                    self.tracking_active = True
                    sys.stderr.write("Tracking Started\n")
                elif cmd == "STOP":
                    self.tracking_active = False
                    sys.stderr.write("Tracking Stopped\n")
            except Exception:
                break

    def calibrate(self):
        if EYETRAX_AVAILABLE and self.estimator:
            sys.stderr.write("Starting Calibration...\n")
            # Signal calibration start
            print(json.dumps({"type": "calibration_event", "status": "start"}))
            sys.stdout.flush()
            
            try:
                # Release camera before calibration to avoid resource contention
                if self.cap.isOpened():
                    self.cap.release()
                
                # This opens a CV2 window
                run_9_point_calibration(self.estimator)
                self.calibrated = True
                sys.stderr.write("Calibration Complete.\n")

            except Exception as e:
                sys.stderr.write(f"Calibration failed: {e}\n")
            
            finally:
                # Re-initialize camera after calibration
                if not self.cap.isOpened():
                    self.cap = cv2.VideoCapture(0)
                    if not self.cap.isOpened():
                        sys.stderr.write("Critical: Failed to re-open camera after calibration.\n")
                
                # Signal calibration end
                print(json.dumps({"type": "calibration_event", "status": "end"}))
                sys.stdout.flush()


    def calculate_ear(self, landmarks, indices, w, h):
        points = [np.array([landmarks[i].x * w, landmarks[i].y * h]) for i in indices]
        v1 = np.linalg.norm(points[1] - points[5])
        v2 = np.linalg.norm(points[2] - points[4])
        h_dist = np.linalg.norm(points[0] - points[3])
        if h_dist == 0: return 0.0
        return (v1 + v2) / (2.0 * h_dist)

    def run(self):
        # Removed auto-calibration
        # if EYETRAX_AVAILABLE and self.estimator:
        #     self.calibrate()

        screen_w, screen_h = pyautogui.size()

        while True:
            # Handle Calibration Request on Main Thread (CV2 GUI needs main thread often)
            if self.calibration_requested:
                self.calibrate()
                self.calibration_requested = False

            success, image = self.cap.read()
            if not success:
                time.sleep(0.01)
                continue

            h, w, _ = image.shape
            
            # 1. Gaze Tracking
            gaze_x, gaze_y = 0, 0
            if EYETRAX_AVAILABLE and self.estimator:
                try:
                    features, blink = self.estimator.extract_features(image)
                    if features is not None and not blink and self.calibrated:
                        pred = self.estimator.predict([features])
                        raw_x, raw_y = pred[0]
                        
                        # Apply smoothing (Exponential Moving Average)
                        if self.smooth_x == 0 and self.smooth_y == 0:
                            self.smooth_x, self.smooth_y = raw_x, raw_y
                        else:
                            self.smooth_x = self.smooth_x * (1 - SMOOTHING_FACTOR) + raw_x * SMOOTHING_FACTOR
                            self.smooth_y = self.smooth_y * (1 - SMOOTHING_FACTOR) + raw_y * SMOOTHING_FACTOR
                        
                        gaze_x, gaze_y = int(self.smooth_x), int(self.smooth_y)
                        
                        # Move Mouse ONLY if active and outside deadzone
                        if self.tracking_active:
                            dx = abs(gaze_x - self.last_mouse_x)
                            dy = abs(gaze_y - self.last_mouse_y)
                            
                            if dx >= DEADZONE or dy >= DEADZONE:
                                pyautogui.moveTo(gaze_x, gaze_y)
                                self.last_mouse_x, self.last_mouse_y = gaze_x, gaze_y
                    else:
                         # sys.stderr.write("Features None or Blink detected\n")
                         pass
                except Exception as e:
                    sys.stderr.write(f"Gaze error: {e}\n")
            
            # 2. Blink Detection
            image_rgb = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
            image_rgb.flags.writeable = False
            results = self.face_mesh.process(image_rgb)
            
            blink_left = False
            blink_right = False
            ear_left = 0.0
            ear_right = 0.0
            
            if results.multi_face_landmarks:
                for face_landmarks in results.multi_face_landmarks:
                    lm = face_landmarks.landmark
                    ear_left = self.calculate_ear(lm, [33, 160, 158, 133, 153, 144], w, h)
                    ear_right = self.calculate_ear(lm, [362, 385, 387, 263, 373, 380], w, h)
                    
                    if ear_left < EAR_THRESHOLD: blink_left = True
                    if ear_right < EAR_THRESHOLD: blink_right = True

            # 3. Process Clicks ONLY if active
            if self.tracking_active:
                curr_time = time.time()
                
                # Left Click Logic
                if blink_left:
                    if self.blink_start_left == 0:
                        self.blink_start_left = curr_time
                    elif (curr_time - self.blink_start_left) > LONG_BLINK_DURATION:
                        if not self.click_triggered_left:
                            pyautogui.click(button='left')
                            self.click_triggered_left = True
                            sys.stderr.write("Left Click\n")
                else:
                    self.blink_start_left = 0
                    self.click_triggered_left = False
                
                # Right Click Logic
                if blink_right:
                    if self.blink_start_right == 0:
                        self.blink_start_right = curr_time
                    elif (curr_time - self.blink_start_right) > LONG_BLINK_DURATION:
                        if not self.click_triggered_right:
                            pyautogui.click(button='right')
                            self.click_triggered_right = True
                            sys.stderr.write("Right Click\n")
                else:
                    self.blink_start_right = 0
                    self.click_triggered_right = False

            # 4. Output Data for UI
            payload = {
                "x": float(gaze_x),
                "y": float(gaze_y),
                "blink_left": self.click_triggered_left,
                "blink_right": self.click_triggered_right,
                "raw_ear_left": ear_left,
                "raw_ear_right": ear_right,
                "active": self.tracking_active
            }
            
            print(json.dumps(payload))
            sys.stdout.flush()

if __name__ == "__main__":
    tracker = EyeTracker()
    tracker.run()
