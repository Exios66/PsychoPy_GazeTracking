#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Test script to verify scipy imports.
"""

import unittest
from pathlib import Path

class TestImports(unittest.TestCase):
    """Test cases for verifying imports."""
    
    def test_scipy_import(self):
        """Test scipy.spatial.distance import."""
        try:
            from scipy.spatial.distance import euclidean
            # Test the function
            distance = euclidean([0, 0], [3, 4])
            self.assertEqual(distance, 5.0)
            print("Successfully imported scipy.spatial.distance.euclidean")
        except ImportError as e:
            self.fail(f"Import error: {e}")

if __name__ == "__main__":
    unittest.main() 