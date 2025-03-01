#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Test script to verify matplotlib and pandas imports.
"""

import unittest
import os
from pathlib import Path

class TestMatplotlib(unittest.TestCase):
    """Test cases for verifying matplotlib and pandas imports."""
    
    def test_imports(self):
        """Test importing all required packages."""
        try:
            import matplotlib.pyplot as plt
            import pandas as pd
            import numpy as np
            from scipy.spatial.distance import euclidean
            
            self.assertTrue(True, "All imports successful")
            print("Successfully imported all required packages:")
            print("- matplotlib.pyplot")
            print("- pandas")
            print("- numpy")
            print("- scipy.spatial.distance")
        except ImportError as e:
            self.fail(f"Import error: {e}")
    
    def test_plot_creation(self):
        """Test creating a matplotlib plot."""
        try:
            import matplotlib.pyplot as plt
            import numpy as np
            
            # Create a simple plot to test matplotlib
            x = np.linspace(0, 10, 100)
            y = np.sin(x)
            
            fig = plt.figure(figsize=(8, 4))
            plt.plot(x, y)
            plt.title("Test Plot")
            
            # Save to tests directory
            output_path = Path(__file__).parent / "test_plot.png"
            plt.savefig(output_path)
            plt.close(fig)
            
            self.assertTrue(output_path.exists(), "Plot file was created")
            print(f"Successfully created a test plot: {output_path}")
            
            # Clean up
            if output_path.exists():
                os.remove(output_path)
        except Exception as e:
            self.fail(f"Error creating plot: {e}")

if __name__ == "__main__":
    unittest.main() 