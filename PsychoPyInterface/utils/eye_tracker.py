#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Eye Tracker Utility Module

This module provides a unified interface for different eye tracking methods in PsychoPy,
including native PsychoPy eye tracking, WebGazer.js integration, and external eye trackers.
"""

import os
import json
import time
import numpy as np
from pathlib import Path
from datetime import datetime
from psychopy import core, visual, event, iohub


class EyeTracker:
    """
    A unified interface for eye tracking in PsychoPy experiments.
    
    This class provides methods for initializing, calibrating, and collecting data
    from various eye tracking sources, including:
    - PsychoPy's built-in iohub interface
    - WebGazer.js (via WebGazerBridge)
    - External eye trackers (Tobii, EyeLink, etc.)
    
    Parameters
    ----------
    window : psychopy.visual.Window
        The PsychoPy window object
    tracker_type : str
        The type of eye tracker to use ('psychopy', 'webgazer', 'tobii', 'eyelink')
    calibration_points : int
        Number of calibration points (default: 9)
    data_dir : str or Path
        Directory to save eye tracking data
    """
    
    def __init__(self, window, tracker_type='psychopy', calibration_points=9, 
                 data_dir=None):
        self.window = window
        self.tracker_type = tracker_type.lower()
        self.calibration_points = calibration_points
        
        # Set up data directory
        if data_dir is None:
            data_dir = Path(__file__).parent.parent / 'data'
        self.data_dir = Path(data_dir)
        if not self.data_dir.exists():
            os.makedirs(self.data_dir)
            
        # Initialize data storage
        self.gaze_data = []
        self.is_recording = False
        self.tracker = None
        
        # Initialize tracker based on type
        self._initialize_tracker()
        
    def _initialize_tracker(self):
        """Initialize the appropriate eye tracker based on tracker_type."""
        if self.tracker_type == 'psychopy':
            self._initialize_psychopy_tracker()
        elif self.tracker_type == 'webgazer':
            self._initialize_webgazer()
        elif self.tracker_type == 'tobii':
            self._initialize_tobii()
        elif self.tracker_type == 'eyelink':
            self._initialize_eyelink()
        else:
            raise ValueError(f"Unsupported tracker type: {self.tracker_type}")
    
    def _initialize_psychopy_tracker(self):
        """Initialize PsychoPy's built-in eye tracker via iohub."""
        try:
            # Initialize iohub
            self.io = iohub.launchHubServer()
            
            # Get the eye tracker device
            self.tracker = self.io.devices.eyetracker
            
            if self.tracker is None:
                print("Warning: No eye tracker detected. Using mouse simulation.")
                # Use mouse simulation if no eye tracker is available
                self.tracker_type = 'mouse'
                self.tracker = self.io.devices.mouse
        except Exception as e:
            print(f"Error initializing PsychoPy eye tracker: {e}")
            print("Falling back to mouse simulation.")
            # Fall back to mouse simulation
            self.tracker_type = 'mouse'
            self.io = iohub.launchHubServer()
            self.tracker = self.io.devices.mouse
    
    def _initialize_webgazer(self):
        """Initialize WebGazer.js bridge."""
        try:
            from PsychoPyInterface.utils.webgazer_bridge import WebGazerBridge
            self.tracker = WebGazerBridge(port=8887)
            self.tracker.start()
            print("WebGazer bridge initialized. Waiting for client connection...")
        except Exception as e:
            print(f"Error initializing WebGazer bridge: {e}")
            print("Falling back to mouse simulation.")
            self.tracker_type = 'mouse'
            self.io = iohub.launchHubServer()
            self.tracker = self.io.devices.mouse
    
    def _initialize_tobii(self):
        """Initialize Tobii eye tracker."""
        try:
            import tobii_research as tr
            
            # Find Tobii eye trackers
            eyetrackers = tr.find_all_eyetrackers()
            
            if len(eyetrackers) == 0:
                raise Exception("No Tobii eye trackers found")
                
            # Use the first eye tracker
            self.tracker = eyetrackers[0]
            print(f"Connected to Tobii eye tracker: {self.tracker.model} "
                  f"(S/N: {self.tracker.serial_number})")
            
            # Set up gaze data callback
            self._tobii_gaze_data = []
            self.tracker.subscribe_to(
                tr.EYETRACKER_GAZE_DATA,
                self._tobii_gaze_callback,
                as_dictionary=True
            )
        except Exception as e:
            print(f"Error initializing Tobii eye tracker: {e}")
            print("Falling back to mouse simulation.")
            self.tracker_type = 'mouse'
            self.io = iohub.launchHubServer()
            self.tracker = self.io.devices.mouse
    
    def _tobii_gaze_callback(self, gaze_data):
        """Callback function for Tobii gaze data."""
        if self.is_recording:
            self._tobii_gaze_data.append(gaze_data)
            
            # Convert to normalized coordinates and add to gaze_data
            left_eye = gaze_data['left_gaze_point_on_display_area']
            right_eye = gaze_data['right_gaze_point_on_display_area']
            
            # Average the two eyes if both are valid
            if left_eye[0] > 0 and right_eye[0] > 0:
                x = (left_eye[0] + right_eye[0]) / 2
                y = (left_eye[1] + right_eye[1]) / 2
            elif left_eye[0] > 0:
                x, y = left_eye
            elif right_eye[0] > 0:
                x, y = right_eye
            else:
                return  # No valid gaze data
                
            # Convert from normalized coordinates to window coordinates
            win_size = self.window.size
            screen_x = x * win_size[0] - win_size[0]/2
            screen_y = (1-y) * win_size[1] - win_size[1]/2
            
            timestamp = gaze_data['device_time_stamp']
            self.gaze_data.append({
                'timestamp': timestamp,
                'x': screen_x,
                'y': screen_y,
                'pupil_left': gaze_data['left_pupil_diameter'],
                'pupil_right': gaze_data['right_pupil_diameter']
            })
    
    def _initialize_eyelink(self):
        """Initialize SR Research EyeLink eye tracker."""
        try:
            import pylink
            
            # Initialize connection to the tracker
            self.tracker = pylink.EyeLink()
            
            # Check if the tracker is connected
            if not self.tracker.isConnected():
                raise RuntimeError("EyeLink not connected")
                
            print(f"Connected to EyeLink eye tracker")
            
            # Configure tracker settings
            self.tracker.sendCommand("sample_rate 1000")
            self.tracker.sendCommand("calibration_type = HV9")
            self.tracker.sendCommand("file_event_filter = LEFT,RIGHT,FIXATION,SACCADE,BLINK,MESSAGE,BUTTON,INPUT")
            self.tracker.sendCommand("file_sample_data = LEFT,RIGHT,GAZE,AREA,GAZERES,STATUS,HTARGET,INPUT")
            
        except Exception as e:
            print(f"Error initializing EyeLink eye tracker: {e}")
            print("Falling back to mouse simulation.")
            self.tracker_type = 'mouse'
            self.io = iohub.launchHubServer()
            self.tracker = self.io.devices.mouse
    
    def calibrate(self):
        """
        Calibrate the eye tracker.
        
        Returns
        -------
        bool
            True if calibration was successful, False otherwise
        """
        if self.tracker_type == 'psychopy':
            return self._calibrate_psychopy()
        elif self.tracker_type == 'webgazer':
            return self._calibrate_webgazer()
        elif self.tracker_type == 'tobii':
            return self._calibrate_tobii()
        elif self.tracker_type == 'eyelink':
            return self._calibrate_eyelink()
        elif self.tracker_type == 'mouse':
            # No calibration needed for mouse simulation
            return True
        else:
            return False
    
    def _calibrate_psychopy(self):
        """Calibrate PsychoPy's eye tracker."""
        if hasattr(self.tracker, 'runSetupProcedure'):
            result = self.tracker.runSetupProcedure()
            return result
        else:
            # For mouse simulation, no calibration needed
            return True
    
    def _calibrate_webgazer(self):
        """Calibrate WebGazer.js."""
        # WebGazer calibration is handled on the client side
        # Just wait for the client to connect and calibrate
        if hasattr(self.tracker, 'wait_for_connection'):
            text = visual.TextStim(
                self.window, 
                text="Please open the WebGazer client and follow the calibration instructions.\n\n"
                     "Press SPACE when calibration is complete.",
                height=0.05
            )
            
            # Wait for client connection
            connected = False
            while not connected:
                text.draw()
                self.window.flip()
                
                # Check for connection
                if hasattr(self.tracker, 'is_connected') and self.tracker.is_connected():
                    connected = True
                
                # Check for key press to skip waiting
                keys = event.getKeys(keyList=['space', 'escape'])
                if 'space' in keys:
                    break
                elif 'escape' in keys:
                    return False
                
                core.wait(0.1)
            
            # Wait for user to confirm calibration is complete
            text.text = "WebGazer client connected!\n\n" \
                        "Complete the calibration in the browser, then press SPACE to continue."
            while True:
                text.draw()
                self.window.flip()
                
                keys = event.getKeys(keyList=['space', 'escape'])
                if 'space' in keys:
                    break
                elif 'escape' in keys:
                    return False
                
                core.wait(0.1)
                
            return True
        return False
    
    def _calibrate_tobii(self):
        """Calibrate Tobii eye tracker."""
        # Simple calibration procedure for Tobii
        if self.tracker_type != 'tobii':
            return False
            
        # Create calibration points
        points = []
        for i in range(self.calibration_points):
            if self.calibration_points == 9:
                # 3x3 grid
                row = i // 3
                col = i % 3
                x = -0.8 + col * 0.8
                y = 0.8 - row * 0.8
            elif self.calibration_points == 5:
                # 5-point calibration
                if i == 0:
                    x, y = 0, 0  # Center
                elif i == 1:
                    x, y = -0.8, 0.8  # Top-left
                elif i == 2:
                    x, y = 0.8, 0.8  # Top-right
                elif i == 3:
                    x, y = -0.8, -0.8  # Bottom-left
                else:
                    x, y = 0.8, -0.8  # Bottom-right
            else:
                # Default to corners and center
                if i == 0:
                    x, y = 0, 0  # Center
                elif i == 1:
                    x, y = -0.8, 0.8  # Top-left
                elif i == 2:
                    x, y = 0.8, 0.8  # Top-right
                elif i == 3:
                    x, y = -0.8, -0.8  # Bottom-left
                else:
                    x, y = 0.8, -0.8  # Bottom-right
                    
            points.append((x, y))
        
        # Create visual stimuli
        target = visual.GratingStim(
            self.window, tex=None, mask='circle', 
            size=0.05, color='red'
        )
        
        inner_target = visual.GratingStim(
            self.window, tex=None, mask='circle', 
            size=0.01, color='white'
        )
        
        instructions = visual.TextStim(
            self.window, 
            text="Follow the red dot with your eyes.\n\n"
                 "Press SPACE to start calibration.",
            height=0.05
        )
        
        # Show instructions
        instructions.draw()
        self.window.flip()
        event.waitKeys(keyList=['space', 'escape'])
        
        # Run calibration
        import tobii_research as tr
        calibration = tr.ScreenBasedCalibration(self.tracker)
        
        # Enter calibration mode
        calibration.enter_calibration_mode()
        
        for i, point in enumerate(points):
            # Convert from normalized coordinates (-1 to 1) to screen coordinates (0 to 1)
            screen_x = (point[0] + 1) / 2
            screen_y = 1 - (point[1] + 1) / 2
            
            # Show point
            target.pos = point
            inner_target.pos = point
            
            # Animate point appearance
            for frame in range(30):  # 0.5 seconds at 60 Hz
                target.size = 0.05 - 0.03 * (frame / 30)
                target.draw()
                inner_target.draw()
                self.window.flip()
                
            # Collect data
            calibration.collect_data(screen_x, screen_y)
            
            # Short pause between points
            core.wait(0.5)
        
        # Apply and exit calibration
        calibration_result = calibration.compute_and_apply()
        calibration.leave_calibration_mode()
        
        # Show result
        if calibration_result.status == tr.CALIBRATION_STATUS_SUCCESS:
            instructions.text = "Calibration successful!\n\n" \
                               "Press SPACE to continue."
            success = True
        else:
            instructions.text = "Calibration failed. Please try again.\n\n" \
                               "Press SPACE to continue."
            success = False
            
        instructions.draw()
        self.window.flip()
        event.waitKeys(keyList=['space'])
        
        return success
    
    def _calibrate_eyelink(self):
        """Calibrate EyeLink eye tracker."""
        if self.tracker_type != 'eyelink':
            return False
            
        # Use EyeLink's built-in calibration routine
        self.tracker.doTrackerSetup()
        return True
    
    def start_recording(self):
        """Start recording eye tracking data."""
        self.gaze_data = []
        self.is_recording = True
        
        if self.tracker_type == 'psychopy':
            if hasattr(self.tracker, 'setRecordingState'):
                self.tracker.setRecordingState(True)
        elif self.tracker_type == 'eyelink':
            self.tracker.startRecording(1, 1, 1, 1)
        
        # For WebGazer and Tobii, recording is handled by callbacks
        
        return True
    
    def stop_recording(self):
        """Stop recording eye tracking data."""
        self.is_recording = False
        
        if self.tracker_type == 'psychopy':
            if hasattr(self.tracker, 'setRecordingState'):
                self.tracker.setRecordingState(False)
        elif self.tracker_type == 'eyelink':
            self.tracker.stopRecording()
        
        return True
    
    def get_gaze_position(self):
        """
        Get the current gaze position.
        
        Returns
        -------
        tuple
            (x, y) coordinates of gaze position in window coordinates
        """
        if not self.is_recording:
            self.update()
            
        if len(self.gaze_data) > 0:
            latest = self.gaze_data[-1]
            return (latest['x'], latest['y'])
        else:
            return (0, 0)
    
    def update(self):
        """Update gaze data from the eye tracker."""
        if self.tracker_type == 'psychopy':
            self._update_psychopy()
        elif self.tracker_type == 'webgazer':
            self._update_webgazer()
        elif self.tracker_type == 'mouse':
            self._update_mouse()
        # Tobii and EyeLink updates are handled by callbacks
    
    def _update_psychopy(self):
        """Update gaze data from PsychoPy's eye tracker."""
        if hasattr(self.tracker, 'getPosition'):
            # For iohub eye tracker
            sample = self.tracker.getLastGazePosition()
            if sample is not None:
                x, y = sample
                timestamp = core.getTime()
                self.gaze_data.append({
                    'timestamp': timestamp,
                    'x': x,
                    'y': y,
                    'pupil_left': None,
                    'pupil_right': None
                })
    
    def _update_webgazer(self):
        """Update gaze data from WebGazer.js."""
        if hasattr(self.tracker, 'get_latest_gaze_data'):
            data = self.tracker.get_latest_gaze_data()
            if data is not None:
                # Convert from normalized coordinates (0-1) to window coordinates
                win_size = self.window.size
                x = data['x'] * win_size[0] - win_size[0]/2
                y = (1-data['y']) * win_size[1] - win_size[1]/2
                
                timestamp = data.get('timestamp', core.getTime())
                self.gaze_data.append({
                    'timestamp': timestamp,
                    'x': x,
                    'y': y,
                    'pupil_left': None,
                    'pupil_right': None
                })
    
    def _update_mouse(self):
        """Update gaze data using mouse position (simulation)."""
        pos = self.tracker.getPos()
        timestamp = core.getTime()
        self.gaze_data.append({
            'timestamp': timestamp,
            'x': pos[0],
            'y': pos[1],
            'pupil_left': None,
            'pupil_right': None
        })
    
    def save_data(self, filename=None):
        """
        Save recorded gaze data to a file.
        
        Parameters
        ----------
        filename : str, optional
            Name of the file to save data to. If None, a default name is generated.
            
        Returns
        -------
        str
            Path to the saved file
        """
        if filename is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"gaze_data_{timestamp}.json"
        
        filepath = self.data_dir / filename
        
        # Ensure data directory exists
        if not self.data_dir.exists():
            os.makedirs(self.data_dir)
        
        # Save data
        with open(filepath, 'w') as f:
            json.dump({
                'tracker_type': self.tracker_type,
                'timestamp': datetime.now().isoformat(),
                'window_size': self.window.size,
                'gaze_data': self.gaze_data
            }, f, indent=2)
        
        print(f"Gaze data saved to {filepath}")
        return str(filepath)
    
    def close(self):
        """Close the eye tracker and clean up resources."""
        self.stop_recording()
        
        if self.tracker_type == 'webgazer':
            if hasattr(self.tracker, 'stop'):
                self.tracker.stop()
        elif self.tracker_type == 'tobii':
            import tobii_research as tr
            if hasattr(self.tracker, 'unsubscribe_from'):
                self.tracker.unsubscribe_from(tr.EYETRACKER_GAZE_DATA)
        elif self.tracker_type == 'eyelink':
            if hasattr(self.tracker, 'close'):
                self.tracker.close()
        
        # Close iohub connection if it exists
        if hasattr(self, 'io'):
            self.io.quit() 