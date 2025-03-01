#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Visual Search Experiment

This experiment presents a visual search task where participants
search for a target among distractors while their eye movements
are tracked.
"""

import os
import json
import random
import numpy as np
from pathlib import Path
from datetime import datetime

from psychopy import visual, core, event, data, gui
from psychopy.hardware import keyboard

from ..utils import EyeTracker
from ..config import DEFAULT_EXPERIMENT_SETTINGS, DATA_DIR


class VisualSearchExperiment:
    """Visual search experiment with eye tracking."""

    def __init__(self, settings=None):
        """
        Initialize the experiment.

        Parameters
        ----------
        settings : dict, optional
            Experiment settings. If None, default settings will be used.
        """
        # Merge settings with defaults
        self.settings = DEFAULT_EXPERIMENT_SETTINGS.copy()
        if settings:
            self.settings.update(settings)
        
        # Initialize experiment components
        self.win = None
        self.tracker = None
        self.kb = None
        self.clock = core.Clock()
        self.session_id = datetime.now().strftime("%Y%m%d_%H%M%S")
        self.data_dir = DATA_DIR / self.session_id
        os.makedirs(self.data_dir, exist_ok=True)
        
        # Experiment parameters
        self.n_trials = 20
        self.set_sizes = [4, 8, 16, 32]  # Number of items in the search display
        self.target_present_prob = 0.5  # Probability of target being present
        self.max_duration = 10  # Maximum trial duration in seconds
        self.results = []

    def setup(self):
        """Set up the experiment."""
        # Create window
        self.win = visual.Window(
            size=(self.settings['screen_width'], self.settings['screen_height']),
            fullscr=self.settings['fullscreen'],
            monitor='testMonitor',
            units='pix',
            color=self.settings['background_color'],
            colorSpace='rgb255'
        )
        
        # Initialize keyboard
        self.kb = keyboard.Keyboard()
        
        # Initialize eye tracker
        self.tracker = EyeTracker(
            win=self.win,
            session_id=self.session_id,
            save_locally=True,
            send_to_server=True
        )
        
        # Create stimuli
        self.fixation = visual.TextStim(
            win=self.win,
            text='+',
            height=30,
            color=self.settings['text_color'],
            colorSpace='rgb255'
        )
        
        self.instructions = visual.TextStim(
            win=self.win,
            text="In this experiment, you will search for a target among distractors.\n\n"
                 "The target is a 'T' and the distractors are 'L's.\n\n"
                 "Press 'f' if the target is present, 'j' if it is absent.\n\n"
                 "Press SPACE to begin.",
            height=24,
            wrapWidth=self.settings['screen_width'] * 0.8,
            color=self.settings['text_color'],
            colorSpace='rgb255'
        )
        
        self.feedback_correct = visual.TextStim(
            win=self.win,
            text="Correct!",
            height=30,
            color=[0, 255, 0],  # Green
            colorSpace='rgb255'
        )
        
        self.feedback_incorrect = visual.TextStim(
            win=self.win,
            text="Incorrect!",
            height=30,
            color=[255, 0, 0],  # Red
            colorSpace='rgb255'
        )
        
        self.end_text = visual.TextStim(
            win=self.win,
            text="Thank you for participating!\n\nPress ESCAPE to exit.",
            height=30,
            color=self.settings['text_color'],
            colorSpace='rgb255'
        )

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
        # Define item properties
        item_size = 30
        min_distance = item_size * 2
        
        # Define grid for item placement
        grid_size = int(np.ceil(np.sqrt(set_size)))
        grid_spacing = min_distance * 1.5
        
        # Calculate grid boundaries
        max_x = self.settings['screen_width'] / 2 - item_size
        min_x = -max_x
        max_y = self.settings['screen_height'] / 2 - item_size
        min_y = -max_y
        
        # Generate positions
        positions = []
        for i in range(set_size):
            while True:
                x = random.uniform(min_x, max_x)
                y = random.uniform(min_y, max_y)
                
                # Check if position is far enough from existing positions
                if all(np.sqrt((x - pos[0])**2 + (y - pos[1])**2) >= min_distance for pos in positions):
                    positions.append((x, y))
                    break
        
        # Create stimuli
        stimuli = []
        target_index = None
        
        if target_present:
            # Add target (T)
            target_index = random.randint(0, set_size - 1)
            target_pos = positions[target_index]
            target = visual.TextStim(
                win=self.win,
                text='T',
                pos=target_pos,
                height=item_size,
                color=self.settings['text_color'],
                colorSpace='rgb255',
                ori=random.choice([0, 90, 180, 270])
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
                    color=self.settings['text_color'],
                    colorSpace='rgb255',
                    ori=random.choice([0, 90, 180, 270])
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
                    color=self.settings['text_color'],
                    colorSpace='rgb255',
                    ori=random.choice([0, 90, 180, 270])
                )
                stimuli.append(distractor)
        
        # Return stimuli and display info
        display_info = {
            'set_size': set_size,
            'target_present': target_present,
            'target_index': target_index,
            'positions': positions
        }
        
        return stimuli, display_info

    def run_trial(self, trial_idx, set_size):
        """
        Run a single trial.

        Parameters
        ----------
        trial_idx : int
            Trial index.
        set_size : int
            Number of items in the display.

        Returns
        -------
        dict
            Trial results.
        """
        # Determine if target is present
        target_present = random.random() < self.target_present_prob
        
        # Create search display
        search_display, display_info = self.create_search_display(set_size, target_present)
        
        # Show fixation
        self.fixation.draw()
        self.win.flip()
        core.wait(1.0)
        
        # Start recording eye movements
        self.tracker.start_recording()
        
        # Show search display
        for stim in search_display:
            stim.draw()
        self.win.flip()
        
        # Reset keyboard and clock
        self.kb.clearEvents()
        self.clock.reset()
        
        # Wait for response or timeout
        response = None
        rt = None
        
        while self.clock.getTime() < self.max_duration:
            # Update eye tracker
            self.tracker.update()
            
            # Check for keyboard response
            keys = self.kb.getKeys(['f', 'j', 'escape'])
            if keys:
                if 'escape' in keys:
                    self.quit()
                    return None
                
                response = 'f' in keys  # True if 'f' (target present), False if 'j' (target absent)
                rt = self.clock.getTime()
                break
            
            # Check for quit
            if event.getKeys(['escape']):
                self.quit()
                return None
        
        # Stop recording eye movements
        self.tracker.stop_recording()
        
        # Determine if response was correct
        correct = response == target_present if response is not None else False
        
        # Show feedback
        if response is not None:
            if correct:
                self.feedback_correct.draw()
            else:
                self.feedback_incorrect.draw()
            self.win.flip()
            core.wait(0.5)
        
        # Prepare trial results
        trial_results = {
            'trial_idx': trial_idx,
            'set_size': set_size,
            'target_present': target_present,
            'response': response,
            'correct': correct,
            'rt': rt,
            'display_info': display_info
        }
        
        return trial_results

    def run(self):
        """Run the experiment."""
        # Set up experiment
        self.setup()
        
        # Calibrate eye tracker
        self.tracker.calibrate()
        
        # Show instructions
        self.instructions.draw()
        self.win.flip()
        event.waitKeys(keyList=['space'])
        
        # Create trial sequence
        trial_sequence = []
        for i in range(self.n_trials):
            set_size = random.choice(self.set_sizes)
            trial_sequence.append((i, set_size))
        
        # Run trials
        for trial_idx, set_size in trial_sequence:
            trial_results = self.run_trial(trial_idx, set_size)
            if trial_results is None:
                break
            self.results.append(trial_results)
        
        # Show end screen
        self.end_text.draw()
        self.win.flip()
        event.waitKeys(keyList=['escape'])
        
        # Save results
        self.save_results()
        
        # Clean up
        self.quit()

    def save_results(self):
        """Save experiment results."""
        if not self.results:
            return
        
        # Save to JSON file
        results_file = self.data_dir / "experiment_results.json"
        with open(results_file, 'w') as f:
            json.dump(self.results, f, indent=2)
        
        print(f"Saved experiment results to {results_file}")

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