"""
main_experiment.py

A full PsychoPy experiment script that:
 • Initializes the PsychoPy window.
 • Begins gaze tracking via a USB webcam (using the gaze_tracking module).
 • Runs a trial loop displaying fixation and stimulus screens.
 • Records gaze tracking data (timestamp, gaze_x, gaze_y) for each trial.
 • Stores the data in a local SQLite database file.
"""

import os
import sqlite3
import json
from psychopy import visual, core, event, gui
from gaze_tracking import GazeTracker  # Make sure this module is in your PYTHONPATH

def init_db(db_path):
    """
    Initialize (or open) a SQLite database and create the gaze_data table if it does not exist.
    """
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS gaze_data (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            trial INTEGER,
            timestamp REAL,
            gaze_x REAL,
            gaze_y REAL
        )
    ''')
    conn.commit()
    return conn

def log_gaze_data(conn, trial, timestamp, gaze_x, gaze_y):
    """
    Insert a row of gaze data into the database.
    """
    cursor = conn.cursor()
    cursor.execute('''
        INSERT INTO gaze_data (trial, timestamp, gaze_x, gaze_y)
        VALUES (?, ?, ?, ?)
    ''', (trial, timestamp, gaze_x, gaze_y))
    conn.commit()

def run_experiment():
    # --- Experiment Parameters ---
    window_width = 1024
    window_height = 768
    full_screen = False
    fixation_duration = 1.0     # seconds for fixation cross display
    stimulus_duration = 2.0     # seconds for stimulus display
    inter_trial_interval = 0.5  # seconds pause between trials
    num_trials = 10             # number of trials in the experiment

    # --- Setup Data Directory and Database ---
    data_dir = os.path.join(os.getcwd(), "Data")
    if not os.path.exists(data_dir):
        os.makedirs(data_dir)
    db_path = os.path.join(data_dir, "gaze_data.db")
    conn = init_db(db_path)
    
    # --- Create PsychoPy Window ---
    win = visual.Window([window_width, window_height], fullscr=full_screen)
    
    # --- Display Instructions ---
    instructions = visual.TextStim(win, text="Welcome to the experiment.\nPress any key to begin.")
    instructions.draw()
    win.flip()
    event.waitKeys()
    
    # --- Initialize Gaze Tracker ---
    try:
        tracker = GazeTracker()
    except Exception as e:
        print("Error initializing Gaze Tracker:", e)
        win.close()
        core.quit()
    
    # Optional: Run calibration routine here if desired.
    # (You might call a separate calibration module here.)

    # --- Begin Trial Loop ---
    for trial in range(1, num_trials + 1):
        # Display fixation cross and record gaze sample during fixation.
        fixation = visual.TextStim(win, text="+", pos=(0, 0), height=0.1)
        fixation.draw()
        win.flip()
        core.wait(fixation_duration)
        
        # Capture gaze data at fixation onset.
        try:
            gaze_sample = tracker.get_gaze_data()  # Expected to return dict with keys 'x' and 'y'
        except Exception as e:
            print(f"Error capturing gaze data on trial {trial}:", e)
            gaze_sample = {"x": None, "y": None}
        
        # Use PsychoPy’s clock to get a timestamp (in seconds)
        timestamp = core.getTime()
        # Log the gaze data for this trial into the database.
        if gaze_sample["x"] is not None and gaze_sample["y"] is not None:
            log_gaze_data(conn, trial, timestamp, gaze_sample["x"], gaze_sample["y"])
        else:
            log_gaze_data(conn, trial, timestamp, None, None)
        
        # Display stimulus (for example, simply the trial number)
        stimulus = visual.TextStim(win, text=f"Trial {trial}", pos=(0, 0))
        stimulus.draw()
        win.flip()
        core.wait(stimulus_duration)
        
        # Inter-trial interval pause
        core.wait(inter_trial_interval)
    
    # --- End of Experiment ---
    thank_you = visual.TextStim(win, text="Thank you for participating!", pos=(0, 0))
    thank_you.draw()
    win.flip()
    core.wait(2.0)
    
    # --- Clean Up Resources ---
    tracker.release()  # Release the webcam resource
    conn.close()       # Close the database connection
    win.close()
    core.quit()

if __name__ == '__main__':
    run_experiment()