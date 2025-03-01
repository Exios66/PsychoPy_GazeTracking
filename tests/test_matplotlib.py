#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Test script to verify matplotlib and pandas imports.
"""

try:
    import matplotlib.pyplot as plt
    import pandas as pd
    import numpy as np
    from scipy.spatial.distance import euclidean
    
    print("Successfully imported all required packages:")
    print("- matplotlib.pyplot")
    print("- pandas")
    print("- numpy")
    print("- scipy.spatial.distance")
    
    # Create a simple plot to test matplotlib
    x = np.linspace(0, 10, 100)
    y = np.sin(x)
    
    plt.figure(figsize=(8, 4))
    plt.plot(x, y)
    plt.title("Test Plot")
    plt.savefig("test_plot.png")
    print("Successfully created a test plot: test_plot.png")
    
except ImportError as e:
    print(f"Import error: {e}") 