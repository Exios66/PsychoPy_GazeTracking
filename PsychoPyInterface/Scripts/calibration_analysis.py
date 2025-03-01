# Scripts/calibration_analysis.py
import os
import numpy as np
import matplotlib.pyplot as plt
from datetime import datetime
import json

def analyze_calibration(log_file_path, threshold=1.0):
    """
    Reads the calibration log file and computes detailed error metrics.
    
    Parameters:
    -----------
    log_file_path : str
        Path to the calibration log file
    threshold : float, optional
        Error threshold for determining acceptable calibration points (default: 1.0)
        
    Returns:
    --------
    dict or None
        Dictionary containing calibration metrics or None if no valid data
        
    Notes:
    ------
    Expects the log file to have a header line:
    "PointIndex, ConfigX, ConfigY, GazeX, GazeY, Error"
    """
    errors = []
    points = []
    gaze_points = []
    target_points = []
    
    if not os.path.exists(log_file_path):
        print(f"Warning: Calibration file not found at {log_file_path}")
        return None

    with open(log_file_path, "r") as f:
        header = next(f)  # Skip header
        for line in f:
            parts = [p.strip() for p in line.strip().split(',')]
            if len(parts) < 6:
                continue
            try:
                point_idx = int(parts[0])
                config_x, config_y = float(parts[1]), float(parts[2])
                gaze_x, gaze_y = float(parts[3]), float(parts[4])
                error = float(parts[5])
                
                errors.append(error)
                points.append(point_idx)
                target_points.append((config_x, config_y))
                gaze_points.append((gaze_x, gaze_y))
            except (ValueError, IndexError) as e:
                print(f"Warning: Could not parse line: {line.strip()} - {str(e)}")
                continue

    if not errors:
        return None

    # Calculate error metrics
    errors_array = np.array(errors)
    points_above_threshold = np.sum(errors_array > threshold)
    percent_above_threshold = (points_above_threshold / len(errors)) * 100
    
    # Calculate spatial accuracy (mean error by region)
    # Divide screen into quadrants and calculate mean error for each
    quadrant_errors = {
        "top_left": [], "top_right": [],
        "bottom_left": [], "bottom_right": []
    }
    
    for i, (tx, ty) in enumerate(target_points):
        if tx < 0 and ty > 0:
            quadrant_errors["top_left"].append(errors[i])
        elif tx >= 0 and ty > 0:
            quadrant_errors["top_right"].append(errors[i])
        elif tx < 0 and ty <= 0:
            quadrant_errors["bottom_left"].append(errors[i])
        else:
            quadrant_errors["bottom_right"].append(errors[i])
    
    quadrant_means = {q: np.mean(errs) if errs else None for q, errs in quadrant_errors.items()}
    
    # Calculate precision (standard deviation of samples for each point)
    precision = np.std(errors)
    
    # Calculate median which is less sensitive to outliers
    median_error = np.median(errors)
    
    analysis = {
        "average": np.mean(errors),
        "median": median_error,
        "std": np.std(errors),
        "min": np.min(errors),
        "max": np.max(errors),
        "errors": errors,
        "points": points,
        "target_points": target_points,
        "gaze_points": gaze_points,
        "points_above_threshold": points_above_threshold,
        "percent_above_threshold": percent_above_threshold,
        "quadrant_means": quadrant_means,
        "precision": precision,
        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "threshold_used": threshold
    }
    return analysis

