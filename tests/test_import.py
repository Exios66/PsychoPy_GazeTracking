#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Test script to verify scipy imports.
"""

try:
    from scipy.spatial.distance import euclidean
    print("Successfully imported scipy.spatial.distance.euclidean")
    
    # Test the function
    distance = euclidean([0, 0], [3, 4])
    print(f"Distance between [0, 0] and [3, 4] is {distance}")
    
except ImportError as e:
    print(f"Import error: {e}") 