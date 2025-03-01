#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Configuration settings for the PsychoPy interface.

This module contains configuration settings for the PsychoPy interface,
including paths, server settings, and experiment parameters.
"""

import os
import json
from pathlib import Path

# Base paths
ROOT_DIR = Path(__file__).parent.absolute()
DATA_DIR = ROOT_DIR / "data"
EXPERIMENT_DIR = ROOT_DIR / "experiments"
RESOURCES_DIR = ROOT_DIR / "resources"

# Ensure directories exist
os.makedirs(DATA_DIR, exist_ok=True)
os.makedirs(EXPERIMENT_DIR, exist_ok=True)
os.makedirs(RESOURCES_DIR, exist_ok=True)

# Server settings
SERVER_URL = "http://localhost:5000"
API_ENDPOINT = f"{SERVER_URL}/api/gaze"

# Default experiment settings
DEFAULT_EXPERIMENT_SETTINGS = {
    "screen_width": 1920,
    "screen_height": 1080,
    "monitor_distance": 60,  # cm
    "monitor_width": 50,     # cm
    "sampling_rate": 60,     # Hz
    "fullscreen": True,
    "background_color": [0, 0, 0],  # RGB values
    "text_color": [255, 255, 255],  # RGB values
    "calibration_points": 9,
    "validation_points": 5,
    "max_calibration_attempts": 3,
}

# Load custom settings if available
SETTINGS_FILE = ROOT_DIR / "settings.json"
if SETTINGS_FILE.exists():
    try:
        with open(SETTINGS_FILE, 'r') as f:
            custom_settings = json.load(f)
            DEFAULT_EXPERIMENT_SETTINGS.update(custom_settings)
    except (json.JSONDecodeError, IOError) as e:
        print(f"Warning: Could not load settings file: {e}")

# Eye tracker settings
EYE_TRACKER_SETTINGS = {
    "calibration_duration": 0.5,  # seconds
    "validation_threshold": 1.5,  # degrees of visual angle
    "gaze_contingent_trigger": 0.5,  # seconds
    "saccade_velocity_threshold": 40,  # degrees per second
    "fixation_duration_threshold": 0.1,  # seconds
    "blink_detection_threshold": 0.1,  # seconds
} 