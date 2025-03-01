#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Eye Tracker Utility Module

This module provides a robust, production-ready interface for different eye tracking methods in PsychoPy,
including native PsychoPy eye tracking, WebGazer.js integration, and external eye trackers.
It handles error recovery, data validation, and comprehensive logging.
"""

import os
import json
import time
import numpy as np
import logging
from pathlib import Path
from datetime import datetime
from psychopy import core, visual, event, iohub
from threading import Lock


# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('EyeTracker')


class EyeTracker:
    """
    A production-ready unified interface for eye tracking in PsychoPy experiments.
    
    This class provides methods for initializing, calibrating, and collecting data
    from various eye tracking sources, including:
    - PsychoPy's built-in iohub interface
    - WebGazer.js (via WebGazerBridge)
    - External eye trackers (Tobii, EyeLink, etc.)
    
    Features include:
    - Robust error handling and recovery
    - Data validation and filtering
    - Comprehensive logging
    - Thread-safe data collection
    - Automatic backup and recovery
    - Performance optimization
    
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
    validation_level : str
        Level of data validation ('none', 'basic', 'strict')
    auto_save_interval : float
        Interval in seconds for automatic data saving (0 to disable)
    """
    
    SUPPORTED_TRACKERS = ['psychopy', 'webgazer', 'tobii', 'eyelink', 'mouse']
    
    def __init__(self, window, tracker_type='psychopy', calibration_points=9, 
                 data_dir=None, validation_level='basic', auto_save_interval=60.0):
        self.window = window
        self.tracker_type = tracker_type.lower()
        self.calibration_points = calibration_points
        self.validation_level = validation_level
        self.auto_save_interval = auto_save_interval
        
        if self.tracker_type not in self.SUPPORTED_TRACKERS:
            logger.error(f"Unsupported tracker type: {self.tracker_type}")
            raise ValueError(f"Unsupported tracker type: {self.tracker_type}. "
                            f"Supported types are: {', '.join(self.SUPPORTED_TRACKERS)}")
        
        # Set up data directory
        if data_dir is None:
            data_dir = Path(__file__).parent.parent / 'data'
        self.data_dir = Path(data_dir)
        if not self.data_dir.exists():
            os.makedirs(self.data_dir)
            logger.info(f"Created data directory: {self.data_dir}")
            
        # Initialize data storage with thread safety
        self.gaze_data = []
        self.data_lock = Lock()
        self.is_recording = False
        self.tracker = None
        self.last_auto_save = time.time()
        self.session_id = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        # Data validation parameters
        self.min_pupil_size = 1.0  # mm
        self.max_pupil_size = 9.0  # mm
        self.max_velocity = 1000.0  # deg/s
        self.last_valid_gaze = (0, 0)
        self.last_timestamp = 0
        
        # Performance metrics
        self.sample_count = 0
        self.dropped_samples = 0
        self.start_time = None
        
        # Initialize tracker based on type
        try:
            self._initialize_tracker()
            logger.info(f"Successfully initialized {self.tracker_type} eye tracker")
        except Exception as e:
            logger.error(f"Failed to initialize {self.tracker_type} eye tracker: {e}", exc_info=True)
            self._fallback_to_mouse()
        
    def _fallback_to_mouse(self):
        """Fall back to mouse simulation if eye tracker initialization fails."""
        logger.warning("Falling back to mouse simulation for eye tracking")
        self.tracker_type = 'mouse'
        try:
            self.io = iohub.launchHubServer()
            self.tracker = self.io.devices.mouse
        except Exception as e:
            logger.error(f"Failed to initialize mouse fallback: {e}", exc_info=True)
            raise RuntimeError("Could not initialize eye tracker or mouse fallback")
        
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
        elif self.tracker_type == 'mouse':
            self._initialize_mouse()
        else:
            raise ValueError(f"Unsupported tracker type: {self.tracker_type}")
    
    def _initialize_mouse(self):
        """Initialize mouse simulation for eye tracking."""
        logger.info("Initializing mouse simulation for eye tracking")
        self.io = iohub.launchHubServer()
        self.tracker = self.io.devices.mouse
    
    def _initialize_psychopy_tracker(self):
        """Initialize PsychoPy's built-in eye tracker via iohub."""
        try:
            # Initialize iohub with eye tracker configuration
            iohub_config = {
                'eyetracker.hw.sr_research.eyelink.EyeTracker': {
                    'name': 'tracker',
                    'model_name': 'EYELINK 1000 DESKTOP',
                    'runtime_settings': {
                        'sampling_rate': 1000,
                        'track_eyes': 'BINOCULAR'
                    }
                }
            }
            
            self.io = iohub.launchHubServer(**iohub_config)
            
            # Get the eye tracker device
            self.tracker = self.io.devices.eyetracker
            
            if self.tracker is None:
                logger.warning("No eye tracker detected via iohub. Using mouse simulation.")
                self._fallback_to_mouse()
        except Exception as e:
            logger.error(f"Error initializing PsychoPy eye tracker: {e}", exc_info=True)
            self._fallback_to_mouse()
    
    def _initialize_webgazer(self):
        """Initialize WebGazer.js bridge."""
        try:
            from PsychoPyInterface.utils.webgazer_bridge import WebGazerBridge
            self.tracker = WebGazerBridge(port=8887)
            self.tracker.start()
            logger.info("WebGazer bridge initialized. Waiting for client connection...")
            
            # Set up connection timeout
            connection_timeout = 30  # seconds
            start_time = time.time()
            
            while not self.tracker.is_connected():
                if time.time() - start_time > connection_timeout:
                    raise TimeoutError("WebGazer client connection timed out")
                time.sleep(0.5)
                
            logger.info("WebGazer client connected successfully")
        except Exception as e:
            logger.error(f"Error initializing WebGazer bridge: {e}", exc_info=True)
            self._fallback_to_mouse()
    
    def _initialize_tobii(self):
        """Initialize Tobii eye tracker with robust error handling."""
        try:
            import tobii_research as tr
            
            # Find Tobii eye trackers
            eyetrackers = tr.find_all_eyetrackers()
            
            if len(eyetrackers) == 0:
                raise Exception("No Tobii eye trackers found")
                
            # Use the first eye tracker
            self.tracker = eyetrackers[0]
            logger.info(f"Connected to Tobii eye tracker: {self.tracker.model} "
                      f"(S/N: {self.tracker.serial_number})")
            
            # Set up gaze data callback with thread safety
            self._tobii_gaze_data = []
            self.tracker.subscribe_to(
                tr.EYETRACKER_GAZE_DATA,
                self._tobii_gaze_callback,
                as_dictionary=True
            )
            
            # Test connection
            test_data_received = False
            start_time = time.time()
            timeout = 5.0  # seconds
            
            def test_callback(gaze_data):
                nonlocal test_data_received
                test_data_received = True
                
            self.tracker.subscribe_to(
                tr.EYETRACKER_GAZE_DATA,
                test_callback,
                as_dictionary=True
            )
            
            while not test_data_received and time.time() - start_time < timeout:
                time.sleep(0.1)
                
            self.tracker.unsubscribe_from(tr.EYETRACKER_GAZE_DATA, test_callback)
            
            if not test_data_received:
                raise Exception("No data received from Tobii eye tracker")
                
        except Exception as e:
            logger.error(f"Error initializing Tobii eye tracker: {e}", exc_info=True)
            self._fallback_to_mouse()
    
    def _tobii_gaze_callback(self, gaze_data):
        """Callback function for Tobii gaze data with validation and filtering."""
        if not self.is_recording:
            return
            
        with self.data_lock:
            self._tobii_gaze_data.append(gaze_data)
            
            # Convert to normalized coordinates and add to gaze_data
            left_eye = gaze_data['left_gaze_point_on_display_area']
            right_eye = gaze_data['right_gaze_point_on_display_area']
            
            # Average the two eyes if both are valid
            if left_eye[0] > 0 and right_eye[0] > 0:
                x = (left_eye[0] + right_eye[0]) / 2
                y = (left_eye[1] + right_eye[1]) / 2
                confidence = 1.0
            elif left_eye[0] > 0:
                x, y = left_eye
                confidence = 0.5
            elif right_eye[0] > 0:
                x, y = right_eye
                confidence = 0.5
            else:
                self.dropped_samples += 1
                return  # No valid gaze data
                
            # Convert from normalized coordinates to window coordinates
            win_size = self.window.size
            screen_x = x * win_size[0] - win_size[0]/2
            screen_y = (1-y) * win_size[1] - win_size[1]/2
            
            timestamp = gaze_data['device_time_stamp']
            
            # Validate data if strict validation is enabled
            if self.validation_level == 'strict':
                # Check for physiologically impossible values
                left_pupil = gaze_data['left_pupil_diameter']
                right_pupil = gaze_data['right_pupil_diameter']
                
                if (left_pupil is not None and 
                    (left_pupil < self.min_pupil_size or left_pupil > self.max_pupil_size)):
                    self.dropped_samples += 1
                    return
                    
                if (right_pupil is not None and 
                    (right_pupil < self.min_pupil_size or right_pupil > self.max_pupil_size)):
                    self.dropped_samples += 1
                    return
                    
                # Check for impossibly fast movements
                if self.last_timestamp > 0:
                    dt = timestamp - self.last_timestamp
                    if dt > 0:
                        dx = screen_x - self.last_valid_gaze[0]
                        dy = screen_y - self.last_valid_gaze[1]
                        distance = np.sqrt(dx**2 + dy**2)
                        velocity = distance / dt
                        
                        if velocity > self.max_velocity:
                            self.dropped_samples += 1
                            return
            
            # Update tracking variables
            self.last_valid_gaze = (screen_x, screen_y)
            self.last_timestamp = timestamp
            self.sample_count += 1
            
            # Add validated data
            self.gaze_data.append({
                'timestamp': timestamp,
                'x': screen_x,
                'y': screen_y,
                'pupil_left': gaze_data['left_pupil_diameter'],
                'pupil_right': gaze_data['right_pupil_diameter'],
                'confidence': confidence
            })
            
            # Auto-save if interval has elapsed
            if (self.auto_save_interval > 0 and 
                time.time() - self.last_auto_save > self.auto_save_interval):
                self._auto_save_data()
    
    def _auto_save_data(self):
        """Automatically save data at regular intervals."""
        if len(self.gaze_data) > 0:
            try:
                backup_file = f"gaze_data_{self.session_id}_backup_{int(time.time())}.json"
                self.save_data(backup_file)
                self.last_auto_save = time.time()
                logger.info(f"Auto-saved eye tracking data to {backup_file}")
            except Exception as e:
                logger.error(f"Failed to auto-save eye tracking data: {e}", exc_info=True)
    
    def _initialize_eyelink(self):
        """Initialize SR Research EyeLink eye tracker with comprehensive setup."""
        try:
            import pylink
            
            # Initialize connection to the tracker
            self.tracker = pylink.EyeLink()
            
            # Check if the tracker is connected
            if not self.tracker.isConnected():
                raise RuntimeError("EyeLink not connected")
                
            logger.info(f"Connected to EyeLink eye tracker")
            
            # Configure tracker settings
            self.tracker.sendCommand("sample_rate 1000")
            self.tracker.sendCommand("calibration_type = HV9")
            self.tracker.sendCommand("file_event_filter = LEFT,RIGHT,FIXATION,SACCADE,BLINK,MESSAGE,BUTTON,INPUT")
            self.tracker.sendCommand("file_sample_data = LEFT,RIGHT,GAZE,AREA,GAZERES,STATUS,HTARGET,INPUT")
            self.tracker.sendCommand("recording_parse_type = GAZE")
            self.tracker.sendCommand("pupil_size_diameter = YES")
            
            # Set up EDF file for recording
            edf_file = f"PSYPY_{self.session_id}"[:8]  # EyeLink limits to 8 chars
            self.tracker.openDataFile(edf_file + '.edf')
            self.tracker.sendMessage("EXPERIMENT_ID " + self.session_id)
            
            # Set up link data
            self.tracker.setLinkEventFilter("FIXATION,SACCADE,BLINK,BUTTON,INPUT")
            self.tracker.setLinkSampleFilter("LEFT,RIGHT,GAZE,GAZERES,AREA,STATUS")
            
            # Test receiving data
            self.tracker.startRecording(1, 1, 1, 1)
            time.sleep(0.1)
            self.tracker.stopRecording()
            
        except Exception as e:
            logger.error(f"Error initializing EyeLink eye tracker: {e}", exc_info=True)
            self._fallback_to_mouse()
    
    def calibrate(self):
        """
        Calibrate the eye tracker with validation and retry options.
        
        Returns
        -------
        bool
            True if calibration was successful, False otherwise
        """
        max_attempts = 3
        for attempt in range(1, max_attempts + 1):
            logger.info(f"Starting calibration attempt {attempt}/{max_attempts}")
            
            try:
                if self.tracker_type == 'psychopy':
                    result = self._calibrate_psychopy()
                elif self.tracker_type == 'webgazer':
                    result = self._calibrate_webgazer()
                elif self.tracker_type == 'tobii':
                    result = self._calibrate_tobii()
                elif self.tracker_type == 'eyelink':
                    result = self._calibrate_eyelink()
                elif self.tracker_type == 'mouse':
                    # No calibration needed for mouse simulation
                    return True
                else:
                    return False
                
                if result:
                    logger.info(f"Calibration successful on attempt {attempt}")
                    return True
                else:
                    logger.warning(f"Calibration failed on attempt {attempt}")
                    
                    # Show retry message
                    if attempt < max_attempts:
                        retry_msg = visual.TextStim(
                            self.window,
                            text=f"Calibration failed. Attempt {attempt}/{max_attempts}\n\n"
                                 f"Press SPACE to retry or ESC to skip calibration.",
                            height=0.05
                        )
                        
                        retry_msg.draw()
                        self.window.flip()
                        
                        keys = event.waitKeys(keyList=['space', 'escape'])
                        if 'escape' in keys:
                            logger.info("User chose to skip calibration")
                            return False
            except Exception as e:
                logger.error(f"Error during calibration attempt {attempt}: {e}", exc_info=True)
                
                # Show error message
                error_msg = visual.TextStim(
                    self.window,
                    text=f"Calibration error: {str(e)}\n\n"
                         f"Press SPACE to retry or ESC to skip calibration.",
                    height=0.05
                )
                
                error_msg.draw()
                self.window.flip()
                
                keys = event.waitKeys(keyList=['space', 'escape'])
                if 'escape' in keys:
                    logger.info("User chose to skip calibration after error")
                    return False
        
        logger.warning(f"Calibration failed after {max_attempts} attempts")
        return False
    
    def _calibrate_psychopy(self):
        """Calibrate PsychoPy's eye tracker."""
        if hasattr(self.tracker, 'runSetupProcedure'):
            try:
                result = self.tracker.runSetupProcedure()
                return result
            except Exception as e:
                logger.error(f"Error during PsychoPy calibration: {e}", exc_info=True)
                return False
        else:
            # For mouse simulation, no calibration needed
            return True
    
    def _calibrate_webgazer(self):
        """Calibrate WebGazer.js with interactive feedback."""
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
            start_time = time.time()
            connection_timeout = 60  # seconds
            
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
                
                # Check for timeout
                if time.time() - start_time > connection_timeout:
                    text.text = "Connection timeout. Please check WebGazer client.\n\n" \
                               "Press SPACE to retry or ESC to cancel."
                    text.draw()
                    self.window.flip()
                    
                    keys = event.waitKeys(keyList=['space', 'escape'])
                    if 'escape' in keys:
                        return False
                    else:
                        start_time = time.time()
                
                core.wait(0.1)
            
            # Wait for user to confirm calibration is complete
            text.text = "WebGazer client connected!\n\n" \
                        "Complete the calibration in the browser, then press SPACE to continue."
            
            # Add validation step
            validation_passed = False
            while not validation_passed:
                text.draw()
                self.window.flip()
                
                keys = event.getKeys(keyList=['space', 'escape'])
                if 'space' in keys:
                    # Validate calibration
                    validation_passed = self._validate_webgazer_calibration()
                    if not validation_passed:
                        text.text = "Calibration validation failed. Please recalibrate in the browser.\n\n" \
                                   "Press SPACE when done or ESC to skip."
                elif 'escape' in keys:
                    return False
                
                core.wait(0.1)
                
            return True
        return False
    
    def _validate_webgazer_calibration(self):
        """Validate WebGazer calibration by testing gaze accuracy."""
        # Create validation points
        validation_points = [
            (0, 0),      # Center
            (-0.8, 0.8), # Top-left
            (0.8, 0.8),  # Top-right
            (-0.8, -0.8),# Bottom-left
            (0.8, -0.8)  # Bottom-right
        ]
        
        target = visual.GratingStim(
            self.window, tex=None, mask='circle', 
            size=0.05, color='green'
        )
        
        instructions = visual.TextStim(
            self.window,
            text="Look at each green dot to validate calibration",
            pos=(0, 0.9),
            height=0.04
        )
        
        errors = []
        
        for point in validation_points:
            # Show point
            target.pos = point
            
            for frame in range(90):  # 1.5 seconds at 60 Hz
                target.draw()
                instructions.draw()
                self.window.flip()
                
                # Collect gaze data for the last 0.5 seconds
                if frame >= 60:  # Last 0.5 seconds
                    gaze = self.get_gaze_position()
                    if gaze != (0, 0):
                        error = np.sqrt((gaze[0] - point[0])**2 + (gaze[1] - point[1])**2)
                        errors.append(error)
            
            core.wait(0.5)  # Brief pause between points
        
        # Calculate average error
        if errors:
            avg_error = sum(errors) / len(errors)
            logger.info(f"WebGazer validation average error: {avg_error:.4f}")
            
            # Convert to visual degrees (approximate)
            # Assuming a typical monitor setup
            screen_width_cm = 50  # Approximate
            viewing_distance_cm = 60  # Approximate
            window_width_px = self.window.size[0]
            
            # Convert normalized coordinates to cm
            error_cm = avg_error * screen_width_cm / 2
            
            # Convert to visual degrees
            error_degrees = np.degrees(np.arctan(error_cm / viewing_distance_cm))
            
            logger.info(f"WebGazer validation error: {error_degrees:.2f} degrees visual angle")
            
            # Typical threshold for acceptable calibration is 1-2 degrees
            return error_degrees < 2.0
        
        return False
    
    def _calibrate_tobii(self):
        """Calibrate Tobii eye tracker with interactive feedback and validation."""
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
        try:
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
                # Validate calibration
                validation_result = self._validate_tobii_calibration(points)
                
                if validation_result:
                    instructions.text = "Calibration successful!\n\n" \
                                       f"Average error: {validation_result:.2f} degrees\n\n" \
                                       "Press SPACE to continue."
                    success = True
                else:
                    instructions.text = "Calibration validation failed.\n\n" \
                                       "Press SPACE to retry or ESC to continue anyway."
                    success = False
            else:
                instructions.text = "Calibration failed. Please try again.\n\n" \
                                   "Press SPACE to retry or ESC to continue anyway."
                success = False
                
            instructions.draw()
            self.window.flip()
            keys = event.waitKeys(keyList=['space', 'escape'])
            
            if 'escape' in keys and not success:
                # User chose to continue with poor calibration
                logger.warning("User continued with failed calibration")
                return True
                
            return success
            
        except Exception as e:
            logger.error(f"Error during Tobii calibration: {e}", exc_info=True)
            return False
    
    def _validate_tobii_calibration(self, points):
        """Validate Tobii calibration by measuring gaze accuracy at calibration points."""
        target = visual.GratingStim(
            self.window, tex=None, mask='circle', 
            size=0.05, color='blue'
        )
        
        instructions = visual.TextStim(
            self.window,
            text="Validating calibration...\nPlease look at each blue dot",
            pos=(0, 0.9),
            height=0.04
        )
        
        errors = []
        
        # Start recording for validation
        self.start_recording()
        
        for point in points:
            # Show point
            target.pos = point
            
            for frame in range(90):  # 1.5 seconds at 60 Hz
                target.draw()
                instructions.draw()
                self.window.flip()
                
                # Collect gaze data for the last 0.5 seconds
                if frame >= 60:  # Last 0.5 seconds
                    self.update()
            
            # Calculate average error for this point
            point_errors = []
            with self.data_lock:
                # Calculate error for this point using gaze data
                if self.gaze_data:
                    # Process gaze data for this point
                    point_errors.append(self.calculate_gaze_error(point))
            
            # Short pause between points
            core.wait(0.5)
        
        # Stop recording after validation
        self.stop_recording()
        
        # Calculate average error across all points
        if point_errors:
            avg_error = sum(point_errors) / len(point_errors)
            errors.append(avg_error)
            
        return errors
        
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