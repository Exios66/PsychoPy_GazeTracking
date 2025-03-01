# Scripts/gaze_tracking.py
import numpy as np
import os
import json
import logging
import traceback
from datetime import datetime

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('gaze_tracking')

# Try to import optional dependencies
try:
    import matplotlib.pyplot as plt
    MATPLOTLIB_AVAILABLE = True
except ImportError:
    MATPLOTLIB_AVAILABLE = False
    logger.warning("Matplotlib not found. Visualization functions will not be available.")

try:
    import cv2
    OPENCV_AVAILABLE = True
except ImportError:
    OPENCV_AVAILABLE = False
    logger.warning("OpenCV not found. Webcam-based tracking will not be available.")

class GazeTracker:
    def __init__(self, calibration_threshold=1.0, tracker_type='simulated', webcam_id=0):
        """
        Initialize the eye-tracker hardware connection and settings.
        
        Parameters:
        -----------
        calibration_threshold : float, optional
            Threshold for acceptable calibration error (default: 1.0)
        tracker_type : str, optional
            Type of tracker to use ('simulated', 'webcam', 'tobii', etc.)
        webcam_id : int, optional
            ID of the webcam to use for webcam-based tracking (default: 0)
        """
        self.initialized = False
        self.calibration_data = None
        self.calibration_threshold = calibration_threshold
        self.calibration_quality = None
        self.calibration_score = 0.0
        self.tracker_type = tracker_type
        self.webcam_id = webcam_id
        self.webcam = None
        
        try:
            # Initialize the appropriate tracker based on type
            if tracker_type == 'webcam':
                self._initialize_webcam_tracker()
            elif tracker_type == 'tobii':
                self._initialize_tobii_tracker()
            else:
                # Default to simulated tracker
                self._initialize_simulated_tracker()
                
            logger.info(f"Gaze Tracker initialized with type: {tracker_type}")
            self.initialized = True
        except Exception as e:
            logger.error(f"Failed to initialize gaze tracker: {str(e)}")
            logger.error(traceback.format_exc())
            # Fall back to simulated tracker
            self._initialize_simulated_tracker()
            logger.warning("Falling back to simulated gaze tracker")
    
    def _initialize_webcam_tracker(self):
        """Initialize webcam-based eye tracking."""
        if not OPENCV_AVAILABLE:
            raise ImportError("OpenCV is required for webcam-based tracking")
            
        try:
            self.webcam = cv2.VideoCapture(self.webcam_id)
            if not self.webcam.isOpened():
                raise RuntimeError(f"Could not open webcam with ID {self.webcam_id}")
                
            # Check webcam properties
            width = self.webcam.get(cv2.CAP_PROP_FRAME_WIDTH)
            height = self.webcam.get(cv2.CAP_PROP_FRAME_HEIGHT)
            fps = self.webcam.get(cv2.CAP_PROP_FPS)
            
            logger.info(f"Webcam initialized: {width}x{height} @ {fps}fps")
            
            # Load face and eye detection cascades
            try:
                # These paths may need to be adjusted based on your OpenCV installation
                self.face_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_frontalface_default.xml')
                self.eye_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_eye.xml')
                
                if self.face_cascade.empty() or self.eye_cascade.empty():
                    logger.warning("Could not load face/eye detection cascades")
            except Exception as e:
                logger.error(f"Error loading detection cascades: {str(e)}")
                
        except Exception as e:
            logger.error(f"Error initializing webcam: {str(e)}")
            raise
    
    def _initialize_tobii_tracker(self):
        """Initialize Tobii eye tracker."""
        try:
            # This would be replaced with actual Tobii SDK initialization
            # For example: import tobii_research as tr
            logger.info("Tobii tracker initialization (simulated)")
        except Exception as e:
            logger.error(f"Error initializing Tobii tracker: {str(e)}")
            raise
    
    def _initialize_simulated_tracker(self):
        """Initialize simulated eye tracker."""
        logger.info("Simulated gaze tracker initialized")
    
    def get_gaze_data(self):
        """
        Acquire current gaze data from the eye-tracker.
        
        Returns:
        --------
        dict
            Dictionary containing x, y coordinates and additional metadata
        """
        if not self.initialized:
            logger.warning("Gaze tracker not initialized")
            return {"x": 0, "y": 0, "valid": False, "error": "Tracker not initialized"}
            
        try:
            if self.tracker_type == 'webcam' and OPENCV_AVAILABLE and self.webcam is not None:
                return self._get_webcam_gaze_data()
            elif self.tracker_type == 'tobii':
                return self._get_tobii_gaze_data()
            else:
                return self._get_simulated_gaze_data()
        except Exception as e:
            logger.error(f"Error getting gaze data: {str(e)}")
            return {"x": 0, "y": 0, "valid": False, "error": str(e)}
    
    def _get_webcam_gaze_data(self):
        """Get gaze data from webcam-based tracking."""
        if not self.webcam or not self.webcam.isOpened():
            logger.error("Webcam not available")
            return {"x": 0, "y": 0, "valid": False, "error": "Webcam not available"}
            
        try:
            # Capture frame from webcam
            ret, frame = self.webcam.read()
            if not ret:
                logger.warning("Could not read frame from webcam")
                return {"x": 0, "y": 0, "valid": False, "error": "Could not read frame"}
                
            # Convert to grayscale for face detection
            gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
            
            # Detect faces
            faces = self.face_cascade.detectMultiScale(gray, 1.3, 5)
            if len(faces) == 0:
                logger.debug("No faces detected")
                return {"x": 0, "y": 0, "valid": False, "error": "No faces detected"}
                
            # Use the first face detected
            (x, y, w, h) = faces[0]
            
            # Extract the face ROI
            roi_gray = gray[y:y+h, x:x+w]
            
            # Detect eyes in the face ROI
            eyes = self.eye_cascade.detectMultiScale(roi_gray)
            if len(eyes) < 2:
                logger.debug(f"Not enough eyes detected: {len(eyes)}")
                return {"x": 0, "y": 0, "valid": False, "error": f"Not enough eyes detected: {len(eyes)}"}
                
            # Calculate the center point between the eyes
            eye_centers = []
            for (ex, ey, ew, eh) in eyes[:2]:  # Use the first two eyes detected
                eye_center_x = x + ex + ew // 2
                eye_center_y = y + ey + eh // 2
                eye_centers.append((eye_center_x, eye_center_y))
                
            # Calculate the midpoint between the eyes
            gaze_x = sum(center[0] for center in eye_centers) / len(eye_centers)
            gaze_y = sum(center[1] for center in eye_centers) / len(eye_centers)
            
            # Normalize coordinates to -1 to 1 range
            frame_width = frame.shape[1]
            frame_height = frame.shape[0]
            norm_x = (gaze_x / frame_width) * 2 - 1
            norm_y = (gaze_y / frame_height) * 2 - 1
            
            return {
                "x": norm_x,
                "y": norm_y,
                "timestamp": datetime.now().timestamp(),
                "confidence": 0.7,  # Estimated confidence
                "valid": True,
                "raw_x": gaze_x,
                "raw_y": gaze_y,
                "frame_width": frame_width,
                "frame_height": frame_height
            }
            
        except Exception as e:
            logger.error(f"Error in webcam gaze tracking: {str(e)}")
            logger.error(traceback.format_exc())
            return {"x": 0, "y": 0, "valid": False, "error": str(e)}
    
    def _get_tobii_gaze_data(self):
        """Get gaze data from Tobii eye tracker."""
        # This would be replaced with actual Tobii SDK calls
        # For example: gaze_data = tobii_tracker.get_gaze_data()
        
        # Simulate Tobii data with some noise
        x = np.random.normal(0, 0.1)
        y = np.random.normal(0, 0.1)
        
        return {
            "x": x,
            "y": y,
            "timestamp": datetime.now().timestamp(),
            "confidence": 0.9,
            "valid": True
        }
    
    def _get_simulated_gaze_data(self):
        """Get simulated gaze data."""
        # Generate random gaze position with some noise
        x = np.random.normal(0, 0.1)
        y = np.random.normal(0, 0.1)
        
        return {
            "x": x,
            "y": y,
            "timestamp": datetime.now().timestamp(),
            "confidence": 0.95,
            "valid": True,
            "simulated": True
        }
    
    def calibrate(self, calibration_points=None, window=None):
        """
        Run a calibration procedure using the provided points.
        
        Parameters:
        -----------
        calibration_points : list, optional
            List of (x, y) coordinates for calibration
        window : psychopy.visual.Window, optional
            PsychoPy window for displaying calibration targets
            
        Returns:
        --------
        dict
            Calibration results including error metrics
        """
        if calibration_points is None:
            # Default 9-point calibration grid
            calibration_points = [
                (-0.8, 0.8), (0, 0.8), (0.8, 0.8),
                (-0.8, 0), (0, 0), (0.8, 0),
                (-0.8, -0.8), (0, -0.8), (0.8, -0.8)
            ]
        
        logger.info(f"Starting calibration with {len(calibration_points)} points")
        
        try:
            # This would be replaced with actual calibration code
            # that interfaces with your specific eye tracker
            
            # Simulate calibration data collection
            calibration_results = {
                "points": [],
                "target_points": [],
                "gaze_points": [],
                "errors": []
            }
            
            for i, point in enumerate(calibration_points):
                target_x, target_y = point
                
                # Simulate gaze data with some random error
                gaze_x = target_x + np.random.normal(0, 0.05)
                gaze_y = target_y + np.random.normal(0, 0.05)
                
                # Calculate error (Euclidean distance)
                error = np.sqrt((gaze_x - target_x)**2 + (gaze_y - target_y)**2)
                
                calibration_results["points"].append(i)
                calibration_results["target_points"].append((target_x, target_y))
                calibration_results["gaze_points"].append((gaze_x, gaze_y))
                calibration_results["errors"].append(error)
            
            # Calculate summary statistics
            errors_array = np.array(calibration_results["errors"])
            points_above_threshold = np.sum(errors_array > self.calibration_threshold)
            percent_above_threshold = (points_above_threshold / len(errors_array)) * 100
            
            # Calculate spatial accuracy by quadrants
            quadrant_errors = {
                "top_left": [], "top_right": [],
                "bottom_left": [], "bottom_right": []
            }
            
            for i, (tx, ty) in enumerate(calibration_results["target_points"]):
                if tx < 0 and ty > 0:
                    quadrant_errors["top_left"].append(calibration_results["errors"][i])
                elif tx >= 0 and ty > 0:
                    quadrant_errors["top_right"].append(calibration_results["errors"][i])
                elif tx < 0 and ty <= 0:
                    quadrant_errors["bottom_left"].append(calibration_results["errors"][i])
                else:
                    quadrant_errors["bottom_right"].append(calibration_results["errors"][i])
            
            quadrant_means = {q: np.mean(errs) if errs else None for q, errs in quadrant_errors.items()}
            
            # Store complete calibration data
            self.calibration_data = {
                "average": np.mean(errors_array),
                "median": np.median(errors_array),
                "std": np.std(errors_array),
                "min": np.min(errors_array),
                "max": np.max(errors_array),
                "errors": calibration_results["errors"],
                "points": calibration_results["points"],
                "target_points": calibration_results["target_points"],
                "gaze_points": calibration_results["gaze_points"],
                "points_above_threshold": points_above_threshold,
                "percent_above_threshold": percent_above_threshold,
                "quadrant_means": quadrant_means,
                "precision": np.std(errors_array),
                "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "threshold_used": self.calibration_threshold
            }
            
            # Evaluate calibration quality
            self.evaluate_calibration_quality()
            
            logger.info(f"Calibration completed with average error: {self.calibration_data['average']:.3f}")
            return self.calibration_data
            
        except Exception as e:
            logger.error(f"Error during calibration: {str(e)}")
            logger.error(traceback.format_exc())
            return None
    
    def evaluate_calibration_quality(self):
        """
        Evaluates the quality of the most recent calibration.
        
        Returns:
        --------
        str
            Calibration quality assessment ('excellent', 'good', 'fair', 'poor')
        float
            Quality score (0-1)
        """
        if not self.calibration_data:
            self.calibration_quality = "unknown"
            self.calibration_score = 0.0
            return self.calibration_quality, self.calibration_score
        
        # Define thresholds for quality assessment
        thresholds = {
            'excellent': {'avg': 0.5, 'max': 1.0, 'percent_above': 5},
            'good': {'avg': 0.8, 'max': 1.5, 'percent_above': 15},
            'fair': {'avg': 1.2, 'max': 2.0, 'percent_above': 30}
        }
        
        avg_error = self.calibration_data['average']
        max_error = self.calibration_data['max']
        percent_above = self.calibration_data['percent_above_threshold']
        
        # Calculate a quality score (0-1)
        avg_score = max(0, 1 - (avg_error / 2.0))
        max_score = max(0, 1 - (max_error / 4.0))
        percent_score = max(0, 1 - (percent_above / 100.0))
        
        self.calibration_score = (avg_score * 0.5) + (max_score * 0.3) + (percent_score * 0.2)
        
        # Determine quality category
        if (avg_error <= thresholds['excellent']['avg'] and 
            max_error <= thresholds['excellent']['max'] and 
            percent_above <= thresholds['excellent']['percent_above']):
            self.calibration_quality = "excellent"
        elif (avg_error <= thresholds['good']['avg'] and 
              max_error <= thresholds['good']['max'] and 
              percent_above <= thresholds['good']['percent_above']):
            self.calibration_quality = "good"
        elif (avg_error <= thresholds['fair']['avg'] and 
              max_error <= thresholds['fair']['max'] and 
              percent_above <= thresholds['fair']['percent_above']):
            self.calibration_quality = "fair"
        else:
            self.calibration_quality = "poor"
        
        return self.calibration_quality, self.calibration_score
    
    def visualize_calibration(self, output_dir=None):
        """
        Creates visualizations of calibration results.
        
        Parameters:
        -----------
        output_dir : str, optional
            Directory to save visualizations (if None, just displays)
        """
        if not MATPLOTLIB_AVAILABLE:
            logger.error("Matplotlib is required for visualization")
            return
            
        if not self.calibration_data:
            logger.warning("No calibration data to visualize")
            return
        
        try:
            # Create figure with subplots
            fig = plt.figure(figsize=(15, 10))
            
            # Plot 1: Error distribution
            ax1 = fig.add_subplot(221)
            ax1.hist(self.calibration_data['errors'], bins=10, alpha=0.7, color='blue')
            ax1.axvline(self.calibration_data['average'], color='red', linestyle='--', 
                       label=f"Mean: {self.calibration_data['average']:.3f}")
            ax1.axvline(self.calibration_data['median'], color='green', linestyle='--', 
                       label=f"Median: {self.calibration_data['median']:.3f}")
            ax1.set_title('Error Distribution')
            ax1.set_xlabel('Error')
            ax1.set_ylabel('Frequency')
            ax1.legend()
            
            # Plot 2: Spatial accuracy (target vs. gaze)
            ax2 = fig.add_subplot(222)
            target_x, target_y = zip(*self.calibration_data['target_points'])
            gaze_x, gaze_y = zip(*self.calibration_data['gaze_points'])
            
            # Plot target points
            ax2.scatter(target_x, target_y, color='blue', label='Target', s=50)
            
            # Plot gaze points
            ax2.scatter(gaze_x, gaze_y, color='red', alpha=0.5, label='Gaze', s=30)
            
            # Draw lines connecting corresponding points
            for i in range(len(target_x)):
                ax2.plot([target_x[i], gaze_x[i]], [target_y[i], gaze_y[i]], 'k-', alpha=0.3)
            
            ax2.set_title('Spatial Accuracy')
            ax2.set_xlabel('X Coordinate')
            ax2.set_ylabel('Y Coordinate')
            ax2.legend()
            ax2.grid(True, alpha=0.3)
            
            # Plot 3: Error by point index
            ax3 = fig.add_subplot(223)
            ax3.bar(self.calibration_data['points'], self.calibration_data['errors'], alpha=0.7)
            ax3.axhline(self.calibration_data['threshold_used'], color='red', linestyle='--', 
                        label=f'Threshold: {self.calibration_data["threshold_used"]:.2f}')
            ax3.set_title('Error by Calibration Point')
            ax3.set_xlabel('Point Index')
            ax3.set_ylabel('Error')
            ax3.legend()
            
            # Plot 4: Quadrant analysis
            ax4 = fig.add_subplot(224)
            quadrants = list(self.calibration_data['quadrant_means'].keys())
            means = [self.calibration_data['quadrant_means'][q] if self.calibration_data['quadrant_means'][q] is not None else 0 
                    for q in quadrants]
            
            ax4.bar(quadrants, means, alpha=0.7)
            ax4.set_title('Error by Screen Quadrant')
            ax4.set_xlabel('Quadrant')
            ax4.set_ylabel('Mean Error')
            
            plt.tight_layout()
            
            # Save if output directory provided
            if output_dir:
                os.makedirs(output_dir, exist_ok=True)
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                plt.savefig(os.path.join(output_dir, f"calibration_analysis_{timestamp}.png"))
                
                # Also save analysis as JSON
                try:
                    with open(os.path.join(output_dir, f"calibration_analysis_{timestamp}.json"), 'w') as f:
                        # Convert numpy types to Python native types for JSON serialization
                        json_safe_analysis = {k: v for k, v in self.calibration_data.items() 
                                            if k not in ['errors', 'points', 'target_points', 'gaze_points']}
                        json_safe_analysis['errors'] = [float(e) for e in self.calibration_data['errors']]
                        json_safe_analysis['points'] = [int(p) for p in self.calibration_data['points']]
                        json_safe_analysis['target_points'] = [(float(x), float(y)) for x, y in self.calibration_data['target_points']]
                        json_safe_analysis['gaze_points'] = [(float(x), float(y)) for x, y in self.calibration_data['gaze_points']]
                        json_safe_analysis['quadrant_means'] = {k: float(v) if v is not None else None 
                                                              for k, v in self.calibration_data['quadrant_means'].items()}
                        
                        json.dump(json_safe_analysis, f, indent=2)
                except Exception as e:
                    logger.error(f"Error saving analysis to JSON: {str(e)}")
            
            plt.show()
        except Exception as e:
            logger.error(f"Error visualizing calibration: {str(e)}")
            logger.error(traceback.format_exc())
    
    def close(self):
        """Close the tracker and release resources."""
        try:
            if self.tracker_type == 'webcam' and self.webcam is not None:
                self.webcam.release()
                logger.info("Webcam released")
            
            # Add other cleanup code for different tracker types
            
            self.initialized = False
            logger.info("Gaze tracker closed")
        except Exception as e:
            logger.error(f"Error closing gaze tracker: {str(e)}")


if __name__ == "__main__":
    # Simple test of the GazeTracker class
    print("Testing GazeTracker...")
    
    # Test with different tracker types
    tracker_types = ['simulated']
    
    if OPENCV_AVAILABLE:
        tracker_types.append('webcam')
    
    for tracker_type in tracker_types:
        print(f"\nTesting {tracker_type} tracker:")
        try:
            tracker = GazeTracker(tracker_type=tracker_type)
            
            # Get some gaze data
            for i in range(3):
                gaze_data = tracker.get_gaze_data()
                print(f"  Gaze data {i+1}: x={gaze_data['x']:.3f}, y={gaze_data['y']:.3f}, valid={gaze_data['valid']}")
            
            # Run a calibration
            calibration_data = tracker.calibrate()
            if calibration_data:
                print(f"  Calibration average error: {calibration_data['average']:.3f}")
                print(f"  Calibration quality: {tracker.calibration_quality}")
            
            # Close the tracker
            tracker.close()
            
        except Exception as e:
            print(f"  Error testing {tracker_type} tracker: {str(e)}")
            traceback.print_exc()