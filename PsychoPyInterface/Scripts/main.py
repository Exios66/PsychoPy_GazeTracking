# Scripts/main.py
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
logger = logging.getLogger('main')

# Import local modules with error handling
try:
    from gaze_tracking import GazeTracker
    from logging_utils import create_log_file, log_message, close_log_file
    GAZE_TRACKER_AVAILABLE = True
except ImportError as e:
    logger.error(f"Error importing local modules: {str(e)}")
    logger.error(traceback.format_exc())
    GAZE_TRACKER_AVAILABLE = False

# Try to import PsychoPy with error handling
try:
    from psychopy import visual, event, core, gui
    PSYCHOPY_AVAILABLE = True
except ImportError:
    logger.error("PsychoPy not found. Please install it using: pip install psychopy")
    PSYCHOPY_AVAILABLE = False

def load_config(config_path=None):
    """
    Load configuration from a JSON file.
    
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
        config_path = os.path.join(os.getcwd(), "Scripts", "config.json")
    
    default_config = {
        "window_width": 800,
        "window_height": 600,
        "full_screen": False,
        "num_trials": 10,
        "fixation_duration": 1.0,
        "stimulus_duration": 2.0,
        "iti_duration": 0.5
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

def run_experiment(config=None):
    """
    Run the main experiment.
    
    Parameters:
    -----------
    config : dict, optional
        Configuration dictionary
        
    Returns:
    --------
    bool
        True if experiment completed successfully, False otherwise
    """
    # Check if required modules are available
    if not PSYCHOPY_AVAILABLE:
        logger.error("Cannot run experiment: PsychoPy is not available")
        return False
    
    if not GAZE_TRACKER_AVAILABLE:
        logger.error("Cannot run experiment: GazeTracker is not available")
        return False
    
    # Load configuration if not provided
    if config is None:
        config = load_config()
    
    # Set up data directory
    data_dir = setup_data_directory()
    
    # Create a unique log file name with timestamp
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    data_log_path = os.path.join(data_dir, f"experiment_log_{timestamp}.csv")
    
    try:
        # Create a window
        win = visual.Window(
            [config.get("window_width", 800), config.get("window_height", 600)],
            fullscr=config.get("full_screen", False),
            allowGUI=True,
            monitor='testMonitor',
            units='height'
        )
        
        # Initialize gaze tracker
        tracker = GazeTracker()
        
        # Display instructions
        instruction_text = visual.TextStim(
            win, 
            text="Focus on the center and press any key to begin.",
            height=0.05
        )
        instruction_text.draw()
        win.flip()
        event.waitKeys()
        
        # Create a log file for data
        log_file = create_log_file(data_log_path, header="Trial,GazeX,GazeY,Timestamp")
        if log_file is None:
            logger.error("Failed to create log file. Aborting experiment.")
            win.close()
            return False
        
        # Example trial loop
        num_trials = config.get("num_trials", 10)
        fixation_duration = config.get("fixation_duration", 1.0)
        stimulus_duration = config.get("stimulus_duration", 2.0)
        iti_duration = config.get("iti_duration", 0.5)
        
        logger.info(f"Starting experiment with {num_trials} trials")
        
        for trial in range(1, num_trials + 1):
            # Check for quit keys
            if event.getKeys(keyList=["escape", "q"]):
                logger.info("Experiment terminated by user")
                break
                
            # Display fixation cross
            fixation = visual.TextStim(win, text="+", height=0.1)
            fixation.draw()
            win.flip()
            core.wait(fixation_duration)
            
            # Acquire gaze data sample at fixation onset
            try:
                gaze_sample = tracker.get_gaze_data()
                gaze_x = gaze_sample.get('x', 'NA')
                gaze_y = gaze_sample.get('y', 'NA')
            except Exception as e:
                logger.error(f"Error acquiring gaze data: {str(e)}")
                gaze_x = "ERROR"
                gaze_y = "ERROR"
            
            # Display stimulus (for example, trial number)
            stimulus = visual.TextStim(win, text=f"Trial {trial}", pos=(0, 0))
            stimulus.draw()
            win.flip()
            core.wait(stimulus_duration)
            
            # Log trial data (gaze coordinates)
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f")[:-3]
            log_message(log_file, f"{trial},{gaze_x},{gaze_y},{timestamp}", include_timestamp=False)
            
            # Allow short inter-trial interval
            core.wait(iti_duration)
        
        # End experiment
        thank_you = visual.TextStim(win, text="Thank you for participating!")
        thank_you.draw()
        win.flip()
        core.wait(2.0)
        
        # Close log file
        close_log_file(log_file)
        
        # Clean up
        win.close()
        logger.info("Experiment completed successfully")
        return True
        
    except Exception as e:
        logger.error(f"Error during experiment: {str(e)}")
        logger.error(traceback.format_exc())
        try:
            # Try to clean up resources
            if 'win' in locals() and win is not None:
                win.close()
            if 'log_file' in locals() and log_file is not None:
                close_log_file(log_file)
        except:
            pass
        return False

if __name__ == "__main__":
    success = run_experiment()
    if not success:
        logger.error("Experiment did not complete successfully")
        sys.exit(1)
    sys.exit(0)