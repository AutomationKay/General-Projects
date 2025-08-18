# Person detection

import os
import cv2
import numpy as np
from typing import Tuple, Optional, List
from config import MODEL_PATH, PERSON_DETECTION_THRESHOLD


_tflite_kind = None

# Setting preference for tflight-runtime, fallback to TF's Interpreter
try:
    import tflite_runtime.interpreter as tflite
    _tflite_kind = "runtime"
except Exception:
    try:
        from tensorflow.lite.python.interpreter import Interpreter as TFInterpreter # type: ignore
        _tflite_kind = "tf"
    except Exception:
        _tflite_kind = None
        print("TensorFlow Lite not available - using fallback detection")


# Different models use different labels
# Some models use 0 for 'person', others use '1'
_PERSON_CLASS_IDS = {1}

class PersonDetector:
    """

    TFLite SSD MobileNet v2 COCO person detector.
    detect_person(frame_bgr) -> (found: bool, bbox: (x1,y1,x2,y2)|None, score: float|None)

    """

    def __init__(self, model_path: str = MODEL_PATH,
                 confidence_threshold: float = PERSON_DETECTION_THRESHOLD):
        self.model_path = model_path
        self.conf_th = float(confidence_threshold)
        self.interpreter = None
        self.input_index = None
        self.input_h = 300
        self.input_w = 300
        self._float_norm_mode = "0_1"
        self._norm_locked = False 
        self._quant = False  # uint8 vs float32

        # Fallback (motion) setup
        self.background_subtractor = cv2.createBackgroundSubtractorMOG2()

        self._load_model()

    def _load_model(self):
        if _tflite_kind is None or not os.path.exists(self.model_path):
            print("Using fallback person detection")
            return
        try:
            if _tflite_kind == "runtime":
                self.interpreter = tflite.Interpreter(self.model_path)
            else:
                self.interpreter = TFInterpreter(model_path=self.model_path)  # type: ignore
            self.interpreter.allocate_tensors()

            in_det = self.interpreter.get_input_details()[0]
            self.input_index = in_det["index"]
            ishape = in_det["shape"]
            if len(ishape) == 4:
                self.input_h, self.input_w = int(ishape[1]), int(ishape[2])
            else:
                self.input_h, self.input_w = 300, 300
            self._quant = (in_det["dtype"] == np.uint8)
            print(f"TensorFlow Lite model loaded. Input shape: [{self.input_h} {self.input_w}]")
        except Exception as e:
            print(f"Model loading failed: {e}")
            print("Falling back to computer vision detection")
            self.interpreter = None

    def detect_person(self, frame_bgr: np.ndarray) -> Tuple[bool, Optional[Tuple[int, int, int, int]], Optional[float]]:
        if self.interpreter is None:
            return self._fallback_detection(frame_bgr)
        return self._tflite_detection(frame_bgr)

    
    # ---------- TFLite path ----------
    #------------------------------------

    def comprehensive_person_test(self, frame_bgr):
        """
        Test person detection with multiple approaches and thresholds
        """
        if self.interpreter is None:
            print("No TensorFlow Lite interpreter loaded")
            return False, None, None
            
        print("=== Comprehensive Person Detection Test ===")
        
        # Test with very low threshold to see any non-background detections
        print("\n1. Testing with very low threshold (0.01)...")
        original_threshold = self.conf_th
        self.conf_th = 0.01
        
        # Run detection
        h, w = frame_bgr.shape[:2]
        inp = self._preprocess(frame_bgr, mode=self._float_norm_mode)
        self.interpreter.set_tensor(self.input_index, inp)
        self.interpreter.invoke()
        
        # Get raw outputs
        output_details = self.interpreter.get_output_details()
        boxes_raw = self.interpreter.get_tensor(output_details[0]["index"])
        logits_raw = self.interpreter.get_tensor(output_details[1]["index"])
        
        # Process outputs
        boxes = boxes_raw.squeeze()
        if boxes.ndim == 3:
            boxes = boxes.squeeze(axis=1)
        
        logits = logits_raw.squeeze(axis=0)
        logits_stable = logits - np.max(logits, axis=1, keepdims=True)
        exp_logits = np.exp(logits_stable)
        probabilities = exp_logits / np.sum(exp_logits, axis=1, keepdims=True)
        
        classes = np.argmax(probabilities, axis=1)
        scores = np.max(probabilities, axis=1)
        
        # Analyze all classes
        unique_classes, counts = np.unique(classes, return_counts=True)
        print(f"Class distribution:")
        for cls, count in zip(unique_classes, counts):
            max_score_for_class = scores[classes == cls].max()
            print(f"  Class {cls}: {count} detections, max score: {max_score_for_class:.4f}")
        
        # Look for non-background detections
        non_bg_mask = classes != 0
        non_bg_count = np.sum(non_bg_mask)
        print(f"\nNon-background detections: {non_bg_count}")
        
        if non_bg_count > 0:
            non_bg_classes = classes[non_bg_mask]
            non_bg_scores = scores[non_bg_mask]
            non_bg_boxes = boxes[non_bg_mask]
            
            # Sort by score
            sort_indices = np.argsort(non_bg_scores)[::-1]
            
            print(f"Top non-background detections:")
            for i in range(min(5, len(sort_indices))):
                idx = sort_indices[i]
                cls = non_bg_classes[idx]
                score = non_bg_scores[idx] 
                box = non_bg_boxes[idx]
                
                # Convert box to pixel coordinates (assuming normalized)
                if box.max() <= 1.0:  # Normalized coordinates
                    x1 = int(box[1] * w)  # Assuming [ymin, xmin, ymax, xmax]
                    y1 = int(box[0] * h)
                    x2 = int(box[3] * w) 
                    y2 = int(box[2] * h)
                else:  # Pixel coordinates
                    x1, y1, x2, y2 = map(int, box)
                
                print(f"  Class {cls}: score={score:.4f}, box=({x1},{y1},{x2},{y2})")
                
                # Check if this is a person
                if cls == 1:  # Standard COCO person class
                    print(f"    ✓ PERSON DETECTED!")
        
        # Test different normalization modes if no objects found
        if non_bg_count == 0:
            print(f"\n2. Testing different input normalization...")
            
            # Try [-1, 1] normalization
            print("  Trying [-1, 1] normalization...")
            inp_neg1_1 = self._preprocess(frame_bgr, mode="neg1_1")
            self.interpreter.set_tensor(self.input_index, inp_neg1_1)
            self.interpreter.invoke()
            
            logits_raw_2 = self.interpreter.get_tensor(output_details[1]["index"])
            logits_2 = logits_raw_2.squeeze(axis=0)
            
            # Quick check for different results
            logits_2_stable = logits_2 - np.max(logits_2, axis=1, keepdims=True)
            exp_logits_2 = np.exp(logits_2_stable)
            probabilities_2 = exp_logits_2 / np.sum(exp_logits_2, axis=1, keepdims=True)
            
            classes_2 = np.argmax(probabilities_2, axis=1)
            non_bg_count_2 = np.sum(classes_2 != 0)
            print(f"    Non-background detections with [-1,1]: {non_bg_count_2}")
            
            if non_bg_count_2 > non_bg_count:
                print(f"    ✓ [-1,1] normalization works better!")
                # Update the normalization mode
                self._float_norm_mode = "neg1_1"
                self._norm_locked = True
        
        # Test with original image preprocessing variations
        print(f"\n3. Testing image preprocessing variations...")
        
        # Test without normalization (if not quantized)
        if not self._quant:
            print("  Testing with raw uint8 input...")
            rgb = cv2.cvtColor(frame_bgr, cv2.COLOR_BGR2RGB)
            resized = cv2.resize(rgb, (self.input_w, self.input_h))
            inp_raw = np.expand_dims(resized.astype(np.float32), axis=0)
            
            self.interpreter.set_tensor(self.input_index, inp_raw)
            self.interpreter.invoke()
            
            logits_raw_3 = self.interpreter.get_tensor(output_details[1]["index"])
            logits_3 = logits_raw_3.squeeze(axis=0)
            
            logits_3_stable = logits_3 - np.max(logits_3, axis=1, keepdims=True)
            exp_logits_3 = np.exp(logits_3_stable)
            probabilities_3 = exp_logits_3 / np.sum(exp_logits_3, axis=1, keepdims=True)
            
            classes_3 = np.argmax(probabilities_3, axis=1)
            non_bg_count_3 = np.sum(classes_3 != 0)
            print(f"    Non-background detections with raw input: {non_bg_count_3}")
        
        # Final recommendation
        print(f"\n=== Test Results ===")
        if non_bg_count > 0:
            person_detections = np.sum((classes[non_bg_mask] == 1) & (scores[non_bg_mask] > 0.25))
            print(f"✓ Model is working - found {non_bg_count} object detections")
            print(f"✓ Found {person_detections} person detections above 0.25 confidence")
            if person_detections > 0:
                print(f"✓ PERSON DETECTION IS WORKING!")
            else:
                print(f"⚠️  No high-confidence person detections - try with a person in view")
        else:
            print(f"⚠️  No objects detected - possible issues:")
            print(f"   - No person/objects in camera view")
            print(f"   - Model input preprocessing incorrect")
            print(f"   - Model expects different input format")
            print(f"   - Camera image quality issues")
        
        # Restore original threshold
        self.conf_th = original_threshold
        
        return non_bg_count > 0, None, None

    # Also add a simple test with a person in view
    def test_with_person_instructions(self):
        """Print instructions for testing with a person"""
        print("=== Person Detection Test Instructions ===")
        print("1. Position yourself or someone in front of the camera")
        print("2. Make sure there's good lighting")
        print("3. Stand at a reasonable distance (2-10 feet)")
        print("4. Run the comprehensive test again")
        print("5. The person should be clearly visible and not too close/far")
        print("\nOptimal conditions:")
        print("- Good lighting (not backlit)")  
        print("- Person fills 10-50% of frame")
        print("- Clear background")
        print("- Person is upright and visible")

    def analyze_class_mapping(self, frame_bgr, min_confidence=0.1):
        """

        Analyze what classes the model actually detects to 
        understand the class mapping. This is mostly for 
        advanced debugging and data analysis.


        """
        if self.interpreter is None:
            print("No TensorFlow Lite interpreter loaded")
            return
            
        h, w = frame_bgr.shape[:2]
        inp = self._preprocess(frame_bgr, mode=self._float_norm_mode)
        self.interpreter.set_tensor(self.input_index, inp)
        self.interpreter.invoke()
        
        # Get outputs using existing method
        boxes, classes, scores, num = self._extract_outputs()
        
        if boxes is None or classes is None or scores is None:
            print("Could not extract outputs")
            return
        
        # Analyze all detections above minimum confidence
        class_stats = {}
        for i in range(len(scores)):
            score = float(scores[i])
            if score < min_confidence:
                continue
                
            cls = int(round(float(classes[i])))
            if cls not in class_stats:
                class_stats[cls] = {'count': 0, 'scores': [], 'max_score': 0}
            
            class_stats[cls]['count'] += 1
            class_stats[cls]['scores'].append(score)
            class_stats[cls]['max_score'] = max(class_stats[cls]['max_score'], score)
        
        print(f"Class analysis (confidence >= {min_confidence}):")
        print(f"{'Class':<6} {'Count':<6} {'Max Score':<10} {'Avg Score':<10} {'Likely Object'}")
        print("-" * 60)
        
        # Common COCO class names for reference
        coco_classes = {
            0: "background",
            1: "person", 
            2: "bicycle", 
            3: "car", 
            4: "motorcycle",
            5: "airplane",
            16: "bird",
            17: "cat", 
            18: "dog",
            # ... there are 91 total COCO classes
        }
        
        for cls in sorted(class_stats.keys()):
            stats = class_stats[cls]
            avg_score = sum(stats['scores']) / len(stats['scores'])
            likely_obj = coco_classes.get(cls, "unknown")
            
            print(f"{cls:<6} {stats['count']:<6} {stats['max_score']:<10.3f} {avg_score:<10.3f} {likely_obj}")
        
        # Special analysis for person detection
        if 1 in class_stats:
            person_stats = class_stats[1] 
            print(f"\n✓ Person class (1) found: {person_stats['count']} detections")
            print(f"  Max confidence: {person_stats['max_score']:.3f}")
            print(f"  Avg confidence: {sum(person_stats['scores'])/len(person_stats['scores']):.3f}")
        else:
            print(f"\n⚠️  No person class (1) detections above {min_confidence} confidence")
            
        # Recommend class IDs to use
        high_confidence_classes = {cls for cls, stats in class_stats.items() 
                                if stats['max_score'] > 0.7 and cls != 0}  # Exclude background
        
        if high_confidence_classes:
            print(f"\nRecommended person class IDs based on high confidence detections:")
            print(f"_PERSON_CLASS_IDS = {{{', '.join(map(str, sorted(high_confidence_classes)))}}}")
        
        return class_stats

    def _preprocess(self, frame_bgr: np.ndarray, mode: str = "0_1") -> np.ndarray:
        # BGR -> RGB, resize to model input
        rgb = cv2.cvtColor(frame_bgr, cv2.COLOR_BGR2RGB)
        resized = cv2.resize(rgb, (self.input_w, self.input_h), interpolation=cv2.INTER_LINEAR)
        if self._quant:
            return np.expand_dims(resized.astype(np.int8), axis=0)
        if mode == "neg1_1":
            inp = ((resized.astype(np.float32) - 127.5) / 127.5).astype(np.float32)
        else:
            inp = (resized.astype(np.float32) / 255.0).astype(np.float32)
        return np.expand_dims(inp, axis=0)

    def _extract_outputs(self):
        """
        Extract outputs for SSD MobileNet v2 with format:
        - Output 0: (1, 1917, 1, 4) - bounding boxes
        - Output 1: (1, 1917, 91) - class logits
        """
        output_details = self.interpreter.get_output_details()
        
        if len(output_details) != 2:
            print(f"Warning: Expected 2 outputs, got {len(output_details)}")
            return None, None, None, None
        
        # Get the raw outputs
        boxes_raw = self.interpreter.get_tensor(output_details[0]["index"])  # (1, 1917, 1, 4)
        logits_raw = self.interpreter.get_tensor(output_details[1]["index"])  # (1, 1917, 91)
        
        # Process boxes: (1, 1917, 1, 4) -> (1917, 4)
        boxes = boxes_raw.squeeze()  # Remove dimensions of size 1
        if boxes.ndim == 3:  # Still has extra dimension
            boxes = boxes.squeeze(axis=1)
        
        # Process logits to get scores and classes
        # logits_raw shape: (1, 1917, 91)
        logits = logits_raw.squeeze(axis=0)  # (1917, 91)
        
        # Convert logits to probabilities using softmax
        # Subtract max for numerical stability
        logits_stable = logits - np.max(logits, axis=1, keepdims=True)
        exp_logits = np.exp(logits_stable)
        probabilities = exp_logits / np.sum(exp_logits, axis=1, keepdims=True)
        
        # Get the class with highest probability and its score for each detection
        classes = np.argmax(probabilities, axis=1).astype(np.float32)
        scores = np.max(probabilities, axis=1).astype(np.float32)
        
        # Filter out background class (class 0) detections
        non_background_mask = classes != 0
        
        if np.any(non_background_mask):
            boxes = boxes[non_background_mask]
            classes = classes[non_background_mask] 
            scores = scores[non_background_mask]
            num = len(scores)
            
            print(f"Debug: Found {num} non-background detections out of {len(non_background_mask)} total")
            print(f"Debug: Non-background classes: {np.unique(classes)}")
            print(f"Debug: Score range: [{scores.min():.3f}, {scores.max():.3f}]")
        else:
            print("Debug: All detections were background class (0)")
            return None, None, None, 0
        
        return boxes, classes, scores, num

    def _postprocess(self, boxes, classes, scores, num, frame_h, frame_w):
        """Updated postprocess method with better debugging"""
        if boxes is None or classes is None or scores is None:
            print("Debug: One or more outputs is None")
            return False, None, 0.0

        n = min(len(scores), len(boxes), len(classes))
        if num is not None:
            n = min(n, int(num))

        print(f"Debug: Processing {n} detections with threshold {self.conf_th}")

        best_score, best_box = -1.0, None
        valid_detections = 0
        person_detections = 0
        
        for i in range(n):
            sc = float(scores[i])
            if sc < self.conf_th:
                continue
                
            cls = int(round(float(classes[i])))
            
            # Only process person class (Class 1)
            if cls != 1:  # Skip non-person detections
                continue
                
            person_detections += 1
            
            # Get box coordinates - try different interpretations
            box_coords = [float(v) for v in boxes[i]]
            
            # Debug the raw coordinates
            print(f"Debug: Detection {i} raw coords: {box_coords}")
            
            # The coordinates seem to be already in a format that needs interpretation
            # Let's try different common formats for SSD MobileNet:
            
            # Format 1: [ymin, xmin, ymax, xmax] normalized
            if all(-2 <= coord <= 2 for coord in box_coords):  # Reasonable normalized range
                ymin, xmin, ymax, xmax = box_coords
                
                # Clamp to valid range
                ymin = max(0, min(1, ymin))
                xmin = max(0, min(1, xmin))
                ymax = max(0, min(1, ymax)) 
                xmax = max(0, min(1, xmax))
                
                # Convert to pixel coordinates
                x1 = int(xmin * frame_w)
                y1 = int(ymin * frame_h)
                x2 = int(xmax * frame_w)
                y2 = int(ymax * frame_h)
                
            # Format 2: Already in pixel coordinates but need bounds checking
            else:
                # Assume [ymin, xmin, ymax, xmax] in pixels
                ymin, xmin, ymax, xmax = box_coords
                
                x1 = int(max(0, min(frame_w - 1, xmin)))
                y1 = int(max(0, min(frame_h - 1, ymin)))
                x2 = int(max(0, min(frame_w - 1, xmax)))
                y2 = int(max(0, min(frame_h - 1, ymax)))
            
            # Ensure valid box dimensions
            if x2 <= x1 or y2 <= y1:
                print(f"Debug: Invalid box dimensions: ({x1},{y1},{x2},{y2})")
                continue
                
            # Ensure reasonable box size (not too small or too large)
            box_width = x2 - x1
            box_height = y2 - y1
            box_area = box_width * box_height
            frame_area = frame_w * frame_h
            
            if box_area < (frame_area * 0.001):  # Too small (less than 0.1% of frame)
                print(f"Debug: Box too small: {box_area} pixels")
                continue
                
            if box_area > (frame_area * 0.8):  # Too large (more than 80% of frame)
                print(f"Debug: Box too large: {box_area} pixels")
                continue
            
            valid_detections += 1
            print(f"Debug: Valid person detection {i}: score={sc:.3f}, box=({x1},{y1},{x2},{y2})")
            
            if sc > best_score:
                best_score, best_box = sc, (x1, y1, x2, y2)
        
        print(f"Debug: {person_detections} person detections above threshold")
        print(f"Debug: {valid_detections} valid person detections after filtering")
        
        if best_box is not None:
            print(f"Debug: Returning best person detection with score {best_score:.3f}")
            return True, best_box, best_score
        
        print("Debug: No valid person detections found")
        return False, None, 0.0

    def _extract_outputs(self):
        """
        Improved extract outputs with better error handling
        """
        output_details = self.interpreter.get_output_details()
        
        if len(output_details) != 2:
            print(f"Warning: Expected 2 outputs, got {len(output_details)}")
            return None, None, None, None
        
        # Get the raw outputs
        boxes_raw = self.interpreter.get_tensor(output_details[0]["index"])
        logits_raw = self.interpreter.get_tensor(output_details[1]["index"])
        
        # Process boxes: (1, 1917, 1, 4) -> (1917, 4)
        boxes = boxes_raw.squeeze()
        if boxes.ndim == 3:
            boxes = boxes.squeeze(axis=1)
        
        # Process logits to get scores and classes
        logits = logits_raw.squeeze(axis=0)  # (1917, 91)
        
        # Convert logits to probabilities using softmax
        logits_stable = logits - np.max(logits, axis=1, keepdims=True)
        exp_logits = np.exp(logits_stable)
        probabilities = exp_logits / np.sum(exp_logits, axis=1, keepdims=True)
        
        # Get the class with highest probability and its score for each detection
        classes = np.argmax(probabilities, axis=1).astype(np.float32)
        scores = np.max(probabilities, axis=1).astype(np.float32)
        
        # Filter to only person detections (Class 1) above a minimum score
        person_mask = (classes == 1) & (scores > 0.1)  # Very low threshold for initial filtering
        
        if np.any(person_mask):
            boxes = boxes[person_mask]
            classes = classes[person_mask]
            scores = scores[person_mask]
            num = len(scores)
            
            print(f"Debug: Found {num} person detections above 0.1 confidence")
            print(f"Debug: Score range: [{scores.min():.3f}, {scores.max():.3f}]")
        else:
            print("Debug: No person detections found")
            return None, None, None, 0
        
        return boxes, classes, scores, num
    
    def _tflite_detection(self, frame_bgr: np.ndarray) -> Tuple[bool, Optional[Tuple[int, int, int, int]], Optional[float]]:
        h, w = frame_bgr.shape[:2]

        def run_detection(mode):
            inp = self._preprocess(frame_bgr, mode=mode)
            self.interpreter.set_tensor(self.input_index, inp)
            self.interpreter.invoke()
            boxes, classes, scores, num = self._extract_outputs()
            
            if boxes is None or len(boxes) == 0:
                return False, None, None, 0.0
                
            found, box, score = self._postprocess(boxes, classes, scores, num, h, w)
            top_score = float(score) if found else 0.0
            return found, box, score, top_score

        # If quantized, just run once
        if self._quant:
            found, box, score, _ = run_detection("0_1")
            return (found, box, score) if found else (False, None, None)

        # If normalization is already locked, use that mode
        if self._norm_locked:
            found, box, score, _ = run_detection(self._float_norm_mode)
            return (found, box, score) if found else (False, None, None)

        # Try both normalization modes and pick the better one
        print("Debug: Testing both normalization modes...")
        
        # Try [0, 1] normalization first
        found1, box1, score1, top1 = run_detection("0_1")
        print(f"Debug: [0,1] normalization - found: {found1}, top_score: {top1:.3f}")
        
        # Try [-1, 1] normalization
        found2, box2, score2, top2 = run_detection("neg1_1")
        print(f"Debug: [-1,1] normalization - found: {found2}, top_score: {top2:.3f}")
        
        # Choose the better result
        if found2 and (not found1 or top2 > top1):
            print("Debug: Using [-1,1] normalization")
            self._float_norm_mode = "neg1_1"
            if top2 >= 0.30:  # Lock if confident
                self._norm_locked = True
            return True, box2, score2
        elif found1:
            print("Debug: Using [0,1] normalization") 
            self._float_norm_mode = "0_1"
            if top1 >= 0.30:  # Lock if confident
                self._norm_locked = True
            return True, box1, score1
        else:
            # Neither worked well, keep trying different modes
            print("Debug: No good detections found")
            return False, None, None
    def advanced_debug_peek(self, frame_bgr, k=10):
        """
        Advanced diagnostic method to understand model behavior
        """
        if self.interpreter is None:
            print("No TensorFlow Lite interpreter loaded")
            return
            
        h, w = frame_bgr.shape[:2]
        inp = self._preprocess(frame_bgr, mode=self._float_norm_mode)
        self.interpreter.set_tensor(self.input_index, inp)
        self.interpreter.invoke()
        
        # Get raw outputs
        output_details = self.interpreter.get_output_details()
        boxes_raw = self.interpreter.get_tensor(output_details[0]["index"])
        logits_raw = self.interpreter.get_tensor(output_details[1]["index"])
        
        print(f"Raw logits stats:")
        print(f"  Shape: {logits_raw.shape}")
        print(f"  Min: {logits_raw.min():.3f}, Max: {logits_raw.max():.3f}")
        print(f"  Mean: {logits_raw.mean():.3f}, Std: {logits_raw.std():.3f}")
        
        # Look at logits for first few detections
        logits = logits_raw.squeeze(axis=0)  # (1917, 91)
        
        print(f"\nFirst few detection logits (raw):")
        for i in range(min(5, logits.shape[0])):
            detection_logits = logits[i]
            top_indices = np.argsort(detection_logits)[::-1][:5]
            print(f"  Detection {i} top 5 classes:")
            for j, idx in enumerate(top_indices):
                print(f"    Class {idx}: {detection_logits[idx]:.3f}")
        
        # Check if logits are already normalized (softmax applied)
        print(f"\nChecking if logits are pre-normalized:")
        for i in range(min(3, logits.shape[0])):
            row_sum = np.sum(np.exp(logits[i] - np.max(logits[i])))
            normalized_sum = np.sum(np.exp(logits[i] - np.max(logits[i])) / row_sum)
            print(f"  Detection {i}: sum of exp(logits) = {row_sum:.6f}")
            print(f"  Detection {i}: sum of softmax = {normalized_sum:.6f}")
        
        # Check for potential issues
        print(f"\nDiagnostic checks:")
        
        # Check if all logits are the same (would indicate model issue)
        if np.allclose(logits[0], logits[1], atol=1e-6):
            print("  ⚠️  WARNING: First two detections have identical logits!")
        else:
            print("  ✓ Logits vary between detections")
        
        # Check class distribution in raw logits
        max_classes = np.argmax(logits, axis=1)
        unique_classes, counts = np.unique(max_classes, return_counts=True)
        print(f"  Class distribution (top class per detection):")
        for cls, count in zip(unique_classes, counts):
            print(f"    Class {cls}: {count} detections ({count/len(max_classes)*100:.1f}%)")
        
        # Check if there's a dominant class that's always winning
        if len(unique_classes) == 1:
            print(f"  ⚠️  WARNING: All detections predict same class ({unique_classes[0]})")
            
            # Check if this class has abnormally high logits
            class_logits = logits[:, unique_classes[0]]
            other_logits = np.delete(logits, unique_classes[0], axis=1)
            print(f"    Dominant class logits: mean={class_logits.mean():.3f}, std={class_logits.std():.3f}")
            print(f"    Other class logits: mean={other_logits.mean():.3f}, std={other_logits.std():.3f}")
            print(f"    Difference in means: {class_logits.mean() - other_logits.mean():.3f}")
        
        # Now let's see what happens with softmax
        print(f"\nAfter softmax processing:")
        logits_stable = logits - np.max(logits, axis=1, keepdims=True)
        exp_logits = np.exp(logits_stable)
        probabilities = exp_logits / np.sum(exp_logits, axis=1, keepdims=True)
        
        classes = np.argmax(probabilities, axis=1)
        scores = np.max(probabilities, axis=1)
        
        print(f"  Probability scores range: [{scores.min():.6f}, {scores.max():.6f}]")
        print(f"  Mean probability score: {scores.mean():.6f}")
        
        # Show distribution of max probabilities
        high_conf = np.sum(scores > 0.9)
        med_conf = np.sum((scores > 0.5) & (scores <= 0.9))
        low_conf = np.sum(scores <= 0.5)
        print(f"  Confidence distribution:")
        print(f"    High (>0.9): {high_conf} ({high_conf/len(scores)*100:.1f}%)")
        print(f"    Medium (0.5-0.9): {med_conf} ({med_conf/len(scores)*100:.1f}%)")
        print(f"    Low (≤0.5): {low_conf} ({low_conf/len(scores)*100:.1f}%)")
        
        # Check top detections
        top_indices = np.argsort(scores)[::-1][:k]
        print(f"\nTop {k} detections after softmax:")
        for i in top_indices:
            print(f"  Detection {i}: class={classes[i]}, score={scores[i]:.6f}")
            # Show the raw logits for this detection
            detection_logits = logits[i]
            top_logit_indices = np.argsort(detection_logits)[::-1][:3]
            print(f"    Raw logits - top 3: {[(idx, detection_logits[idx]) for idx in top_logit_indices]}")

# Add this method to your PersonDetector class


    # ---------- Fallback path ----------
    #------------------------------------

    def _fallback_detection(self, frame_bgr: np.ndarray):
        # Very simple motion/person-ish fallback
        gray = cv2.cvtColor(frame_bgr, cv2.COLOR_BGR2GRAY)
        fg = self.background_subtractor.apply(frame_bgr)
        kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (5, 5))
        fg = cv2.morphologyEx(fg, cv2.MORPH_CLOSE, kernel)
        fg = cv2.morphologyEx(fg, cv2.MORPH_OPEN, kernel)

        contours, _ = cv2.findContours(fg, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        h, w = frame_bgr.shape[:2]
        min_area = (w * h) * 0.01
        max_area = (w * h) * 0.80

        best, best_area = None, 0.0
        for c in contours:
            area = cv2.contourArea(c)
            if not (min_area < area < max_area):
                continue
            x, y, ww, hh = cv2.boundingRect(c)
            ar = hh / ww if ww > 0 else 0
            if 1.2 < ar < 4.0 and area > best_area:
                best, best_area = (x, y, x + ww, y + hh), area

        if best is not None:
            conf = min(0.9, best_area / max_area)
            return True, best, conf
        return False, None, None
