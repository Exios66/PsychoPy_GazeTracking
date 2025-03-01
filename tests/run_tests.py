#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Test runner script for PsychoPy Gaze Tracking.
"""

import unittest
import sys
from pathlib import Path

# Add the parent directory to the path
sys.path.insert(0, str(Path(__file__).parent.parent))

def run_all_tests():
    """Run all tests in the tests directory."""
    # Discover and run all tests
    test_loader = unittest.TestLoader()
    test_suite = test_loader.discover(start_dir=str(Path(__file__).parent), pattern="test_*.py")
    
    # Run the tests
    test_runner = unittest.TextTestRunner(verbosity=2)
    result = test_runner.run(test_suite)
    
    # Return appropriate exit code
    return 0 if result.wasSuccessful() else 1

if __name__ == "__main__":
    sys.exit(run_all_tests()) 