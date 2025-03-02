#!/usr/bin/env python
"""
Enhanced PsychoPy experiment with gaze tracking functionality.
Features:
- Comprehensive 9-point calibration with visual feedback
- Continuous gaze data logging to SQLite with participant metadata
- Real-time heat map visualization (toggle with 'h')
- Robust error handling and graceful degradation
- Configuration via external settings file
- Enhanced visualization options
"""

import os
import json
import time
import sqlite3
import numpy as np
import pandas as pd
from datetime import datetime
from psychopy import visual, core, event, gui, monitors, logging
from gaze_tracking import GazeTracker  # Ensure this module is available in your PYTHONPATH

# Configure logging
logging.console.setLevel(logging.WARNING)  # Only show warnings and errors in console

class ExperimentSettings:
    """Settings manager for the experiment"""
    
    DEFAULT_SETTINGS = {
        'window': {
            'width': 1024,
            'height': 768,
            'full_screen': False,
            'monitor_name': 'testMonitor',
            'units': 'norm',
            'color': [-1, -1, -1]  # Black background
        },
        'timing': {
            'fixation_duration': 1.0,
            'stimulus_duration': 2.0,
            'inter_trial_interval': 0.5,
            'calibration_wait': 0.5
        },
        'experiment': {
            'num_trials': 10,
            'data_dir': 'Data',
            'db_name': 'gaze_data.db'
        },
        'calibration': {
            'num_points': 9,  # 3x3 grid
            'point_size': 0.03,
            'point_color': 'red',
            'success_color': 'green',
            'repeat_on_poor_quality': True,
            'quality_threshold': 0.85  # R² threshold for acceptable calibration
        },
        'heatmap': {
            'point_radius': 0.02,
            'color': [1, 0, 0],  # Red
            'opacity': 0.3,
            'decay_rate': 200  # Number of points to keep in buffer
        }
    }
    
    def __init__(self, settings_file='experiment_settings.json'):
        """Initialize settings from file or defaults"""
        self.settings_file = settings_file
        self.settings = self.DEFAULT_SETTINGS.copy()
        self.load_settings()
    
    def load_settings(self):
        """Load settings from JSON file if it exists"""
        if os.path.exists(self.settings_file):
            try:
                with open(self.settings_file, 'r') as f:
                    loaded_settings = json.load(f)
                # Update default settings with loaded values (preserving structure)
                self._update_nested_dict(self.settings, loaded_settings)
                logging.info(f"Settings loaded from {self.settings_file}")
            except Exception as e:
                logging.warning(f"Error loading settings: {e}. Using defaults.")
    
    def _update_nested_dict(self, d, u):
        """Recursively update nested dictionary"""
        for k, v in u.items():
            if isinstance(v, dict) and k in d:
                self._update_nested_dict(d[k], v)
            else:
                d[k] = v
    
    def save_settings(self):
        """Save current settings to JSON file"""
        try:
            with open(self.settings_file, 'w') as f:
                json.dump(self.settings, f, indent=4)
            logging.info(f"Settings saved to {self.settings_file}")
        except Exception as e:
            logging.error(f"Error saving settings: {e}")
    
    def get(self, *args):
        """Get a nested setting value using dot notation"""
        value = self.settings
        for arg in args:
            if arg in value:
                value = value[arg]
            else:
                return None
        return value


