# Scripts/validation.py
from psychopy import visual, core, event
import json
import os
from utils.eye_tracker import EyeTracker  # Use the EyeTracker class from utils.eye_tracker

def load_calibration_config(config_path):
    with open(config_path, 'r') as f:
        return json.load(f)

def run_validation():
    # Load configuration
    config = load_calibration_config(os.path.join("Scripts", "calibration_config.json"))
    window_width = config.get("window_width", 1024)
    window_height = config.get("window_height", 768)
    full_screen = config.get("full_screen", False)
    fixation_duration = config.get("fixation_duration", 1.0)
    inter_trial_interval = config.get("inter_trial_interval", 0.5)
    # Use validation_points if provided; otherwise default to calibration_points
    validation_points = config.get("validation_points", config.get("calibration_points", []))
    dot_size = config.get("dot_size", 0.05)
    validation_threshold = config.get("validation_threshold", 0.2)
    
    # Create window and initialize tracker
    win = visual.Window([window_width, window_height], fullscr=full_screen)
    tracker = EyeTracker(win, tracker_type='webgazer')  # Use EyeTracker instead of GazeTracker
    
    # Create and open a log file for validation data
    log_path = os.path.join("Data", "validation_log.txt")
    os.makedirs(os.path.dirname(log_path), exist_ok=True)
    log_file = open(log_path, "w")
    log_file.write("PointIndex, ConfigX, ConfigY, GazeX, GazeY, Error\n")
    
    # Display instructions
    instruction = visual.TextStim(win, text="Validation:\nPlease follow the dot on the screen.\nPress any key to begin.")
    instruction.draw()
    win.flip()
    event.waitKeys()
    
    error_sum = 0
    for i, point in enumerate(validation_points, start=1):
        try:
            # Draw validation dot
            dot = visual.Circle(win, radius=dot_size, fillColor="green", lineColor="green", pos=(point["x"], point["y"]))
            dot.draw()
            win.flip()
            core.wait(fixation_duration)
            
            # Acquire gaze data and compute error
            gaze_position = tracker.get_gaze_position()  # Use get_gaze_position method
            gaze_data = {"x": gaze_position[0], "y": gaze_position[1]} if gaze_position else {"x": 0, "y": 0}
            error_x = abs(gaze_data.get("x", 0) - point["x"])
            error_y = abs(gaze_data.get("y", 0) - point["y"])
            error = (error_x**2 + error_y**2)**0.5
            
            log_file.write(f"{i}, {point['x']}, {point['y']}, {gaze_data.get('x')}, {gaze_data.get('y')}, {error}\n")
            error_sum += error
        
        except Exception as e:
            log_file.write(f"{i}, {point['x']}, {point['y']}, ERROR, ERROR, {str(e)}\n")
            print(f"Error at validation point {i}: {e}")
        
        core.wait(inter_trial_interval)
    
    avg_error = error_sum / len(validation_points) if validation_points else None
    log_file.write(f"Average Error: {avg_error}\n")
    log_file.close()
    
    # Display validation result message
    if avg_error is not None and avg_error <= validation_threshold:
        result_text = f"Validation successful!\nAverage error: {avg_error:.2f}\nPress any key to continue."
    else:
        result_text = (f"Validation not successful.\nAverage error: {avg_error:.2f} "
                       f"(Threshold: {validation_threshold})\nConsider recalibrating.\nPress any key to continue.")
    
    result = visual.TextStim(win, text=result_text)
    result.draw()
    win.flip()
    event.waitKeys()
    win.close()
    core.quit()

if __name__ == '__main__':
    run_validation()