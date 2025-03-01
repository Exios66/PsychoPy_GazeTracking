# Scripts/calibration.py
from psychopy import visual, core, event, logging
import json
import os
import numpy as np
from gaze_tracking import GazeTracker  # Assumes your gaze tracking module is set up

def load_calibration_config(config_path):
    """
    Load calibration configuration from a JSON file.
    
    Parameters:
    -----------
    config_path : str
        Path to the configuration file
        
    Returns:
    --------
    dict
        Configuration parameters
    """
    try:
        with open(config_path, 'r') as f:
            return json.load(f)
    except FileNotFoundError:
        logging.error(f"Configuration file not found: {config_path}")
        return {}
    except json.JSONDecodeError:
        logging.error(f"Invalid JSON in configuration file: {config_path}")
        return {}

def calculate_error(gaze_x, gaze_y, target_x, target_y):
    """
    Calculate Euclidean distance between gaze position and target position.
    
    Parameters:
    -----------
    gaze_x, gaze_y : float
        Coordinates of the gaze position
    target_x, target_y : float
        Coordinates of the target position
        
    Returns:
    --------
    float
        Euclidean distance between gaze and target
    """
    return np.sqrt((gaze_x - target_x)**2 + (gaze_y - target_y)**2)

def animate_point(win, start_pos, end_pos, duration=0.5, steps=20):
    """
    Animate a point moving from start_pos to end_pos.
    
    Parameters:
    -----------
    win : psychopy.visual.Window
        Window to draw on
    start_pos : tuple
        Starting position (x, y)
    end_pos : tuple
        Ending position (x, y)
    duration : float
        Duration of animation in seconds
    steps : int
        Number of steps in the animation
    """
    dot = visual.Circle(win, radius=0.02, fillColor="white", lineColor="white")
    
    for i in range(steps + 1):
        t = i / steps
        x = start_pos[0] + t * (end_pos[0] - start_pos[0])
        y = start_pos[1] + t * (end_pos[1] - start_pos[1])
        dot.pos = (x, y)
        dot.draw()
        win.flip()
        core.wait(duration / steps)

