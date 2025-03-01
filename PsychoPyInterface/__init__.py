#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
PsychoPy Interface for Gaze Tracking

This package provides tools and utilities for creating and running eye-tracking
experiments using PsychoPy, with support for various eye tracking methods including
WebGazer.js integration for web-based eye tracking.

The package includes:
- Sample experiments demonstrating eye tracking functionality
- Utility modules for eye tracking and data analysis
- A launcher for running experiments through a graphical interface
"""

import os
from pathlib import Path

# Create necessary directories if they don't exist
PACKAGE_DIR = Path(__file__).parent.absolute()
DATA_DIR = PACKAGE_DIR / "data"
RESOURCES_DIR = PACKAGE_DIR / "resources"

for directory in [DATA_DIR, RESOURCES_DIR]:
    if not directory.exists():
        os.makedirs(directory)

# Import main components
from PsychoPyInterface.experiments import VisualSearchExperiment, WebGazerDemo
from PsychoPyInterface.utils import WebGazerBridge

__version__ = "0.1.0"
__author__ = "PsychoPy Gaze Tracking Team"

__all__ = [
    "VisualSearchExperiment",
    "WebGazerDemo",
    "WebGazerBridge",
    "PACKAGE_DIR",
    "DATA_DIR",
    "RESOURCES_DIR",
] 