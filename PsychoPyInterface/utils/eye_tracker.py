#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Eye tracking utility module for PsychoPy.

This module provides functions for eye tracking using PsychoPy's iohub interface
and integrates with the web-based analytics dashboard.
"""

import os
import json
import time
import numpy as np
from pathlib import Path
from datetime import datetime
import requests
from psychopy import core, visual, event
from psychopy.iohub import launchHubServer

from ..config import API_ENDPOINT, EYE_TRACKER_SETTINGS, DATA_DIR


class EyeTracker:
    """Eye tracker interface for PsychoPy experiments."""

    def __init__(self, win, session_id=None, save_locally=True, send_to_server=True):
        """
        Initialize the eye tracker.

        Parameters
        ----------
        win : psychopy.visual.Window
            The PsychoPy window object.
        session_id : str, optional
            The session ID for data storage. If None, a timestamp will be used.
        save_locally : bool, optional
            Whether to save data locally. Default is True.
        send_to_server : bool, optional
            Whether to send data to the server. Default is True.
        """
        self.win = win
        self.session_id = session_id or datetime.now().strftime("%Y%m%d_%H%M%S")
        self.save_locally = save_locally
        self.send_to_server = send_to_server
        self.is_recording = False
        self.gaze_data = []
        self.calibrated = False
        self.io = None
        self.tracker = None
        self._setup_tracker()

    def _setup_tracker(self):
        """Set up the eye tracker using iohub."""
        try:
            # Configure and launch iohub
            iohub_config = {
                'eyetracker.hw.mouse.EyeTracker': {
                    'name': 'tracker',
                    'runtime_settings': {
                        'sampling_rate': 60,
                        'track_eyes': 'BINOCULAR'
                    }
                }
            }
            
            self.io = launchHubServer(**iohub_config)
            self.tracker = self.io.devices.tracker
            
            print("Eye tracker initialized successfully using mouse simulation.")
            print("Note: For real eye tracking, replace the configuration with your specific eye tracker.")
            
        except Exception as e:
            print(f"Warning: Could not initialize eye tracker: {e}")
            print("Falling back to mouse simulation for gaze position.")
            self.tracker = None

    def calibrate(self, points=9, randomize=True, target_duration=1.0):
        """
        Calibrate the eye tracker.

        Parameters
        ----------
        points : int, optional
            Number of calibration points. Default is 9.
        randomize : bool, optional
            Whether to randomize the order of calibration points. Default is True.
        target_duration : float, optional
            Duration to show each calibration point in seconds. Default is 1.0.

        Returns
        -------
        bool
            True if calibration was successful, False otherwise.
        """
        if self.tracker is None:
            print("Using mouse simulation - no calibration needed.")
            self.calibrated = True
            return True

        # Create calibration points grid
        if points == 9:
            grid = [(-0.8, -0.8), (0, -0.8), (0.8, -0.8),
                    (-0.8, 0), (0, 0), (0.8, 0),
                    (-0.8, 0.8), (0, 0.8), (0.8, 0.8)]
        elif points == 5:
            grid = [(-0.8, -0.8), (0.8, -0.8), (0, 0),
                    (-0.8, 0.8), (0.8, 0.8)]
        else:
            # Generate a grid based on the number of points
            n_per_side = int(np.sqrt(points))
            x = np.linspace(-0.8, 0.8, n_per_side)
            y = np.linspace(-0.8, 0.8, n_per_side)
            grid = [(x_pos, y_pos) for y_pos in y for x_pos in x]
            grid = grid[:points]  # Ensure we only use the requested number of points

        if randomize:
            np.random.shuffle(grid)

        # Create visual stimuli for calibration
        target = visual.GratingStim(
            win=self.win, 
            tex=None, 
            mask='circle', 
            size=0.05, 
            color='white'
        )
        
        # Instructions
        instructions = visual.TextStim(
            win=self.win,
            text="Please follow the white dot with your eyes.\n\nPress SPACE to begin calibration.",
            pos=(0, 0),
            color='white'
        )
        instructions.draw()
        self.win.flip()
        event.waitKeys(keyList=['space'])

        # Run calibration
        try:
            self.tracker.runCalibration(
                target_positions=grid,
                randomize_positions=randomize,
                target_duration=target_duration
            )
            calibration_ok = self.tracker.isCalibrated()
            
            if calibration_ok:
                success_text = visual.TextStim(
                    win=self.win,
                    text="Calibration successful!\n\nPress SPACE to continue.",
                    pos=(0, 0),
                    color='green'
                )
                success_text.draw()
                self.win.flip()
                event.waitKeys(keyList=['space'])
            else:
                failure_text = visual.TextStim(
                    win=self.win,
                    text="Calibration failed.\n\nPress SPACE to try again or ESC to continue anyway.",
                    pos=(0, 0),
                    color='red'
                )
                failure_text.draw()
                self.win.flip()
                keys = event.waitKeys(keyList=['space', 'escape'])
                if 'space' in keys:
                    return self.calibrate(points, randomize, target_duration)
            
            self.calibrated = calibration_ok
            return calibration_ok
            
        except Exception as e:
            print(f"Calibration error: {e}")
            error_text = visual.TextStim(
                win=self.win,
                text=f"Calibration error: {e}\n\nPress SPACE to continue with mouse simulation.",
                pos=(0, 0),
                color='red'
            )
            error_text.draw()
            self.win.flip()
            event.waitKeys(keyList=['space'])
            self.calibrated = False
            return False

    def start_recording(self):
        """Start recording eye tracking data."""
        if self.is_recording:
            return
            
        if self.tracker:
            self.tracker.setRecordingState(True)
        
        self.is_recording = True
        self.gaze_data = []
        print(f"Started recording eye tracking data for session {self.session_id}")

    def stop_recording(self):
        """Stop recording eye tracking data."""
        if not self.is_recording:
            return
            
        if self.tracker:
            self.tracker.setRecordingState(False)
        
        self.is_recording = False
        print(f"Stopped recording eye tracking data for session {self.session_id}")
        
        # Save data
        if self.save_locally and self.gaze_data:
            self._save_data_locally()

    def get_gaze_position(self):
        """
        Get the current gaze position.

        Returns
        -------
        tuple
            (x, y) coordinates of gaze position in window coordinates (-1 to 1).
            Returns (None, None) if gaze position cannot be determined.
        """
        if self.tracker:
            # Get gaze data from the eye tracker
            gaze_data = self.tracker.getPosition()
            if gaze_data is not None:
                x, y = gaze_data
                # Convert to normalized coordinates (-1 to 1)
                x = (x / self.win.size[0]) * 2 - 1
                y = (y / self.win.size[1]) * 2 - 1
                return (x, y)
        else:
            # Fallback to mouse position
            mouse_pos = event.getMousePos()
            if mouse_pos:
                x, y = mouse_pos
                # Convert to normalized coordinates (-1 to 1)
                x = (x / self.win.size[0]) * 2 - 1
                y = (y / self.win.size[1]) * 2 - 1
                return (x, y)
                
        return (None, None)

    def update(self):
        """
        Update eye tracking data.
        
        This method should be called on each frame to collect gaze data.
        """
        if not self.is_recording:
            return
            
        timestamp = core.getTime()
        gaze_pos = self.get_gaze_position()
        
        if gaze_pos[0] is not None and gaze_pos[1] is not None:
            # Convert from normalized coordinates (-1 to 1) to pixel coordinates
            x_px = int((gaze_pos[0] + 1) / 2 * self.win.size[0])
            y_px = int((gaze_pos[1] + 1) / 2 * self.win.size[1])
            
            data_point = {
                'timestamp': timestamp,
                'x': x_px,
                'y': y_px,
                'session_id': self.session_id,
                'screen_width': self.win.size[0],
                'screen_height': self.win.size[1]
            }
            
            self.gaze_data.append(data_point)
            
            # Send to server if enabled
            if self.send_to_server:
                self._send_data_to_server(data_point)

    def _save_data_locally(self):
        """Save recorded data to a local file."""
        if not self.gaze_data:
            return
            
        # Create session directory
        session_dir = DATA_DIR / self.session_id
        os.makedirs(session_dir, exist_ok=True)
        
        # Save data to JSON file
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = session_dir / f"gaze_data_{timestamp}.json"
        
        with open(filename, 'w') as f:
            json.dump(self.gaze_data, f, indent=2)
            
        print(f"Saved {len(self.gaze_data)} gaze data points to {filename}")

    def _send_data_to_server(self, data_point):
        """
        Send gaze data to the server.
        
        Parameters
        ----------
        data_point : dict
            The gaze data point to send.
        """
        try:
            response = requests.post(
                API_ENDPOINT,
                json=data_point,
                timeout=0.1  # Short timeout to avoid blocking
            )
            if response.status_code != 200:
                print(f"Warning: Failed to send gaze data to server. Status code: {response.status_code}")
        except requests.exceptions.RequestException:
            # Silently fail to avoid disrupting the experiment
            pass

    def close(self):
        """Close the eye tracker and clean up resources."""
        if self.is_recording:
            self.stop_recording()
            
        if self.io:
            self.io.quit()
            
        print("Eye tracker closed.") 