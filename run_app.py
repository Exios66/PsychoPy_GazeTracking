#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
PsychoPy GazeTracking Application Launcher

A simplified launcher script that runs the web interface with minimal dependencies.
"""

import os
import sys
import logging
import argparse
from pathlib import Path

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('app_launcher')

def check_dependencies():
    """Check if required dependencies are installed."""
    missing_deps = []
    
    try:
        import flask
        logger.info("Flask is installed")
    except ImportError:
        missing_deps.append("flask")
        logger.error("Flask is not installed")
    
    try:
        import flask_cors
        logger.info("Flask-CORS is installed")
    except ImportError:
        missing_deps.append("flask-cors")
        logger.error("Flask-CORS is not installed")
    
    try:
        import psychopy
        logger.info("PsychoPy is installed")
    except ImportError:
        missing_deps.append("psychopy")
        logger.error("PsychoPy is not installed")
    
    try:
        import numpy
        logger.info("NumPy is installed")
    except ImportError:
        missing_deps.append("numpy")
        logger.error("NumPy is not installed")
    
    try:
        import matplotlib
        logger.info("Matplotlib is installed")
    except ImportError:
        missing_deps.append("matplotlib")
        logger.error("Matplotlib is not installed")
    
    try:
        import cv2
        logger.info("OpenCV is installed")
    except ImportError:
        missing_deps.append("opencv-python")
        logger.error("OpenCV is not installed (webcam features will be limited)")
    
    return missing_deps

def install_dependencies(missing_deps):
    """Install missing dependencies."""
    if not missing_deps:
        return True
    
    logger.info(f"Installing missing dependencies: {', '.join(missing_deps)}")
    
    try:
        import subprocess
        subprocess.check_call([sys.executable, "-m", "pip", "install"] + missing_deps)
        logger.info("Dependencies installed successfully")
        return True
    except Exception as e:
        logger.error(f"Failed to install dependencies: {e}")
        return False

def main():
    """Main entry point for the application."""
    parser = argparse.ArgumentParser(description='PsychoPy GazeTracking Application')
    parser.add_argument('--install-deps', action='store_true', help='Install missing dependencies')
    parser.add_argument('--host', type=str, default='127.0.0.1', help='Host for web interface')
    parser.add_argument('--port', type=int, default=5000, help='Port for web interface')
    parser.add_argument('--no-browser', action='store_true', help='Do not open browser automatically')
    parser.add_argument('--tracker', type=str, default='simulated', help='Tracker type (webcam, tobii, mouse, simulated)')
    args = parser.parse_args()
    
    # Check dependencies
    missing_deps = check_dependencies()
    
    # Install dependencies if requested
    if missing_deps and args.install_deps:
        if not install_dependencies(missing_deps):
            logger.error("Failed to install dependencies. Please install them manually.")
            sys.exit(1)
    elif missing_deps:
        logger.warning("Some dependencies are missing. Run with --install-deps to install them.")
    
    # Import the application module
    try:
        from PsychoPyInterface.run_application import main as run_app
        
        # Run the application
        sys.argv = [sys.argv[0]]  # Reset argv to avoid conflicts
        
        # Add arguments
        if args.host:
            sys.argv.extend(['--host', args.host])
        if args.port:
            sys.argv.extend(['--port', str(args.port)])
        if args.no_browser:
            sys.argv.append('--no-browser')
        if args.tracker:
            sys.argv.extend(['--tracker', args.tracker])
        
        run_app()
    except ImportError as e:
        logger.error(f"Failed to import application module: {e}")
        logger.error("Make sure the PsychoPyInterface package is properly installed.")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Error running application: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main() 