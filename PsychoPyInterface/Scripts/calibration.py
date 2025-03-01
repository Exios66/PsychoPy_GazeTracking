# Scripts/calibration.py
from psychopy import visual, core, event
import json
import os
from gaze_tracking import GazeTracker  # Assumes your gaze tracking module is set up

def load_calibration_config(config_path):
    with open(config_path, 'r') as f:
        return json.load(f)

def run_calibration():
    # Load configuration
    config = load_calibration_config(os.path.join("Scripts", "calibration_config.json"))
    window_width = config.get("window_width", 1024)
    window_height = config.get("window_height", 768)
    full_screen = config.get("full_screen", False)
    fixation_duration = config.get("fixation_duration", 1.0)
    inter_trial_interval = config.get("inter_trial_interval", 0.5)
    calibration_points = config.get("calibration_points", [])
    dot_size = config.get("dot_size", 0.05)
    
    # Create window and initialize tracker
    win = visual.Window([window_width, window_height], fullscr=full_screen)
    tracker = GazeTracker()
    
    # Create and open a log file for calibration data
    log_path = os.path.join("Data", "calibration_log.txt")
    os.makedirs(os.path.dirname(log_path), exist_ok=True)
    log_file = open(log_path, "w")
    log_file.write("PointIndex, ConfigX, ConfigY, GazeX, GazeY, Error\n")
    
    # Display instructions
    instruction = visual.TextStim(win, text="Calibration:\nPlease follow the dot on the screen.\nPress any key to begin.")
    instruction.draw()
    win.flip()
    event.waitKeys()
    
    # Loop through each calibration point
    for i, point in enumerate(calibration_points, start=1):
        try:
            # Draw calibration dot at specified coordinates
            dot = visual.Circle(win, radius=dot_size, fillColor="white", lineColor="white", pos=(point["x"], point["y"]))
            dot.draw()
            win.flip()
            core.wait(fixation_duration)
            
            # Acquire gaze data with error handling
            gaze_data = tracker.get_gaze_data()  # Expected to return a dict with keys 'x' and 'y'
            # Compute error (simple Euclidean difference in this example)
            error_x = abs(gaze_data.get("x", 0) - point["x"])
            error_y = abs(gaze_data.get("y", 0) - point["y"])
            error = (error_x**2 + error_y**2)**0.5
            
            # Log calibration data
            log_file.write(f"{i}, {point['x']}, {point['y']}, {gaze_data.get('x')}, {gaze_data.get('y')}, {error}\n")
        
        except Exception as e:
            # Log any error encountered
            log_file.write(f"{i}, {point['x']}, {point['y']}, ERROR, ERROR, {str(e)}\n")
            print(f"Error at calibration point {i}: {e}")
        
        core.wait(inter_trial_interval)
    
    log_file.close()
    
    # End calibration message
    end_text = visual.TextStim(win, text="Calibration complete.\nPress any key to continue.")
    end_text.draw()
    win.flip()
    event.waitKeys()
    win.close()
    core.quit()

if __name__ == '__main__':
    run_calibration()