def visualize_calibration(analysis, output_dir=None):
    """
    Creates visualizations of calibration results.
    
    Parameters:
    -----------
    analysis : dict
        Calibration analysis results from analyze_calibration
    output_dir : str, optional
        Directory to save visualizations (if None, just displays)
    """
    if not analysis:
        print("No analysis data to visualize")
        return
    
    # Create figure with subplots
    fig = plt.figure(figsize=(15, 10))
    
    # Plot 1: Error distribution
    ax1 = fig.add_subplot(221)
    ax1.hist(analysis['errors'], bins=10, alpha=0.7, color='blue')
    ax1.axvline(analysis['average'], color='red', linestyle='--', label=f"Mean: {analysis['average']:.3f}")
    ax1.axvline(analysis['median'], color='green', linestyle='--', label=f"Median: {analysis['median']:.3f}")
    ax1.set_title('Error Distribution')
    ax1.set_xlabel('Error')
    ax1.set_ylabel('Frequency')
    ax1.legend()
    
    # Plot 2: Spatial accuracy (target vs. gaze)
    ax2 = fig.add_subplot(222)
    target_x, target_y = zip(*analysis['target_points'])
    gaze_x, gaze_y = zip(*analysis['gaze_points'])
    
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
    ax3.bar(analysis['points'], analysis['errors'], alpha=0.7)
    ax3.axhline(analysis['threshold_used'], color='red', linestyle='--', 
                label=f'Threshold: {analysis["threshold_used"]:.2f}')
    ax3.set_title('Error by Calibration Point')
    ax3.set_xlabel('Point Index')
    ax3.set_ylabel('Error')
    ax3.legend()
    
    # Plot 4: Quadrant analysis
    ax4 = fig.add_subplot(224)
    quadrants = list(analysis['quadrant_means'].keys())
    means = [analysis['quadrant_means'][q] if analysis['quadrant_means'][q] is not None else 0 
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
            json_safe_analysis = {k: v for k, v in analysis.items() if k not in ['errors', 'points', 'target_points', 'gaze_points']}
            json_safe_analysis['errors'] = [float(e) for e in analysis['errors']]
            json_safe_analysis['points'] = [int(p) for p in analysis['points']]
            json_safe_analysis['target_points'] = [(float(x), float(y)) for x, y in analysis['target_points']]
            json_safe_analysis['gaze_points'] = [(float(x), float(y)) for x, y in analysis['gaze_points']]
            json_safe_analysis['quadrant_means'] = {k: float(v) if v is not None else None for k, v in analysis['quadrant_means'].items()}
            
            json.dump(json_safe_analysis, f, indent=2)
    
    plt.show()

def get_calibration_quality(analysis):
    """
    Evaluates the overall quality of the calibration.
    
    Parameters:
    -----------
    analysis : dict
        Calibration analysis results
        
    Returns:
    --------
    str
        Calibration quality assessment ('excellent', 'good', 'fair', 'poor')
    float
        Quality score (0-1)
    """
    if not analysis:
        return "unknown", 0.0
    
    # Define thresholds for quality assessment
    thresholds = {
        'excellent': {'avg': 0.5, 'max': 1.0, 'percent_above': 5},
        'good': {'avg': 0.8, 'max': 1.5, 'percent_above': 15},
        'fair': {'avg': 1.2, 'max': 2.0, 'percent_above': 30}
    }
    
    avg_error = analysis['average']
    max_error = analysis['max']
    percent_above = analysis['percent_above_threshold']
    
    # Calculate a quality score (0-1)
    # Lower is better for all metrics
    avg_score = max(0, 1 - (avg_error / 2.0))
    max_score = max(0, 1 - (max_error / 4.0))
    percent_score = max(0, 1 - (percent_above / 100.0))
    
    quality_score = (avg_score * 0.5) + (max_score * 0.3) + (percent_score * 0.2)
    
    # Determine quality category
    if (avg_error <= thresholds['excellent']['avg'] and 
        max_error <= thresholds['excellent']['max'] and 
        percent_above <= thresholds['excellent']['percent_above']):
        quality = "excellent"
    elif (avg_error <= thresholds['good']['avg'] and 
          max_error <= thresholds['good']['max'] and 
          percent_above <= thresholds['good']['percent_above']):
        quality = "good"
    elif (avg_error <= thresholds['fair']['avg'] and 
          max_error <= thresholds['fair']['max'] and 
          percent_above <= thresholds['fair']['percent_above']):
        quality = "fair"
    else:
        quality = "poor"
    
    return quality, quality_score

if __name__ == '__main__':
    # For standalone testing, update the path if needed.
    log_path = os.path.join("Data", "calibration_log.txt")
    result = analyze_calibration(log_path, threshold=1.0)
    
    if result:
        print("Calibration Analysis:")
        print(f"Average Error: {result['average']:.3f}")
        print(f"Median Error: {result['median']:.3f}")
        print(f"Standard Deviation: {result['std']:.3f}")
        print(f"Minimum Error: {result['min']:.3f}")
        print(f"Maximum Error: {result['max']:.3f}")
        print(f"Points above threshold: {result['points_above_threshold']} ({result['percent_above_threshold']:.1f}%)")
        
        quality, score = get_calibration_quality(result)
        print(f"Calibration Quality: {quality.upper()} (Score: {score:.2f})")
        
        # Visualize the results
        output_dir = os.path.join("Data", "calibration_reports")
        visualize_calibration(result, output_dir)
        
        print(f"Visualization saved to {output_dir}")
    else:
        print("No valid calibration data found.")