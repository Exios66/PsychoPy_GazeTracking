# Scripts/calibration_analysis.py
import os
import numpy as np

def analyze_calibration(log_file_path):
    """
    Reads the calibration log file and computes detailed error metrics.
    Expects the log file to have a header line:
    "PointIndex, ConfigX, ConfigY, GazeX, GazeY, Error"
    """
    errors = []
    if not os.path.exists(log_file_path):
        return None

    with open(log_file_path, "r") as f:
        next(f)  # Skip header
        for line in f:
            parts = line.strip().split(',')
            if len(parts) < 6:
                continue
            try:
                error = float(parts[5])
                errors.append(error)
            except Exception:
                continue

    if not errors:
        return None

    analysis = {
        "average": np.mean(errors),
        "std": np.std(errors),
        "min": np.min(errors),
        "max": np.max(errors),
        "errors": errors
    }
    return analysis

if __name__ == '__main__':
    # For standalone testing, update the path if needed.
    log_path = os.path.join("Data", "calibration_log.txt")
    result = analyze_calibration(log_path)
    if result:
        print("Calibration Analysis:")
        print(f"Average Error: {result['average']:.3f}")
        print(f"Standard Deviation: {result['std']:.3f}")
        print(f"Minimum Error: {result['min']:.3f}")
        print(f"Maximum Error: {result['max']:.3f}")
    else:
        print("No valid calibration data found.")