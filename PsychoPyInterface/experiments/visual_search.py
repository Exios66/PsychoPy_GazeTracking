#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Visual Search Experiment

This experiment presents a visual search task where participants
search for a target among distractors while their eye movements
are tracked.

Features:
- Configurable set sizes and trial parameters
- Comprehensive eye movement tracking and analysis
- Adaptive difficulty based on performance
- Detailed data logging and visualization
- Robust error handling and recovery
"""

import os
import json
import random
import numpy as np
import logging
import time
import csv
from pathlib import Path
from datetime import datetime
import matplotlib.pyplot as plt
import traceback
from collections import defaultdict

# Try to import PsychoPy with error handling
try:
    from psychopy import visual, core, event, data, gui, monitors
    from psychopy.hardware import keyboard
    PSYCHOPY_AVAILABLE = True
except ImportError:
    PSYCHOPY_AVAILABLE = False
    logging.warning("PsychoPy not found. Please install it: pip install psychopy")

from ..utils import EyeTracker
from ..config import DEFAULT_EXPERIMENT_SETTINGS, DATA_DIR
from ..Scripts.adaptive_control import check_calibration_and_adapt
from ..Scripts.adaptive_file_control import run_adaptive_trial_control


# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('VisualSearchExperiment')


class VisualSearchExperiment:
    """Visual search experiment with eye tracking and adaptive control."""

    def __init__(self, settings=None, participant_id=None, session_id=None):
        """
        Initialize the experiment.

        Parameters
        ----------
        settings : dict, optional
            Experiment settings. If None, default settings will be used.
        participant_id : str, optional
            Participant identifier. If None, will be requested via GUI.
        session_id : str, optional
            Session identifier. If None, will be generated automatically.
        """
        # Check if PsychoPy is available
        if not PSYCHOPY_AVAILABLE:
            raise ImportError("PsychoPy is required to run this experiment. Please install it: pip install psychopy")
            
        # Merge settings with defaults
        self.settings = DEFAULT_EXPERIMENT_SETTINGS.copy()
        if settings:
            self.settings.update(settings)
        
        # Initialize experiment components
        self.win = None
        self.tracker = None
        self.kb = None
        self.clock = core.Clock()
        self.global_clock = core.Clock()  # For overall experiment timing
        
        # Set up session identifiers
        self.participant_id = participant_id
        self.session_id = session_id or datetime.now().strftime("%Y%m%d_%H%M%S")
        self.data_dir = DATA_DIR / f"P{self.participant_id}" / self.session_id if self.participant_id else DATA_DIR / self.session_id
        os.makedirs(self.data_dir, exist_ok=True)
        
        # Set up logging to file
        self.log_file = self.data_dir / "experiment.log"
        file_handler = logging.FileHandler(self.log_file)
        file_handler.setFormatter(logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s'))
        logger.addHandler(file_handler)
        
        logger.info(f"Initializing experiment for session {self.session_id}")
        logger.info(f"Data will be saved to {self.data_dir}")
        
        # Experiment parameters
        self.n_trials = self.settings.get('n_trials', 20)
        self.set_sizes = self.settings.get('set_sizes', [4, 8, 16, 32])
        self.target_present_prob = self.settings.get('target_present_prob', 0.5)
        self.max_duration = self.settings.get('max_duration', 10)
        self.fixation_duration = self.settings.get('fixation_duration', 1.0)
        self.feedback_duration = self.settings.get('feedback_duration', 0.5)
        self.iti_duration = self.settings.get('iti_duration', 0.5)  # Inter-trial interval
        self.calibration_threshold = self.settings.get('calibration_threshold', 1.0)
        self.adaptive_difficulty = self.settings.get('adaptive_difficulty', True)
        
        # Data storage
        self.results = []
        self.trial_data = []
        self.eye_data = []
        self.error_log = []
        
        # Performance metrics
        self.accuracy = 0
        self.mean_rt = 0
        self.current_performance = {
            'accuracy': [],
            'rt': [],
            'set_size': [],
            'target_present': []
        }
        
        # Stimuli containers
        self.stimuli = {}
        
        # Trial handler for more sophisticated trial sequencing
        self.trials = None
        
        # Flag for experiment state
        self.paused = False
        self.aborted = False

    def setup(self):
        """Set up the experiment hardware, window, and stimuli."""
        logger.info("Setting up experiment")
        
        try:
            # Create monitor with proper settings
            monitor_name = self.settings.get('monitor_name', 'testMonitor')
            monitor = monitors.Monitor(
                monitor_name,
                width=self.settings.get('monitor_width_cm', 50),
                distance=self.settings.get('viewing_distance_cm', 60)
            )
            
            # Create window
            self.win = visual.Window(
                size=(self.settings.get('screen_width', 1920), self.settings.get('screen_height', 1080)),
                fullscr=self.settings.get('fullscreen', True),
                monitor=monitor,
                units='pix',
                color=self.settings.get('background_color', [128, 128, 128]),
                colorSpace='rgb255',
                screen=self.settings.get('screen_number', 0),
                allowGUI=False,
                winType='pyglet'
            )
            
            # Initialize keyboard with accurate timing
            self.kb = keyboard.Keyboard(backend='ptb')
            
            # Initialize eye tracker
            self.tracker = EyeTracker(
                win=self.win,
                session_id=self.session_id,
                save_locally=True,
                send_to_server=self.settings.get('send_to_server', False),
                sampling_rate=self.settings.get('eye_tracking_rate', 60),
                calibration_points=self.settings.get('calibration_points', 9)
            )
            
            # Create all stimuli
            self._create_stimuli()
            
            # Create trial handler
            self._create_trial_sequence()
            
            logger.info("Experiment setup completed successfully")
            return True
            
        except Exception as e:
            logger.error(f"Error during experiment setup: {str(e)}")
            logger.error(traceback.format_exc())
            self.error_log.append({
                'time': time.time(),
                'component': 'setup',
                'error': str(e),
                'traceback': traceback.format_exc()
            })
            return False

    def _create_stimuli(self):
        """Create all stimuli used in the experiment."""
        logger.info("Creating experiment stimuli")
        
        # Fixation cross
        self.stimuli['fixation'] = visual.TextStim(
            win=self.win,
            text='+',
            height=30,
            color=self.settings.get('text_color', [255, 255, 255]),
            colorSpace='rgb255',
            name='fixation'
        )
        
        # Instructions
        self.stimuli['instructions'] = visual.TextStim(
            win=self.win,
            text="In this experiment, you will search for a target among distractors.\n\n"
                 "The target is a 'T' and the distractors are 'L's.\n\n"
                 "Press 'f' if the target is present, 'j' if it is absent.\n\n"
                 "Try to respond as quickly and accurately as possible.\n\n"
                 "Press SPACE to begin. Press 'p' to pause at any time.",
            height=24,
            wrapWidth=self.settings.get('screen_width', 1920) * 0.8,
            color=self.settings.get('text_color', [255, 255, 255]),
            colorSpace='rgb255',
            alignText='center',
            name='instructions'
        )
        
        # Feedback stimuli
        self.stimuli['feedback_correct'] = visual.TextStim(
            win=self.win,
            text="Correct!",
            height=30,
            color=[0, 255, 0],  # Green
            colorSpace='rgb255',
            name='feedback_correct'
        )
        
        self.stimuli['feedback_incorrect'] = visual.TextStim(
            win=self.win,
            text="Incorrect!",
            height=30,
            color=[255, 0, 0],  # Red
            colorSpace='rgb255',
            name='feedback_incorrect'
        )
        
        self.stimuli['feedback_timeout'] = visual.TextStim(
            win=self.win,
            text="Too slow!",
            height=30,
            color=[255, 255, 0],  # Yellow
            colorSpace='rgb255',
            name='feedback_timeout'
        )
        
        # End text
        self.stimuli['end_text'] = visual.TextStim(
            win=self.win,
            text="Thank you for participating!\n\nPress ESCAPE to exit.",
            height=30,
            color=self.settings.get('text_color', [255, 255, 255]),
            colorSpace='rgb255',
            alignText='center',
            name='end_text'
        )
        
        # Pause screen
        self.stimuli['pause_text'] = visual.TextStim(
            win=self.win,
            text="Experiment paused.\n\nPress 'p' to continue or ESCAPE to quit.",
            height=30,
            color=self.settings.get('text_color', [255, 255, 255]),
            colorSpace='rgb255',
            alignText='center',
            name='pause_text'
        )
        
        # Progress bar background
        self.stimuli['progress_bar_bg'] = visual.Rect(
            win=self.win,
            width=self.settings.get('screen_width', 1920) * 0.8,
            height=20,
            fillColor=[50, 50, 50],
            lineColor=[200, 200, 200],
            colorSpace='rgb255',
            pos=(0, -self.settings.get('screen_height', 1080) * 0.4),
            name='progress_bar_bg'
        )
        
        # Progress bar fill
        self.stimuli['progress_bar_fill'] = visual.Rect(
            win=self.win,
            width=0,  # Will be updated during the experiment
            height=20,
            fillColor=[0, 255, 0],
            lineColor=None,
            colorSpace='rgb255',
            pos=(0, -self.settings.get('screen_height', 1080) * 0.4),
            name='progress_bar_fill'
        )
        
        logger.info("Stimuli creation completed")

    def _create_trial_sequence(self):
        """Create the trial sequence using PsychoPy's trial handler."""
        logger.info("Creating trial sequence")
        
        # Create factorial design
        factors = {
            'set_size': self.set_sizes,
            'target_present': [True, False]
        }
        
        # Calculate repetitions to achieve desired number of trials
        factor_combinations = len(self.set_sizes) * 2  # set_sizes × target_present
        repetitions = max(1, self.n_trials // factor_combinations)
        
        # Create trial handler with randomization
        self.trials = data.TrialHandler(
            trialList=data.createFactorialTrialList(factors),
            nReps=repetitions,
            method='random',
            dataTypes=['response', 'rt', 'correct', 'adapted_duration']
        )
        
        logger.info(f"Created trial sequence with {self.trials.nTotal} trials")

    def create_search_display(self, set_size, target_present):
        """
        Create a visual search display.

        Parameters
        ----------
        set_size : int
            Number of items in the display.
        target_present : bool
            Whether the target is present.

        Returns
        -------
        list
            List of stimuli for the search display.
        dict
            Information about the display.
        """
        logger.debug(f"Creating search display: set_size={set_size}, target_present={target_present}")
        
        # Define item properties
        item_size = self.settings.get('item_size', 30)
        min_distance = item_size * 2
        
        # Define grid for item placement
        grid_size = int(np.ceil(np.sqrt(set_size)))
        grid_spacing = min_distance * 1.5
        
        # Calculate grid boundaries
        max_x = self.settings.get('screen_width', 1920) / 2 - item_size * 2
        min_x = -max_x
        max_y = self.settings.get('screen_height', 1080) / 2 - item_size * 2
        min_y = -max_y
        
        # Generate positions
        positions = []
        attempts = 0
        max_attempts = 1000  # Prevent infinite loops
        
        while len(positions) < set_size and attempts < max_attempts:
            x = random.uniform(min_x, max_x)
            y = random.uniform(min_y, max_y)
            
            # Check if position is far enough from existing positions
            if all(np.sqrt((x - pos[0])**2 + (y - pos[1])**2) >= min_distance for pos in positions):
                positions.append((x, y))
            
            attempts += 1
        
        # If we couldn't place all items randomly, use a grid layout
        if len(positions) < set_size:
            logger.warning(f"Could not place all {set_size} items randomly. Using grid layout.")
            positions = []
            x_positions = np.linspace(min_x, max_x, int(np.ceil(np.sqrt(set_size))))
            y_positions = np.linspace(min_y, max_y, int(np.ceil(np.sqrt(set_size))))
            
            for i in range(set_size):
                x_idx = i % len(x_positions)
                y_idx = i // len(x_positions)
                if y_idx < len(y_positions):
                    positions.append((x_positions[x_idx], y_positions[y_idx]))
        
        # Create stimuli
        stimuli = []
        target_index = None
        target_pos = None
        
        if target_present:
            # Add target (T)
            target_index = random.randint(0, set_size - 1)
            target_pos = positions[target_index]
            target = visual.TextStim(
                win=self.win,
                text='T',
                pos=target_pos,
                height=item_size,
                color=self.settings.get('text_color', [255, 255, 255]),
                colorSpace='rgb255',
                ori=random.choice([0, 90, 180, 270]),
                name='target'
            )
            stimuli.append(target)
            
            # Add distractors (L)
            for i in range(set_size - 1):
                idx = i if i < target_index else i + 1
                distractor = visual.TextStim(
                    win=self.win,
                    text='L',
                    pos=positions[idx],
                    height=item_size,
                    color=self.settings.get('text_color', [255, 255, 255]),
                    colorSpace='rgb255',
                    ori=random.choice([0, 90, 180, 270]),
                    name=f'distractor_{i}'
                )
                stimuli.append(distractor)
        else:
            # Add distractors only (L)
            for i in range(set_size):
                distractor = visual.TextStim(
                    win=self.win,
                    text='L',
                    pos=positions[i],
                    height=item_size,
                    color=self.settings.get('text_color', [255, 255, 255]),
                    colorSpace='rgb255',
                    ori=random.choice([0, 90, 180, 270]),
                    name=f'distractor_{i}'
                )
                stimuli.append(distractor)
        
        # Return stimuli and display info
        display_info = {
            'set_size': set_size,
            'target_present': target_present,
            'target_index': target_index,
            'target_position': target_pos,
            'positions': positions,
            'creation_time': self.global_clock.getTime()
        }
        
        logger.debug(f"Created search display with {len(stimuli)} items")
        return stimuli, display_info

    def run_trial(self, trial_idx, trial_info):
        """
        Run a single trial.

        Parameters
        ----------
        trial_idx : int
            Trial index.
        trial_info : dict
            Information about the trial from the trial handler.

        Returns
        -------
        dict
            Trial results.
        """
        set_size = trial_info['set_size']
        target_present = trial_info['target_present']
        
        logger.info(f"Running trial {trial_idx+1}/{self.trials.nTotal}: set_size={set_size}, target_present={target_present}")
        
        # Apply adaptive fixation duration if enabled
        fixation_duration = self.fixation_duration
        if self.adaptive_difficulty and len(self.current_performance['accuracy']) > 0:
            # Calculate error rate for adaptive control
            recent_accuracy = np.mean(self.current_performance['accuracy'][-5:]) if len(self.current_performance['accuracy']) >= 5 else 0.5
            error_rate = 1.0 - recent_accuracy
            
            trial_info_for_adaptation = {
                'trial_number': trial_idx + 1,
                'error': error_rate
            }
            
            fixation_duration, feedback_message = run_adaptive_trial_control(
                self.win, 
                trial_info_for_adaptation, 
                error_threshold=0.3
            )
            logger.info(f"Adaptive control: {feedback_message}")
        
        try:
            # Create search display
            search_display, display_info = self.create_search_display(set_size, target_present)
            
            # Show fixation
            self.stimuli['fixation'].draw()
            self.win.flip()
            core.wait(fixation_duration)
            
            # Start recording eye movements
            self.tracker.start_recording()
            
            # Show search display
            for stim in search_display:
                stim.draw()
            
            # Draw progress bar
            progress = (trial_idx + 1) / self.trials.nTotal
            self.stimuli['progress_bar_bg'].draw()
            self.stimuli['progress_bar_fill'].width = progress * self.settings.get('screen_width', 1920) * 0.8
            self.stimuli['progress_bar_fill'].pos = (
                (progress - 1) * self.settings.get('screen_width', 1920) * 0.4,
                -self.settings.get('screen_height', 1080) * 0.4
            )
            self.stimuli['progress_bar_fill'].draw()
            
            # Flip window and record onset time
            onset_time = self.win.flip()
            
            # Reset keyboard and clock
            self.kb.clearEvents()
            self.clock.reset()
            
            # Wait for response or timeout
            response = None
            rt = None
            timeout = False
            
            # Collect eye tracking data
            eye_data = []
            
            while self.clock.getTime() < self.max_duration:
                # Update eye tracker and collect data
                gaze_data = self.tracker.update()
                if gaze_data:
                    gaze_data['trial_time'] = self.clock.getTime()
                    gaze_data['trial_idx'] = trial_idx
                    eye_data.append(gaze_data)
                
                # Check for keyboard response
                keys = self.kb.getKeys(['f', 'j', 'p', 'escape'])
                if keys:
                    if 'escape' in keys:
                        logger.info("Escape key pressed, aborting experiment")
                        self.aborted = True
                        return None
                    
                    if 'p' in keys:
                        logger.info("Pause key pressed, pausing experiment")
                        self._handle_pause()
                        # Reset clock after pause
                        self.clock.reset()
                        continue
                    
                    # Process response
                    for key in keys:
                        if key.name in ['f', 'j']:
                            response = key.name == 'f'  # True if 'f' (target present), False if 'j' (target absent)
                            rt = key.rt
                            break
                    
                    if response is not None:
                        break
            
            # Check for timeout
            if response is None:
                timeout = True
                logger.info(f"Trial {trial_idx+1} timed out")
            
            # Stop recording eye movements
            self.tracker.stop_recording()
            
            # Determine if response was correct
            correct = response == target_present if response is not None else False
            
            # Update performance metrics
            if not timeout:
                self.current_performance['accuracy'].append(int(correct))
                self.current_performance['rt'].append(rt)
                self.current_performance['set_size'].append(set_size)
                self.current_performance['target_present'].append(target_present)
            
            # Show feedback
            if timeout:
                self.stimuli['feedback_timeout'].draw()
            elif correct:
                self.stimuli['feedback_correct'].draw()
            else:
                self.stimuli['feedback_incorrect'].draw()
            
            feedback_onset = self.win.flip()
            core.wait(self.feedback_duration)
            
            # Inter-trial interval
            self.win.flip()
            core.wait(self.iti_duration)
            
            # Prepare trial results
            trial_results = {
                'trial_idx': trial_idx,
                'set_size': set_size,
                'target_present': target_present,
                'response': response,
                'correct': correct,
                'rt': rt,
                'timeout': timeout,
                'display_info': display_info,
                'onset_time': onset_time,
                'feedback_onset': feedback_onset,
                'fixation_duration': fixation_duration,
                'eye_data': eye_data
            }
            
            # Add to trial handler for automatic data saving
            self.trials.addData('response', 1 if response else 0 if response is not None else None)
            self.trials.addData('rt', rt)
            self.trials.addData('correct', int(correct))
            self.trials.addData('adapted_duration', fixation_duration)
            
            logger.info(f"Trial {trial_idx+1} completed: correct={correct}, rt={rt:.3f}s")
            return trial_results
            
        except Exception as e:
            logger.error(f"Error during trial {trial_idx+1}: {str(e)}")
            logger.error(traceback.format_exc())
            self.error_log.append({
                'time': time.time(),
                'component': 'trial',
                'trial_idx': trial_idx,
                'error': str(e),
                'traceback': traceback.format_exc()
            })
            
            # Try to recover and continue with next trial
            if self.tracker:
                try:
                    self.tracker.stop_recording()
                except:
                    pass
            
            return {
                'trial_idx': trial_idx,
                'set_size': set_size,
                'target_present': target_present,
                'error': str(e),
                'recovered': True
            }

    def _handle_pause(self):
        """Handle experiment pause."""
        self.paused = True
        
        # Stop eye tracking during pause
        if self.tracker:
            self.tracker.stop_recording()
        
        # Show pause screen
        self.stimuli['pause_text'].draw()
        self.win.flip()
        
        # Wait for unpause or quit
        while self.paused:
            keys = event.getKeys(['p', 'escape'])
            if 'escape' in keys:
                logger.info("Escape key pressed during pause, aborting experiment")
                self.aborted = True
                self.paused = False
            elif 'p' in keys:
                logger.info("Resuming experiment from pause")
                self.paused = False
            
            core.wait(0.1)
        
        # Countdown before resuming
        countdown = visual.TextStim(
            win=self.win,
            text="Resuming in 3...",
            height=30,
            color=self.settings.get('text_color', [255, 255, 255]),
            colorSpace='rgb255'
        )
        
        for i in range(3, 0, -1):
            countdown.text = f"Resuming in {i}..."
            countdown.draw()
            self.win.flip()
            core.wait(1.0)

    def run(self):
        """Run the experiment."""
        logger.info("Starting experiment")
        self.global_clock.reset()
        
        try:
            # Set up experiment
            if not self.setup():
                logger.error("Experiment setup failed")
                return False
            
            # Calibrate eye tracker
            calibration_log_path = self.data_dir / "calibration_log.txt"
            calibration_threshold = self.calibration_threshold
            
            # Initial calibration
            self.tracker.calibrate()
            
            # Check calibration quality and adapt if needed
            if check_calibration_and_adapt(self.win, calibration_log_path, calibration_threshold):
                logger.info("Recalibration recommended, running calibration again")
                self.tracker.calibrate()
            
            # Show instructions
            self.stimuli['instructions'].draw()
            self.win.flip()
            event.waitKeys(keyList=['space'])
            
            # Run trials
            for trial_idx, trial_info in enumerate(self.trials):
                # Check for abort
                if self.aborted:
                    break
                
                # Run trial
                trial_results = self.run_trial(trial_idx, trial_info)
                if trial_results is None:
                    break
                
                self.results.append(trial_results)
                
                # Save data incrementally
                if trial_idx % 5 == 0:
                    self.save_results(final=False)
                
                # Check if we need to recalibrate
                if trial_idx > 0 and trial_idx % 20 == 0:
                    logger.info("Periodic calibration check")
                    if check_calibration_and_adapt(self.win, calibration_log_path, calibration_threshold):
                        logger.info("Recalibration recommended")
                        self.tracker.calibrate()
            
            # Calculate final performance metrics
            if self.current_performance['accuracy']:
                self.accuracy = np.mean(self.current_performance['accuracy'])
                self.mean_rt = np.mean(self.current_performance['rt']) if self.current_performance['rt'] else 0
                
                logger.info(f"Experiment completed. Overall accuracy: {self.accuracy:.2f}, Mean RT: {self.mean_rt:.3f}s")
            
            # Show end screen
            self.stimuli['end_text'].draw()
            self.win.flip()
            event.waitKeys(keyList=['escape'])
            
            # Save final results
            self.save_results(final=True)
            
            # Generate and save visualizations
            self.generate_visualizations()
            
            # Clean up
            self.quit()
            return True
            
        except Exception as e:
            logger.error(f"Error during experiment: {str(e)}")
            logger.error(traceback.format_exc())
            self.error_log.append({
                'time': time.time(),
                'component': 'run',
                'error': str(e),
                'traceback': traceback.format_exc()
            })
            
            # Try to save any collected data
            self.save_results(final=True)
            
            # Clean up
            self.quit()
            return False

    def save_results(self, final=True):
        """
        Save experiment results.
        
        Parameters
        ----------
        final : bool
            Whether this is the final save (True) or an incremental save (False).
        """
        if not self.results:
            logger.warning("No results to save")
            return
        
        try:
            # Save to JSON file
            results_file = self.data_dir / "experiment_results.json"
            with open(results_file, 'w') as f:
                # Remove eye_data from JSON to keep file size manageable
                results_for_json = []
                for trial in self.results:
                    trial_copy = trial.copy()
                    if 'eye_data' in trial_copy:
                        # Just store summary of eye data in JSON
                        trial_copy['eye_data_count'] = len(trial_copy['eye_data'])
                        del trial_copy['eye_data']
                    results_for_json.append(trial_copy)
                
                json.dump(results_for_json, f, indent=2)
            
            # Save eye tracking data separately in CSV format
            eye_data_file = self.data_dir / "eye_tracking_data.csv"
            with open(eye_data_file, 'w', newline='') as f:
                if self.results and any('eye_data' in trial for trial in self.results):
                    # Get all possible fields from eye data
                    all_fields = set()
                    for trial in self.results:
                        if 'eye_data' in trial:
                            for sample in trial['eye_data']:
                                all_fields.update(sample.keys())
                    
                    # Create CSV writer with all fields
                    fieldnames = sorted(list(all_fields))
                    writer = csv.DictWriter(f, fieldnames=fieldnames)
                    writer.writeheader()
                    
                    # Write all eye tracking samples
                    for trial in self.results:
                        if 'eye_data' in trial:
                            for sample in trial['eye_data']:
                                writer.writerow(sample)
            
            # Save trial data in CSV format for easy analysis
            trial_data_file = self.data_dir / "trial_data.csv"
            with open(trial_data_file, 'w', newline='') as f:
                if self.results:
                    # Get all possible fields from trial data
                    all_fields = set()
                    for trial in self.results:
                        all_fields.update(k for k, v in trial.items() if k != 'eye_data' and k != 'display_info')
                    
                    # Create CSV writer with all fields
                    fieldnames = sorted(list(all_fields))
                    writer = csv.DictWriter(f, fieldnames=fieldnames)
                    writer.writeheader()
                    
                    # Write all trial data
                    for trial in self.results:
                        row = {k: v for k, v in trial.items() if k in fieldnames}
                        writer.writerow(row)
            
            logger.info(f"Saved results to {self.data_dir}")
            
        except Exception as e:
            logger.error(f"Error saving results: {str(e)}")
            logger.error(traceback.format_exc())
        finally:
            if final:
                # Save error log if there were any errors
                if self.error_log:
                    error_log_file = self.data_dir / "error_log.json"
                    try:
                        with open(error_log_file, 'w') as f:
                            json.dump(self.error_log, f, indent=2)
                        logger.info(f"Saved error log to {error_log_file}")
                    except Exception as e:
                        logger.error(f"Error saving error log: {str(e)}")

    def quit(self):
        """Quit the experiment and clean up."""
        if self.tracker:
            self.tracker.close()
        
        if self.win:
            self.win.close()
        
        core.quit()


if __name__ == "__main__":
    # Show dialog for experiment settings
    exp_info = {
        'participant': '',
        'session': '001',
        'fullscreen': True
    }
    
    dlg = gui.DlgFromDict(
        dictionary=exp_info,
        title='Visual Search Experiment',
        fixed=['session']
    )
    
    if dlg.OK:
        # Create experiment
        experiment = VisualSearchExperiment(settings={
            'fullscreen': exp_info['fullscreen']
        })
        
        # Run experiment
        experiment.run()
    else:
        core.quit() 