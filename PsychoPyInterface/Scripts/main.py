# Scripts/main.py
from psychopy import visual, event, core, gui
from gaze_tracking import GazeTracker
import json
import os

# Load configuration (if needed)
with open(os.path.join(os.getcwd(), "Scripts", "config.json"), "r") as f:
    config = json.load(f)

# Create a window
win = visual.Window([config.get("window_width", 800), config.get("window_height", 600)], 
                    fullscr=config.get("full_screen", False))

# Initialize gaze tracker
tracker = GazeTracker()

# Display instructions
instruction_text = visual.TextStim(win, text="Focus on the center and press any key to begin.")
instruction_text.draw()
win.flip()
event.waitKeys()

# Create a log file for data
data_log = os.path.join(os.getcwd(), "Data", "experiment_log.txt")
with open(data_log, "w") as log_file:
    log_file.write("Trial, GazeX, GazeY\n")

# Example trial loop (10 trials)
for trial in range(1, 11):
    # Display fixation cross
    fixation = visual.TextStim(win, text="+", height=0.1)
    fixation.draw()
    win.flip()
    core.wait(1.0)  # fixation duration
    
    # Acquire gaze data sample at fixation onset
    gaze_sample = tracker.get_gaze_data()
    
    # Display stimulus (for example, trial number)
    stimulus = visual.TextStim(win, text=f"Trial {trial}", pos=(0, 0))
    stimulus.draw()
    win.flip()
    core.wait(2.0)  # stimulus duration
    
    # Log trial data (gaze coordinates)
    with open(data_log, "a") as log_file:
        log_file.write(f"{trial}, {gaze_sample['x']}, {gaze_sample['y']}\n")
    
    # Allow short inter-trial interval
    core.wait(0.5)

# End experiment
thank_you = visual.TextStim(win, text="Thank you for participating!")
thank_you.draw()
win.flip()
core.wait(2.0)
win.close()
core.quit()