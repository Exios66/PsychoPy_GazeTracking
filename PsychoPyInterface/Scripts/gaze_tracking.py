# Scripts/gaze_tracking.py
import numpy as np
import os
import json
from datetime import datetime
import matplotlib.pyplot as plt

class GazeTracker:
    def __init__(self, calibration_threshold=1.0):
        """
        Initialize the eye-tracker hardware connection and settings.
        
        Parameters:
        -----------
        calibration_threshold : float, optional
            Threshold for acceptable calibration error (default: 1.0)
        """
        # Initialize connection to the eye-tracker hardware
        # (e.g., using vendor SDK or a serial port connection)
        # For demonstration, we simulate initialization.
        self.initialized = True
        self.calibration_data = None
        self.calibration_threshold = calibration_threshold
        self.calibration_quality = None
        self.calibration_score = 0.0
        print("Gaze Tracker Initialized.")
    
    def get_gaze_data(self):
        """
        Acquire current gaze data from the eye-tracker.
        
        Returns:
        --------
        dict
            Dictionary containing x, y coordinates and additional metadata
        """
        # Acquire gaze data from the eye-tracker
        # Replace the simulated values with actual gaze coordinates.
        # For example, using an API call: gaze = tracker.get_current_gaze()
        simulated_data = {
            "x": 400, 
            "y": 300,
            "timestamp": datetime.now().timestamp(),
            "confidence": 0.95,
            "valid": True
        }
        return simulated_data
    
    def calibrate(self, calibration_points, window=None):
        """
        Run a calibration procedure using the provided points.
        
        Parameters:
        -----------
        calibration_points : list
            List of (x, y) coordinates for calibration
        window : psychopy.visual.Window, optional
            PsychoPy window for displaying calibration targets
            
        Returns:
        --------
        dict
            Calibration results including error metrics
        """
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
        
        return self.calibration_data
    
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
        if not self.calibration_data:
            print("No calibration data to visualize")
            return
        
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
        
        plt.show()
        
    def save_calibration_log(self, log_path):
        """
        Saves calibration data to a log file.
        
        Parameters:
        -----------
        log_path : str
            Path to save the calibration log
        """
        if not self.calibration_data:
            print("No calibration data to save")
            return
            
        os.makedirs(os.path.dirname(log_path), exist_ok=True)
        
        with open(log_path, 'w') as f:
            # Write header
            f.write("PointIndex, ConfigX, ConfigY, GazeX, GazeY, Error\n")
            
            # Write data rows
            for i in range(len(self.calibration_data['points'])):
                point_idx = self.calibration_data['points'][i]
                target_x, target_y = self.calibration_data['target_points'][i]
                gaze_x, gaze_y = self.calibration_data['gaze_points'][i]
                error = self.calibration_data['errors'][i]
                
                f.write(f"{point_idx}, {target_x}, {target_y}, {gaze_x}, {gaze_y}, {error}\n")
                
        print(f"Calibration log saved to {log_path}")

if __name__ == '__main__':
    # For testing the gaze tracker independently:
    tracker = GazeTracker(calibration_threshold=0.8)
    
    # Test basic gaze data acquisition
    sample = tracker.get_gaze_data()
    print("Sample gaze data:", sample)
    
    # Test calibration with simulated points
    calibration_points = [
        (-0.8, -0.8), (0, -0.8), (0.8, -0.8),
        (-0.8, 0), (0, 0), (0.8, 0),
        (-0.8, 0.8), (0, 0.8), (0.8, 0.8)
    ]
    
    calibration_results = tracker.calibrate(calibration_points)
    quality, score = tracker.evaluate_calibration_quality()
    
    print(f"\nCalibration Results:")
    print(f"Average Error: {calibration_results['average']:.3f}")
    print(f"Median Error: {calibration_results['median']:.3f}")
    print(f"Quality: {quality.upper()} (Score: {score:.2f})")
    
    # Save and visualize results
    output_dir = os.path.join("Data", "calibration_reports")
    tracker.save_calibration_log(os.path.join("Data", "calibration_log.txt"))
    tracker.visualize_calibration(output_dir)