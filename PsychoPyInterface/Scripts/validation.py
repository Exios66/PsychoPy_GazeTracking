# Scripts/validation.py
import os
import json
import logging
import traceback
from datetime import datetime
import sys

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('validation')

# Import local modules with error handling
try:
    from logging_utils import create_log_file, log_message, close_log_file
    LOGGING_UTILS_AVAILABLE = True
except ImportError as e:
    logger.error(f"Error importing logging_utils: {str(e)}")
    logger.error(traceback.format_exc())
    LOGGING_UTILS_AVAILABLE = False

# Try to import PsychoPy with error handling
try:
    from psychopy import visual, core, event
    PSYCHOPY_AVAILABLE = True
except ImportError:
    logger.error("PsychoPy not found. Please install it using: pip install psychopy")
    PSYCHOPY_AVAILABLE = False

# Try to import EyeTracker with error handling
try:
    from utils.eye_tracker import EyeTracker
    EYETRACKER_AVAILABLE = True
except ImportError as e:
    logger.error(f"Error importing EyeTracker: {str(e)}")
    logger.error(traceback.format_exc())
    EYETRACKER_AVAILABLE = False

def load_calibration_config(config_path=None):
    """
    Load calibration configuration from a JSON file.
    
    Parameters:
    -----------
    config_path : str, optional
        Path to the configuration file
        
    Returns:
    --------
    dict
        Configuration dictionary or default values if loading fails
    """
    if config_path is None:
        config_path = os.path.join(os.getcwd(), "Scripts", "calibration_config.json")
    
    default_config = {
        "window_width": 1024,
        "window_height": 768,
        "full_screen": False,
        "fixation_duration": 1.0,
        "inter_trial_interval": 0.5,
        "validation_points": [
            {"x": 0, "y": 0},
            {"x": -0.5, "y": -0.5},
            {"x": 0.5, "y": 0.5},
            {"x": -0.5, "y": 0.5},
            {"x": 0.5, "y": -0.5}
        ],
        "dot_size": 0.05,
        "validation_threshold": 0.2
    }
    
    try:
        if os.path.exists(config_path):
            with open(config_path, "r") as f:
                config = json.load(f)
                logger.info(f"Configuration loaded from {config_path}")
                return config
        else:
            logger.warning(f"Configuration file not found at {config_path}. Using default values.")
            return default_config
    except Exception as e:
        logger.error(f"Error loading configuration: {str(e)}")
        logger.error(traceback.format_exc())
        logger.warning("Using default configuration values.")
        return default_config

def setup_data_directory():
    """
    Create data directory if it doesn't exist.
    
    Returns:
    --------
    str
        Path to the data directory
    """
    data_dir = os.path.join(os.getcwd(), "Data")
    try:
        os.makedirs(data_dir, exist_ok=True)
        logger.info(f"Data directory set up at {data_dir}")
        return data_dir
    except Exception as e:
        logger.error(f"Error creating data directory: {str(e)}")
        logger.error(traceback.format_exc())
        # Fall back to current directory
        return os.getcwd()

def calculate_error(gaze_point, target_point):
    """
    Calculate the Euclidean distance between gaze and target points.
    
    Parameters:
    -----------
    gaze_point : dict
        Dictionary with 'x' and 'y' keys for gaze coordinates
    target_point : dict
        Dictionary with 'x' and 'y' keys for target coordinates
        
    Returns:
    --------
    float
        Euclidean distance between the points
    """
    try:
        error_x = abs(gaze_point.get("x", 0) - target_point["x"])
        error_y = abs(gaze_point.get("y", 0) - target_point["y"])
        return (error_x**2 + error_y**2)**0.5
    except Exception as e:
        logger.error(f"Error calculating distance: {str(e)}")
        return float('inf')  # Return infinity to indicate error

