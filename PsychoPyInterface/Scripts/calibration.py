# Scripts/calibration.py
import os
import json
import numpy as np
import logging
import traceback
from datetime import datetime

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('calibration')

try:
    from psychopy import visual, core, event, logging as psychopy_logging
    PSYCHOPY_AVAILABLE = True
except ImportError:
    PSYCHOPY_AVAILABLE = False
    logger.warning("PsychoPy not found. Please install it: pip install psychopy")

try:
    from gaze_tracking import GazeTracker  # Assumes your gaze tracking module is set up
    GAZE_TRACKER_AVAILABLE = True
except ImportError:
    GAZE_TRACKER_AVAILABLE = False
    logger.warning("GazeTracker module not found. Calibration will not be available.")

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
        logger.error(f"Configuration file not found: {config_path}")
        return {}
    except json.JSONDecodeError:
        logger.error(f"Invalid JSON in configuration file: {config_path}")
        return {}
    except Exception as e:
        logger.error(f"Error loading configuration: {str(e)}")
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
    try:
        return np.sqrt((gaze_x - target_x)**2 + (gaze_y - target_y)**2)
    except Exception as e:
        logger.error(f"Error calculating distance: {str(e)}")
        return float('inf')  # Return infinity to indicate an error

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
    if not PSYCHOPY_AVAILABLE:
        logger.error("PsychoPy not available. Cannot animate point.")
        return
        
    try:
        dot = visual.Circle(win, radius=0.02, fillColor="white", lineColor="white")
        
        for i in range(steps + 1):
            t = i / steps
            x = start_pos[0] + t * (end_pos[0] - start_pos[0])
            y = start_pos[1] + t * (end_pos[1] - start_pos[1])
            dot.pos = (x, y)
            dot.draw()
            win.flip()
            core.wait(duration / steps)
    except Exception as e:
        logger.error(f"Error animating point: {str(e)}")

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
    if not PSYCHOPY_AVAILABLE:
        logger.error("PsychoPy not available. Cannot run calibration.")
        return {"success": False, "error": "PsychoPy not available"}
        
    if not GAZE_TRACKER_AVAILABLE:
        logger.error("GazeTracker not available. Cannot run calibration.")
        return {"success": False, "error": "GazeTracker not available"}
    
    # Set up logging
    try:
        psychopy_logging.console.setLevel(psychopy_logging.INFO)
    except Exception as e:
        logger.warning(f"Could not configure PsychoPy logging: {str(e)}")
    
    # Load configuration
    if config_path is None:
        config_path = os.path.join("Scripts", "calibration_config.json")
    
    config = load_calibration_config(config_path)
    if not config:
        logger.error("Failed to load configuration")
        return {"success": False, "error": "Failed to load configuration"}
        
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
    
    # Create window and initialize tracker
    win = None
    tracker = None
    log_file = None
    
    try:
        win = visual.Window(
            [window_width, window_height], 
            fullscr=full_screen,
            monitor="testMonitor",
            units="norm",
            color="gray"
        )
        
        try:
            tracker = GazeTracker()
            logger.info("Eye tracker initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize eye tracker: {e}")
            if win:
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
            logger.error(f"Failed to create log file: {e}")
            if win:
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
                try:
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
                    logger.error(f"Error acquiring gaze data at point {i}: {str(e)}")
                    log_file.write(f"Calibration, {i}, {point['x']}, {point['y']}, ERROR, ERROR, NA\n")
            
            except Exception as e:
                # Log any error encountered
                if log_file:
                    log_file.write(f"Calibration, {i}, {point['x']}, {point['y']}, ERROR, ERROR, NA\n")
                logger.error(f"Error at calibration point {i}: {e}")
                logger.error(traceback.format_exc())
            
            # Inter-trial interval
            core.wait(inter_trial_interval)
        
        # Calculate average error
        avg_error = np.mean(all_errors) if all_errors else float('inf')
        
        # Display calibration results
        if all_errors:
            result_text = f"Calibration completed.\nAverage error: {avg_error:.3f}\nPress any key to continue."
        else:
            result_text = "Calibration failed. No valid data collected.\nPress any key to continue."
        
        result = visual.TextStim(win, text=result_text)
        result.draw()
        win.flip()
        event.waitKeys()
        
        # Close log file
        if log_file:
            log_file.close()
        
        # Return calibration results
        return {
            "success": len(all_errors) > 0,
            "average_error": avg_error if all_errors else None,
            "log_path": log_path,
            "points_collected": len(all_errors),
            "total_points": len(calibration_points)
        }
        
    except Exception as e:
        logger.error(f"Error during calibration: {str(e)}")
        logger.error(traceback.format_exc())
        
        # Try to display error message
        if win:
            try:
                error_msg = visual.TextStim(
                    win, 
                    text=f"Error during calibration:\n{str(e)}\n\nPress any key to exit.",
                    color="red"
                )
                error_msg.draw()
                win.flip()
                event.waitKeys()
            except:
                pass
        
        return {"success": False, "error": str(e)}
        
    finally:
        # Clean up resources
        if log_file and not log_file.closed:
            try:
                log_file.close()
            except:
                pass
        
        if win:
            try:
                win.close()
            except:
                pass

if __name__ == "__main__":
    # Run calibration as standalone script
    if PSYCHOPY_AVAILABLE and GAZE_TRACKER_AVAILABLE:
        results = run_calibration()
        print(f"Calibration results: {results}")
    else:
        if not PSYCHOPY_AVAILABLE:
            print("PsychoPy not available. Cannot run calibration.")
        if not GAZE_TRACKER_AVAILABLE:
            print("GazeTracker not available. Cannot run calibration.")