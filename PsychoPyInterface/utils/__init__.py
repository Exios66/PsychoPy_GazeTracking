#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Utility modules for the PsychoPy interface.

This package contains utility modules for eye tracking, data analysis,
and WebGazer integration.
"""

from .eye_tracker import EyeTracker
from .analysis import (
    load_gaze_data,
    detect_fixations,
    detect_saccades,
    create_heatmap,
    plot_gaze_data,
    analyze_session
)
from .webgazer_bridge import WebGazerBridge

__all__ = [
    'EyeTracker',
    'WebGazerBridge',
    'load_gaze_data',
    'detect_fixations',
    'detect_saccades',
    'create_heatmap',
    'plot_gaze_data',
    'analyze_session'
] 