class GazeDatabase:
    """SQLite database manager for gaze data"""
    
    def __init__(self, db_path):
        """Initialize database connection and create tables if needed"""
        self.db_path = db_path
        self._init_db()
    
    def _init_db(self):
        """Initialize database schema"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Create participants table
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS participants (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            participant_id TEXT UNIQUE,
            session_timestamp TEXT,
            age INTEGER,
            gender TEXT,
            handedness TEXT,
            notes TEXT
        )
        ''')
        
        # Create calibration table
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS calibration (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            participant_id TEXT,
            timestamp TEXT,
            mapping_params TEXT,
            quality_score REAL,
            FOREIGN KEY (participant_id) REFERENCES participants(participant_id)
        )
        ''')
        
        # Create gaze_data table
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS gaze_data (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            participant_id TEXT,
            trial INTEGER,
            timestamp REAL,
            raw_x REAL,
            raw_y REAL,
            calibrated_x REAL,
            calibrated_y REAL,
            stimulus TEXT,
            event_type TEXT,
            FOREIGN KEY (participant_id) REFERENCES participants(participant_id)
        )
        ''')
        
        conn.commit()
        conn.close()
    
    def add_participant(self, participant_info):
        """Add participant to database"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Extract fields from participant_info
        participant_id = participant_info.get('participant_id', '')
        age = participant_info.get('age', None)
        gender = participant_info.get('gender', '')
        handedness = participant_info.get('handedness', '')
        notes = participant_info.get('notes', '')
        
        # Add timestamp
        session_timestamp = datetime.now().isoformat()
        
        try:
            cursor.execute('''
            INSERT OR REPLACE INTO participants 
            (participant_id, session_timestamp, age, gender, handedness, notes)
            VALUES (?, ?, ?, ?, ?, ?)
            ''', (participant_id, session_timestamp, age, gender, handedness, notes))
            conn.commit()
        except Exception as e:
            logging.error(f"Error adding participant: {e}")
        finally:
            conn.close()
    
    def save_calibration(self, participant_id, mapping_params, quality_score):
        """Save calibration parameters"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        timestamp = datetime.now().isoformat()
        mapping_json = json.dumps(mapping_params)
        
        try:
            cursor.execute('''
            INSERT INTO calibration 
            (participant_id, timestamp, mapping_params, quality_score)
            VALUES (?, ?, ?, ?)
            ''', (participant_id, timestamp, mapping_json, quality_score))
            conn.commit()
        except Exception as e:
            logging.error(f"Error saving calibration: {e}")
        finally:
            conn.close()
    
    def log_gaze_data(self, participant_id, trial, timestamp, raw_x, raw_y, 
                     calibrated_x, calibrated_y, stimulus="", event_type="sample"):
        """Log a gaze data sample"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        try:
            cursor.execute('''
            INSERT INTO gaze_data 
            (participant_id, trial, timestamp, raw_x, raw_y, calibrated_x, calibrated_y, stimulus, event_type)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (participant_id, trial, timestamp, raw_x, raw_y, 
                 calibrated_x, calibrated_y, stimulus, event_type))
            conn.commit()
        except Exception as e:
            logging.error(f"Error logging gaze data: {e}")
        finally:
            conn.close()
    
    def get_participant_data(self, participant_id):
        """Retrieve all gaze data for a participant"""
        conn = sqlite3.connect(self.db_path)
        
        try:
            query = '''
            SELECT * FROM gaze_data 
            WHERE participant_id = ? 
            ORDER BY trial, timestamp
            '''
            df = pd.read_sql_query(query, conn, params=(participant_id,))
            return df
        except Exception as e:
            logging.error(f"Error retrieving participant data: {e}")
            return pd.DataFrame()
        finally:
            conn.close()
    
    def close(self):
        """Close any open connections"""
        # SQLite connections are opened and closed for each operation
        pass


class GazeCalibration:
    """Handle gaze calibration process"""
    
    def __init__(self, win, tracker, settings):
        """Initialize calibration with window, tracker, and settings"""
        self.win = win
        self.tracker = tracker
        self.settings = settings
        self.calibration_data = []
        self.mapping = None
        self.quality_score = 0.0
    
    def get_calibration_points(self):
        """Generate calibration point grid based on settings"""
        num_points = self.settings.get('calibration', 'num_points')
        
        if num_points == 9:  # 3x3 grid
            return [
                (-0.8, 0.8), (0, 0.8), (0.8, 0.8),
                (-0.8, 0),   (0, 0),   (0.8, 0),
                (-0.8, -0.8), (0, -0.8), (0.8, -0.8)
            ]
        elif num_points == 5:  # 5-point calibration
            return [
                (0, 0),         # Center
                (-0.8, 0.8),    # Top-left
                (0.8, 0.8),     # Top-right
                (-0.8, -0.8),   # Bottom-left
                (0.8, -0.8)     # Bottom-right
            ]
        else:  # Default to 3x3 grid
            return [
                (-0.8, 0.8), (0, 0.8), (0.8, 0.8),
                (-0.8, 0),   (0, 0),   (0.8, 0),
                (-0.8, -0.8), (0, -0.8), (0.8, -0.8)
            ]
    
    def run_calibration(self):
        """Run calibration procedure"""
        calibration_points = self.get_calibration_points()
        point_size = self.settings.get('calibration', 'point_size')
        point_color = self.settings.get('calibration', 'point_color')
        success_color = self.settings.get('calibration', 'success_color')
        wait_time = self.settings.get('timing', 'calibration_wait')
        
        # Display instructions
        instructions = visual.TextStim(
            self.win, 
            text="Calibration: Look at each red dot and press SPACE.\nPress ESC to quit.", 
            pos=(0, 0.9), 
            height=0.05
        )
        instructions.draw()
        self.win.flip()
        core.wait(2.0)
        
        # Clear previous calibration data
        self.calibration_data = []
        
        # Calibration loop
        for i, point in enumerate(calibration_points):
            # Draw the calibration point
            dot = visual.Circle(
                self.win, 
                radius=point_size, 
                fillColor=point_color, 
                lineColor=point_color, 
                pos=point
            )
            
            # Draw progress indicator
            progress = visual.TextStim(
                self.win,
                text=f"Point {i+1}/{len(calibration_points)}",
                pos=(0, -0.9),
                height=0.05
            )
            
            # Draw screen elements
            dot.draw()
            instructions.draw()
            progress.draw()
            self.win.flip()
            
            # Wait for spacebar or escape
            event.clearEvents()
            while True:
                keys = event.getKeys(keyList=['space', 'escape'])
                if 'escape' in keys:
                    return False  # Calibration aborted
                if 'space' in keys:
                    # Get current gaze data with multiple samples for stability
                    gaze_samples = []
                    for _ in range(3):  # Take 3 samples
                        sample = self.tracker.get_gaze_data()
                        if sample and sample.get("x") is not None and sample.get("y") is not None:
                            gaze_samples.append((sample["x"], sample["y"]))
                        core.wait(0.05)  # Brief pause between samples
                    
                    if gaze_samples:
                        # Average the samples
                        avg_x = sum(x for x, _ in gaze_samples) / len(gaze_samples)
                        avg_y = sum(y for _, y in gaze_samples) / len(gaze_samples)
                        
                        # Convert pixel coordinates to normalized coordinates
                        win_width, win_height = self.win.size
                        observed_x = (avg_x - win_width / 2) / (win_width / 2)
                        observed_y = (win_height / 2 - avg_y) / (win_height / 2)
                        
                        # Store calibration point: (expected_x, expected_y, observed_x, observed_y)
                        self.calibration_data.append((point[0], point[1], observed_x, observed_y))
                        
                        # Visual feedback of successful capture
                        success_dot = visual.Circle(
                            self.win, 
                            radius=point_size, 
                            fillColor=success_color, 
                            lineColor=success_color, 
                            pos=point
                        )
                        success_dot.draw()
                        instructions.draw()
                        progress.draw()
                        self.win.flip()
                    
                    break
            
            # Brief pause before next point
            core.wait(wait_time)
        
        # Compute calibration mapping
        success = self.compute_calibration_mapping()
        
        # Display calibration quality
        quality_text = f"Calibration quality: {self.quality_score:.2f}"
        if self.quality_score < self.settings.get('calibration', 'quality_threshold'):
            quality_text += "\nCalibration quality is poor. Press R to recalibrate or C to continue."
            should_repeat = True
        else:
            quality_text += "\nPress any key to continue."
            should_repeat = False
        
        quality_msg = visual.TextStim(self.win, text=quality_text, pos=(0, 0), height=0.05)
        quality_msg.draw()
        self.win.flip()
        
        # Wait for response if quality is poor
        if should_repeat and self.settings.get('calibration', 'repeat_on_poor_quality'):
            keys = event.waitKeys(keyList=['r', 'c', 'escape'])
            if 'escape' in keys:
                return False
            if 'r' in keys:
                return self.run_calibration()  # Recursive call to repeat calibration
        else:
            event.waitKeys()
        
        return success
    
    def compute_calibration_mapping(self):
        """Compute calibration parameters and quality score"""
        if len(self.calibration_data) < 5:  # Need at least 5 points for reliable calibration
            logging.warning("Insufficient calibration data points")
            self.mapping = (1, 0, 1, 0)  # Identity mapping
            self.quality_score = 0.0
            return False
        
        try:
            # Extract data points
            expected_x = np.array([d[0] for d in self.calibration_data])
            expected_y = np.array([d[1] for d in self.calibration_data])
            observed_x = np.array([d[2] for d in self.calibration_data])
            observed_y = np.array([d[3] for d in self.calibration_data])
            
            # Compute linear regression parameters
            a_x, b_x = np.polyfit(observed_x, expected_x, 1)
            a_y, b_y = np.polyfit(observed_y, expected_y, 1)
            
            # Calculate R² (coefficient of determination) as quality score
            x_fitted = a_x * observed_x + b_x
            y_fitted = a_y * observed_y + b_y
            
            ss_res_x = np.sum((expected_x - x_fitted) ** 2)
            ss_tot_x = np.sum((expected_x - np.mean(expected_x)) ** 2)
            r2_x = 1 - (ss_res_x / ss_tot_x) if ss_tot_x != 0 else 0
            
            ss_res_y = np.sum((expected_y - y_fitted) ** 2)
            ss_tot_y = np.sum((expected_y - np.mean(expected_y)) ** 2)
            r2_y = 1 - (ss_res_y / ss_tot_y) if ss_tot_y != 0 else 0
            
            # Average R² as overall quality score
            self.quality_score = (r2_x + r2_y) / 2
            
            # Store calibration parameters
            self.mapping = (a_x, b_x, a_y, b_y)
            
            logging.info(f"Calibration mapping: {self.mapping}, Quality: {self.quality_score:.2f}")
            return True
        
        except Exception as e:
            logging.error(f"Error computing calibration: {e}")
            self.mapping = (1, 0, 1, 0)  # Identity mapping
            self.quality_score = 0.0
            return False
    
    def apply_calibration(self, observed_x, observed_y):
        """Apply calibration mapping to observed coordinates"""
        if self.mapping is None:
            return observed_x, observed_y
        
        a_x, b_x, a_y, b_y = self.mapping
        calibrated_x = a_x * observed_x + b_x
        calibrated_y = a_y * observed_y + b_y
        return calibrated_x, calibrated_y
    
    def get_mapping_params(self):
        """Return calibration mapping parameters"""
        return self.mapping
    
    def get_quality_score(self):
        """Return calibration quality score"""
        return self.quality_score


class HeatmapVisualizer:
    """Manage gaze heatmap visualization"""
    
    def __init__(self, win, settings):
        """Initialize visualizer with window and settings"""
        self.win = win
        self.settings = settings
        self.heatmap_buffer = []
        self.active = False
        self.decay_rate = settings.get('heatmap', 'decay_rate')
        self.point_radius = settings.get('heatmap', 'point_radius')
        self.point_color = settings.get('heatmap', 'color')
        self.opacity = settings.get('heatmap', 'opacity')
    
    def toggle(self):
        """Toggle heatmap display on/off"""
        self.active = not self.active
        return self.active
    
    def add_point(self, point):
        """Add a calibrated gaze point to the buffer"""
        self.heatmap_buffer.append(point)
        # Limit buffer size to prevent performance issues
        if len(self.heatmap_buffer) > self.decay_rate:
            self.heatmap_buffer.pop(0)
    
    def draw(self):
        """Draw heatmap if active"""
        if not self.active:
            return
        
        for i, point in enumerate(self.heatmap_buffer):
            # Newer points are more opaque
            point_opacity = self.opacity * min(1.0, (i + 1) / len(self.heatmap_buffer))
            
            circle = visual.Circle(
                self.win, 
                radius=self.point_radius, 
                fillColor=self.point_color, 
                lineColor=None, 
                opacity=point_opacity, 
                pos=point
            )
            circle.draw()
    
    def clear(self):
        """Clear heatmap buffer"""
        self.heatmap_buffer = []


class ExperimentRunner:
    """Main experiment controller"""
    
    def __init__(self):
        """Initialize experiment resources"""
        self.settings = ExperimentSettings()
        self.setup_experiment()
    
    def setup_experiment(self):
        """Set up experiment resources"""
        # Create data directory
        data_dir = os.path.join(os.getcwd(), self.settings.get('experiment', 'data_dir'))
        if not os.path.exists(data_dir):
            os.makedirs(data_dir)
        
        # Initialize database
        db_path = os.path.join(data_dir, self.settings.get('experiment', 'db_name'))
        self.db = GazeDatabase(db_path)
        
        # Set up monitor
        mon = monitors.Monitor(self.settings.get('window', 'monitor_name'))
        
        # Create PsychoPy window
        self.win = visual.Window(
            size=[self.settings.get('window', 'width'), self.settings.get('window', 'height')],
            fullscr=self.settings.get('window', 'full_screen'),
            monitor=mon,
            units=self.settings.get('window', 'units'),
            color=self.settings.get('window', 'color'),
            allowGUI=False
        )
        
        # Initialize clock
        self.clock = core.Clock()
    
    def collect_participant_info(self):
        """Collect participant information"""
        # Basic info
        info = {
            'participant_id': '',
            'age': '',
            'gender': ['Male', 'Female', 'Non-binary', 'Prefer not to say'],
            'handedness': ['Right', 'Left', 'Ambidextrous'],
            'notes': ''
        }
        
        # Create dialog
        dlg = gui.DlgFromDict(
            dictionary=info,
            title="Experiment Information"
        )
        
        # Exit if canceled
        if not dlg.OK:
            self.cleanup()
            core.quit()
        
        # Convert age to integer if possible
        try:
            if info['age']:
                info['age'] = int(info['age'])
        except ValueError:
            info['age'] = None
        
        # Add participant to database
        self.db.add_participant(info)
        
        return info
    
    def initialize_tracker(self):
        """Initialize gaze tracker"""
        try:
            tracker = GazeTracker()
            return tracker
        except Exception as e:
            error_msg = f"Error initializing Gaze Tracker: {e}"
            logging.error(error_msg)
            
            # Display error message
            error_text = visual.TextStim(
                self.win,
                text=f"{error_msg}\n\nPress any key to exit.",
                pos=(0, 0),
                color='red',
                height=0.05
            )
            error_text.draw()
            self.win.flip()
            event.waitKeys()
            
            self.cleanup()
            core.quit()
    
    def show_instructions(self, text, duration=None, wait_for_key=False, key_list=None):
        """Display instructions on screen"""
        instructions = visual.TextStim(
            self.win,
            text=text,
            pos=(0, 0),
            height=0.05,
            wrapWidth=1.8
        )
        instructions.draw()
        self.win.flip()
        
        if duration is not None:
            core.wait(duration)
        elif wait_for_key:
            if key_list:
                keys = event.waitKeys(keyList=key_list)
            else:
                keys = event.waitKeys()
            return keys
        else:
            event.waitKeys()
    
    def run_trials(self, participant_id, calibration):
        """Run experimental trials"""
        # Get experiment parameters
        num_trials = self.settings.get('experiment', 'num_trials')
        fixation_duration = self.settings.get('timing', 'fixation_duration')
        stimulus_duration = self.settings.get('timing', 'stimulus_duration')
        inter_trial_interval = self.settings.get('timing', 'inter_trial_interval')
        
        # Initialize heatmap
        heatmap = HeatmapVisualizer(self.win, self.settings)
        
        # Create stimuli
        fixation = visual.TextStim(self.win, text="+", pos=(0, 0), height=0.2)
        
        # Reset clock
        self.clock.reset()
        
        # Begin trial loop
        for trial in range(1, num_trials + 1):
            # Check for keypress events (heatmap toggle or quit)
            keys = event.getKeys(keyList=['h', 'escape', 'q'])
            if 'escape' in keys or 'q' in keys:
                break
            if 'h' in keys:
                heatmap.toggle()
            
            # --- Fixation phase ---
            fixation.draw()
            if heatmap.active:
                heatmap.draw()
            self.win.flip()
            
            # Log fixation onset
            timestamp = self.clock.getTime()
            self.db.log_gaze_data(
                participant_id, trial, timestamp,
                None, None, None, None,
                "fixation", "onset"
            )
            
            # Wait for fixation duration while collecting samples
            fixation_start = core.getTime()
            while core.getTime() - fixation_start < fixation_duration:
                try:
                    gaze_sample = self.tracker.get_gaze_data()
                    if gaze_sample and gaze_sample.get("x") is not None and gaze_sample.get("y") is not None:
                        # Convert to normalized coordinates
                        win_width, win_height = self.win.size
                        observed_x = (gaze_sample["x"] - win_width/2) / (win_width/2)
                        observed_y = (win_height/2 - gaze_sample["y"]) / (win_height/2)
                        
                        # Apply calibration
                        calibrated_x, calibrated_y = calibration.apply_calibration(observed_x, observed_y)
                        
                        # Log sample
                        sample_time = self.clock.getTime()
                        self.db.log_gaze_data(
                            participant_id, trial, sample_time,
                            observed_x, observed_y, calibrated_x, calibrated_y,
                            "fixation", "sample"
                        )
                        
                        # Add to heatmap
                        heatmap.add_point((calibrated_x, calibrated_y))
                except Exception as e:
                    logging.warning(f"Error capturing gaze during fixation: {e}")
                
                if event.getKeys(keyList=['escape', 'q']):
                    return
            
            # --- Stimulus phase ---
            stimulus = visual.TextStim(
                self.win, 
                text=f"Trial {trial}", 
                pos=(0, 0), 
                height=0.1
            )
            
            stimulus.draw()
            if heatmap.active:
                heatmap.draw()
            self.win.flip()
            
            # Log stimulus onset
            timestamp = self.clock.getTime()
            self.db.log_gaze_data(
                participant_id, trial, timestamp,
                None, None, None, None,
                f"stimulus_{trial}", "onset"
            )
            
            # Wait for stimulus duration while collecting samples
            stim_start = core.getTime()
            while core.getTime() - stim_start < stimulus_duration:
                try:
                    gaze_sample = self.tracker.get_gaze_data()
                    if gaze_sample and gaze_sample.get("x") is not None and gaze_sample.get("y") is not None:
                        # Convert to normalized coordinates
                        win_width, win_height = self.win.size
                        observed_x = (gaze_sample["x"] - win_width/2) / (win_width/2)
                        observed_y = (win_height/2 - gaze_sample["y"]) / (win_height/2)
                        
                        # Apply calibration
                        calibrated_x, calibrated_y = calibration.apply_calibration(observed_x, observed_y)
                        
                        # Log sample
                        sample_time = self.clock.getTime()
                        self.db.log_gaze_data(
                            participant_id, trial, sample_time,
                            observed_x, observed_y, calibrated_x, calibrated_y,
                            f"stimulus_{trial}", "sample"
                        )
                        
                        # Add to heatmap
                        heatmap.add_point((calibrated_x, calibrated_y))
                except Exception as e:
                    logging.warning(f"Error capturing gaze during stimulus: {e}")
                
                if event.getKeys(keyList=['escape', 'q']):
                    return
            
            # --- Inter-trial interval ---
            self.win.flip()  # Clear screen
            core.wait(inter_trial_interval)
    
    def run_experiment(self):
        """Run the full experiment procedure"""
        try:
            # Display welcome screen
            self.show_instructions(
                "Welcome to the experiment.\n\n"
                "You will see a series of stimuli while your eye movements are tracked.\n\n"
                "Press any key to begin.",
                wait_for_key=True
            )
            
            # Collect participant information
            participant_info = self.collect_participant_info()
            participant_id = participant_info['participant_id']
            
            # Initialize gaze tracker
            self.tracker = self.initialize_tracker()
            
            # Create calibration handler
            calibration = GazeCalibration(self.win, self.tracker, self.settings)
            
            # Run calibration
            cal_success = calibration.run_calibration()
            if not cal_success:
                self.show_instructions("Calibration aborted or failed. Exiting experiment.", wait_for_key=True)
                self.cleanup()
                core.quit()
            
            # Save calibration parameters in database
            self.db.save_calibration(participant_id, calibration.get_mapping_params(), calibration.get_quality_score())
            
            # Confirm calibration success before starting trials
            self.show_instructions("Calibration completed successfully.\nPress any key to begin the trials.", wait_for_key=True)
            
            # Run experimental trials
            self.run_trials(participant_id, calibration)
            
            # Show debriefing message
            self.show_instructions("Experiment completed.\nThank you for your participation!\nPress any key to exit.", wait_for_key=True)
            
        except Exception as e:
            logging.error(f"Experiment error: {e}")
        finally:
            self.cleanup()
    
    def cleanup(self):
        """Clean up resources"""
        if self.win:
            self.win.close()
        core.quit()


if __name__ == '__main__':
    experiment = ExperimentRunner()
    experiment.run_experiment()