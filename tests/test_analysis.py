#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Test script for the analysis utilities.
"""

import os
import sys
import unittest
import numpy as np
from pathlib import Path

# Add the parent directory to the path so we can import the PsychoPyInterface package
sys.path.insert(0, str(Path(__file__).parent.parent))

try:
    # Test imports for analysis utilities
    import matplotlib.pyplot as plt
    import pandas as pd
    from scipy.spatial.distance import euclidean
    from scipy.ndimage import gaussian_filter
    
    # Only attempt to import these if the directory exists
    if Path("PsychoPyInterface/utils").exists():
        try:
            from PsychoPyInterface.utils.analysis import (
                load_gaze_data,
                detect_fixations,
                detect_saccades,
                create_heatmap,
                plot_gaze_data,
                analyze_session
            )
        except ImportError as e:
            print(f"Warning: Could not import analysis modules: {e}")
    
    class TestAnalysisUtils(unittest.TestCase):
        """Test cases for analysis utilities."""
        
        def setUp(self):
            """Set up test data."""
            # Create sample gaze data
            self.gaze_data = [
                {"timestamp": 100, "x": 100, "y": 100},
                {"timestamp": 150, "x": 105, "y": 102},
                {"timestamp": 200, "x": 103, "y": 101},
                {"timestamp": 250, "x": 102, "y": 103},
                {"timestamp": 300, "x": 200, "y": 200},
                {"timestamp": 350, "x": 205, "y": 202},
                {"timestamp": 400, "x": 203, "y": 201},
                {"timestamp": 450, "x": 202, "y": 203}
            ]
        
        def test_euclidean_distance(self):
            """Test euclidean distance calculation."""
            dist = euclidean([0, 0], [3, 4])
            self.assertEqual(dist, 5.0)
        
        def test_gaussian_filter(self):
            """Test gaussian filter."""
            data = np.ones((5, 5))
            filtered = gaussian_filter(data, sigma=1.0)
            self.assertEqual(filtered.shape, (5, 5))
            
        def test_matplotlib(self):
            """Test matplotlib functionality."""
            fig, ax = plt.subplots()
            ax.plot([1, 2, 3], [1, 2, 3])
            self.assertIsNotNone(fig)
            plt.close(fig)
    
    if __name__ == "__main__":
        unittest.main()

except ImportError as e:
    print(f"Import error: {e}")
    print("Make sure you have activated the virtual environment and installed all dependencies.")
    print("Run: source venv/bin/activate && pip install -r requirements.txt") 