def run_validation(config=None, tracker=None):
    """
    Run the validation procedure.
    
    Parameters:
    -----------
    config : dict, optional
        Configuration dictionary
    tracker : EyeTracker, optional
        Initialized eye tracker instance
        
    Returns:
    --------
    dict
        Validation results including average error and success status
    """
    # Check if required modules are available
    if not PSYCHOPY_AVAILABLE:
        logger.error("Cannot run validation: PsychoPy is not available")
        return {"success": False, "error": "PsychoPy not available"}
    
    if not EYETRACKER_AVAILABLE:
        logger.error("Cannot run validation: EyeTracker is not available")
        return {"success": False, "error": "EyeTracker not available"}
    
    # Load configuration if not provided
    if config is None:
        config = load_calibration_config()
    
    # Set up data directory
    data_dir = setup_data_directory()
    
    # Create a unique log file name with timestamp
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    log_path = os.path.join(data_dir, f"validation_log_{timestamp}.csv")
    
    # Extract configuration parameters
    window_width = config.get("window_width", 1024)
    window_height = config.get("window_height", 768)
    full_screen = config.get("full_screen", False)
    fixation_duration = config.get("fixation_duration", 1.0)
    inter_trial_interval = config.get("inter_trial_interval", 0.5)
    # Use validation_points if provided; otherwise default to calibration_points
    validation_points = config.get("validation_points", config.get("calibration_points", []))
    dot_size = config.get("dot_size", 0.05)
    validation_threshold = config.get("validation_threshold", 0.2)
    
    win = None
    log_file = None
    
    try:
        # Create window
        win = visual.Window(
            [window_width, window_height], 
            fullscr=full_screen,
            allowGUI=True,
            monitor='testMonitor',
            units='height'
        )
        
        # Initialize tracker if not provided
        if tracker is None:
            tracker = EyeTracker(win, tracker_type='webgazer')
        
        # Create and open a log file for validation data
        header = "PointIndex,ConfigX,ConfigY,GazeX,GazeY,Error,Timestamp"
        if LOGGING_UTILS_AVAILABLE:
            log_file = create_log_file(log_path, header=header)
            if log_file is None:
                logger.error("Failed to create log file. Aborting validation.")
                win.close()
                return {"success": False, "error": "Failed to create log file"}
        else:
            try:
                os.makedirs(os.path.dirname(log_path), exist_ok=True)
                log_file = open(log_path, "w")
                log_file.write(f"{header}\n")
            except Exception as e:
                logger.error(f"Error creating log file: {str(e)}")
                win.close()
                return {"success": False, "error": f"Failed to create log file: {str(e)}"}
        
        # Display instructions
        instruction = visual.TextStim(
            win, 
            text="Validation:\nPlease follow the dot on the screen.\nPress any key to begin.",
            height=0.05
        )
        instruction.draw()
        win.flip()
        event.waitKeys()
        
        # Run validation procedure
        error_sum = 0
        valid_points = 0
        point_errors = []
        
        for i, point in enumerate(validation_points, start=1):
            try:
                # Check for quit keys
                if event.getKeys(keyList=["escape", "q"]):
                    logger.info("Validation terminated by user")
                    break
                
                # Draw validation dot
                dot = visual.Circle(
                    win, 
                    radius=dot_size, 
                    fillColor="green", 
                    lineColor="green", 
                    pos=(point["x"], point["y"])
                )
                dot.draw()
                win.flip()
                core.wait(fixation_duration)
                
                # Acquire gaze data and compute error
                gaze_position = tracker.get_gaze_position()
                
                if gaze_position is None:
                    logger.warning(f"No gaze data received for point {i}")
                    gaze_data = {"x": "NA", "y": "NA"}
                    error = "NA"
                else:
                    gaze_data = {"x": gaze_position[0], "y": gaze_position[1]}
                    error = calculate_error(gaze_data, point)
                    error_sum += error
                    valid_points += 1
                    point_errors.append(error)
                
                # Log data
                timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f")[:-3]
                log_entry = f"{i},{point['x']},{point['y']},{gaze_data.get('x')},{gaze_data.get('y')},{error},{timestamp}"
                
                if LOGGING_UTILS_AVAILABLE:
                    log_message(log_file, log_entry, include_timestamp=False)
                else:
                    log_file.write(f"{log_entry}\n")
                    log_file.flush()
            
            except Exception as e:
                logger.error(f"Error at validation point {i}: {str(e)}")
                logger.error(traceback.format_exc())
                
                # Log error
                timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f")[:-3]
                log_entry = f"{i},{point['x']},{point['y']},ERROR,ERROR,ERROR,{timestamp}"
                
                if LOGGING_UTILS_AVAILABLE:
                    log_message(log_file, log_entry, include_timestamp=False)
                else:
                    log_file.write(f"{log_entry}\n")
                    log_file.flush()
            
            # Inter-trial interval
            core.wait(inter_trial_interval)
        
        # Calculate average error
        avg_error = error_sum / valid_points if valid_points > 0 else float('inf')
        validation_success = avg_error <= validation_threshold if valid_points > 0 else False
        
        # Log summary
        summary = f"Average Error: {avg_error}, Valid Points: {valid_points}/{len(validation_points)}, Success: {validation_success}"
        logger.info(summary)
        
        if LOGGING_UTILS_AVAILABLE:
            log_message(log_file, f"Summary,{summary}", include_timestamp=True)
        else:
            log_file.write(f"Summary,{summary}\n")
            log_file.flush()
        
        # Display validation result message
        if validation_success:
            result_text = f"Validation successful!\nAverage error: {avg_error:.2f}\nValid points: {valid_points}/{len(validation_points)}\nPress any key to continue."
        else:
            result_text = (f"Validation not successful.\nAverage error: {avg_error:.2f} "
                          f"(Threshold: {validation_threshold})\nValid points: {valid_points}/{len(validation_points)}\n"
                          f"Consider recalibrating.\nPress any key to continue.")
        
        result = visual.TextStim(win, text=result_text, height=0.05)
        result.draw()
        win.flip()
        event.waitKeys()
        
        # Close resources
        if LOGGING_UTILS_AVAILABLE:
            close_log_file(log_file)
        else:
            log_file.close()
        
        win.close()
        
        # Return validation results
        return {
            "success": validation_success,
            "average_error": avg_error,
            "valid_points": valid_points,
            "total_points": len(validation_points),
            "point_errors": point_errors,
            "log_path": log_path
        }
        
    except Exception as e:
        logger.error(f"Error during validation: {str(e)}")
        logger.error(traceback.format_exc())
        
        # Clean up resources
        try:
            if log_file:
                if LOGGING_UTILS_AVAILABLE:
                    close_log_file(log_file)
                else:
                    log_file.close()
            if win:
                win.close()
        except:
            pass
        
        return {
            "success": False,
            "error": str(e),
            "log_path": log_path if 'log_path' in locals() else None
        }

if __name__ == '__main__':
    result = run_validation()
    if not result.get("success", False):
        logger.error(f"Validation failed: {result.get('error', 'Unknown error')}")
        sys.exit(1)
    sys.exit(0)