def run_calibration(config_path=None):
    """
    Run the eye-tracking calibration procedure.
    
    Parameters:
    -----------
    config_path : str, optional
        Path to the configuration file. If None, uses default path.
    
    Returns:
    --------
    dict
        Calibration results including average error and success status
    """
    # Set up logging
    logging.console.setLevel(logging.INFO)
    
    # Load configuration
    if config_path is None:
        config_path = os.path.join("Scripts", "calibration_config.json")
    
    config = load_calibration_config(config_path)
    window_width = config.get("window_width", 1024)
    window_height = config.get("window_height", 768)
    full_screen = config.get("full_screen", False)
    fixation_duration = config.get("fixation_duration", 1.0)
    inter_trial_interval = config.get("inter_trial_interval", 0.5)
    calibration_points = config.get("calibration_points", [
        {"x": -0.8, "y": -0.8}, {"x": 0, "y": -0.8}, {"x": 0.8, "y": -0.8},
        {"x": -0.8, "y": 0}, {"x": 0, "y": 0}, {"x": 0.8, "y": 0},
        {"x": -0.8, "y": 0.8}, {"x": 0, "y": 0.8}, {"x": 0.8, "y": 0.8}
    ])
    dot_size = config.get("dot_size", 0.05)
    validation_points = config.get("validation_points", [
        {"x": -0.4, "y": -0.4}, {"x": 0.4, "y": -0.4},
        {"x": -0.4, "y": 0.4}, {"x": 0.4, "y": 0.4}
    ])
    
    # Create window and initialize tracker
    win = visual.Window(
        [window_width, window_height], 
        fullscr=full_screen,
        monitor="testMonitor",
        units="norm",
        color="gray"
    )
    
    try:
        tracker = GazeTracker()
        logging.info("Eye tracker initialized successfully")
    except Exception as e:
        logging.error(f"Failed to initialize eye tracker: {e}")
        error_msg = visual.TextStim(
            win, 
            text=f"Failed to initialize eye tracker:\n{e}\n\nPress any key to exit.",
            color="red"
        )
        error_msg.draw()
        win.flip()
        event.waitKeys()
        win.close()
        return {"success": False, "error": str(e)}
    
    # Create and open a log file for calibration data
    timestamp = core.getAbsTime()
    log_dir = os.path.join("Data", "calibration")
    os.makedirs(log_dir, exist_ok=True)
    log_path = os.path.join(log_dir, f"calibration_log_{timestamp:.0f}.txt")
    
    try:
        log_file = open(log_path, "w")
        log_file.write("Phase, PointIndex, ConfigX, ConfigY, GazeX, GazeY, Error\n")
    except Exception as e:
        logging.error(f"Failed to create log file: {e}")
        error_msg = visual.TextStim(
            win, 
            text=f"Failed to create log file:\n{e}\n\nPress any key to exit.",
            color="red"
        )
        error_msg.draw()
        win.flip()
        event.waitKeys()
        win.close()
        return {"success": False, "error": str(e)}
    
    # Display instructions
    instruction = visual.TextStim(
        win, 
        text="Calibration:\nPlease follow the dot on the screen.\n"
             "Try to keep your head still during the procedure.\n"
             "Press any key to begin.",
        height=0.05
    )
    instruction.draw()
    win.flip()
    event.waitKeys()
    
    # Countdown before starting
    for i in range(3, 0, -1):
        countdown = visual.TextStim(win, text=str(i), height=0.15)
        countdown.draw()
        win.flip()
        core.wait(1.0)
    
    # Initialize variables to track calibration quality
    all_errors = []
    last_pos = (0, 0)
    
    # Loop through each calibration point
    for i, point in enumerate(calibration_points, start=1):
        try:
            # Animate dot movement to the next position
            target_pos = (point["x"], point["y"])
            animate_point(win, last_pos, target_pos)
            last_pos = target_pos
            
            # Draw calibration dot at specified coordinates
            dot = visual.Circle(
                win, 
                radius=dot_size, 
                fillColor="white", 
                lineColor="black", 
                pos=target_pos
            )
            
            # Pulse the dot to attract attention
            for pulse in range(3):
                for size in np.linspace(dot_size*0.8, dot_size*1.2, 5):
                    dot.radius = size
                    dot.draw()
                    win.flip()
                    core.wait(0.03)
            
            # Hold the dot steady for fixation
            dot.radius = dot_size
            dot.draw()
            win.flip()
            core.wait(fixation_duration)
            
            # Acquire gaze data with error handling
            gaze_data = tracker.get_gaze_data()  # Expected to return a dict with keys 'x' and 'y'
            
            # Compute error (Euclidean distance)
            error = calculate_error(
                gaze_data.get("x", 0), 
                gaze_data.get("y", 0), 
                point["x"], 
                point["y"]
            )
            all_errors.append(error)
            
            # Log calibration data
            log_file.write(f"Calibration, {i}, {point['x']}, {point['y']}, "
                          f"{gaze_data.get('x', 'NA')}, {gaze_data.get('y', 'NA')}, {error}\n")
            
            # Visual feedback (optional)
            if config.get("show_gaze_feedback", False):
                feedback_dot = visual.Circle(
                    win, 
                    radius=dot_size/2, 
                    fillColor="red", 
                    pos=(gaze_data.get("x", 0), gaze_data.get("y", 0))
                )
                dot.draw()
                feedback_dot.draw()
                win.flip()
                core.wait(0.5)
        
        except Exception as e:
            # Log any error encountered
            log_file.write(f"Calibration, {i}, {point['x']}, {point['y']}, ERROR, ERROR, NA\n")
            logging.error(f"Error at calibration point {i}: {e}")
        
        core.wait(inter_trial_interval)
    
    # Validation phase
    validation_text = visual.TextStim(
        win, 
        text="Validation phase starting...\nPlease continue to follow the dot.",
        height=0.05
    )
    validation_text.draw()
    win.flip()
    core.wait(2.0)
    
    validation_errors = []
    
    # Loop through validation points
    for i, point in enumerate(validation_points, start=1):
        try:
            # Animate dot movement to the next position
            target_pos = (point["x"], point["y"])
            animate_point(win, last_pos, target_pos)
            last_pos = target_pos
            
            # Draw validation dot
            dot = visual.Circle(
                win, 
                radius=dot_size, 
                fillColor="yellow", 
                lineColor="black", 
                pos=target_pos
            )
            dot.draw()
            win.flip()
            core.wait(fixation_duration)
            
            # Acquire gaze data
            gaze_data = tracker.get_gaze_data()
            
            # Compute error
            error = calculate_error(
                gaze_data.get("x", 0), 
                gaze_data.get("y", 0), 
                point["x"], 
                point["y"]
            )
            validation_errors.append(error)
            
            # Log validation data
            log_file.write(f"Validation, {i}, {point['x']}, {point['y']}, "
                          f"{gaze_data.get('x', 'NA')}, {gaze_data.get('y', 'NA')}, {error}\n")
        
        except Exception as e:
            log_file.write(f"Validation, {i}, {point['x']}, {point['y']}, ERROR, ERROR, NA\n")
            logging.error(f"Error at validation point {i}: {e}")
        
        core.wait(inter_trial_interval)
    
    log_file.close()
    
    # Calculate average errors
    avg_calibration_error = np.mean(all_errors) if all_errors else float('nan')
    avg_validation_error = np.mean(validation_errors) if validation_errors else float('nan')
    
    # Determine if calibration was successful
    error_threshold = config.get("error_threshold", 0.2)
    calibration_success = avg_validation_error <= error_threshold if not np.isnan(avg_validation_error) else False
    
    # End calibration message with results
    result_color = "green" if calibration_success else "red"
    result_text = "Calibration successful!" if calibration_success else "Calibration needs improvement."
    
    end_text = visual.TextStim(
        win, 
        text=f"Calibration complete.\n\n"
             f"Average calibration error: {avg_calibration_error:.3f}\n"
             f"Average validation error: {avg_validation_error:.3f}\n\n"
             f"{result_text}\n\n"
             f"Press any key to continue.",
        color=result_color,
        height=0.05
    )
    end_text.draw()
    win.flip()
    event.waitKeys()
    
    # Save calibration results
    results = {
        "success": calibration_success,
        "calibration_error": float(avg_calibration_error),
        "validation_error": float(avg_validation_error),
        "timestamp": timestamp,
        "log_path": log_path
    }
    
    results_path = os.path.join(log_dir, f"calibration_results_{timestamp:.0f}.json")
    with open(results_path, 'w') as f:
        json.dump(results, f, indent=4)
    
    win.close()
    return results

if __name__ == '__main__':
    results = run_calibration()
    print(f"Calibration {'successful' if results['success'] else 'failed'}")
    print(f"Average error: {results['validation_error']:.3f}")