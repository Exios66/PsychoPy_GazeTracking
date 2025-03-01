#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Simple script to run the PsychoPy interface.
This is a convenience script that imports and runs the launcher.
"""

import sys
from pathlib import Path

# Add the project root to the Python path
project_root = Path(__file__).resolve().parent
sys.path.insert(0, str(project_root))

try:
    from PsychoPyInterface.launcher import main
    
    if __name__ == "__main__":
        main()
except ImportError as e:
    print(f"Error importing PsychoPyInterface: {e}")
    print("Make sure you have installed the package with 'pip install -e .'")
    sys.exit(1) 