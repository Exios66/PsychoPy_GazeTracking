#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Minimal PsychoPy GazeTracking Web Interface

A minimal web interface for the PsychoPy GazeTracking application that doesn't
depend on PsychoPy for the web server functionality.
"""

import os
import sys
import json
import logging
import argparse
import webbrowser
import threading
import traceback
from datetime import datetime
from pathlib import Path
import socket
import time

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('minimal_app')

# Try to import required dependencies
try:
    import flask
    from flask import Flask, render_template, request, jsonify, send_from_directory
    from flask_cors import CORS
    FLASK_AVAILABLE = True
except ImportError:
    logger.error("Flask not found. Web interface will not be available.")
    logger.error("Please install Flask: pip install flask flask-cors")
    FLASK_AVAILABLE = False
    sys.exit(1)

# Check for optional dependencies
try:
    import numpy as np
    import matplotlib.pyplot as plt
    from matplotlib.backends.backend_agg import FigureCanvasAgg as FigureCanvas
    import io
    import base64
    VISUALIZATION_AVAILABLE = True
except ImportError:
    logger.warning("Visualization libraries not found. Visualization features will be limited.")
    VISUALIZATION_AVAILABLE = False

try:
    import cv2
    OPENCV_AVAILABLE = True
except ImportError:
    logger.warning("OpenCV not found. Webcam-based tracking will not be available.")
    OPENCV_AVAILABLE = False

# Application configuration
DEFAULT_CONFIG = {
    "web_interface": {
        "host": "127.0.0.1",
        "port": 5000,
        "debug": False,
        "open_browser": True
    },
    "experiment": {
        "fullscreen": False,
        "screen_width": 1024,
        "screen_height": 768,
        "background_color": [128, 128, 128],
        "text_color": [255, 255, 255]
    },
    "eye_tracking": {
        "tracker_type": "simulated",  # Options: webcam, tobii, mouse, simulated
        "webcam_id": 0,
        "calibration_points": 9,
        "validation_threshold": 1.0
    },
    "data": {
        "save_directory": "data",
        "auto_save_interval": 60  # seconds
    }
}

class MinimalApp:
    """Minimal web application for PsychoPy GazeTracking."""
    
    def __init__(self, config=None):
        """
        Initialize the application.
        
        Parameters:
        -----------
        config : dict, optional
            Configuration dictionary. If None, default config will be used.
        """
        self.config = DEFAULT_CONFIG.copy()
        if config:
            self._update_config(config)
            
        # Set up logging
        self.log_dir = Path(self.config["data"]["save_directory"]) / "logs"
        os.makedirs(self.log_dir, exist_ok=True)
        
        # Initialize state variables
        self.session_id = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        # Initialize Flask app
        self.flask_app = None
        if FLASK_AVAILABLE:
            self._setup_flask_app()
    
    def _update_config(self, config):
        """
        Update configuration with user-provided values.
        
        Parameters:
        -----------
        config : dict
            Configuration dictionary to merge with defaults
        """
        for section, values in config.items():
            if section in self.config:
                if isinstance(self.config[section], dict) and isinstance(values, dict):
                    self.config[section].update(values)
                else:
                    self.config[section] = values
            else:
                self.config[section] = values
    
    def _setup_flask_app(self):
        """Set up Flask web application."""
        # Get the directory containing this script
        current_dir = Path(__file__).parent
        
        # Set up Flask app with template and static folders
        self.flask_app = Flask(__name__, 
                              static_folder=str(current_dir / "PsychoPyInterface" / "static"),
                              template_folder=str(current_dir / "PsychoPyInterface" / "templates"))
        CORS(self.flask_app)
        
        # Register routes
        @self.flask_app.route('/')
        def index():
            return render_template('index.html')
        
        @self.flask_app.route('/api/status')
        def status():
            return jsonify({
                'psychopy_available': self._check_psychopy(),
                'opencv_available': OPENCV_AVAILABLE,
                'visualization_available': VISUALIZATION_AVAILABLE,
                'local_modules_available': self._check_local_modules(),
                'tracker_initialized': False,
                'experiment_running': False,
                'session_id': self.session_id,
                'calibration_results': None,
                'validation_results': None
            })
        
        @self.flask_app.route('/api/config', methods=['GET', 'POST'])
        def config():
            if request.method == 'POST':
                try:
                    new_config = request.json
                    self._update_config(new_config)
                    return jsonify({'status': 'success', 'config': self.config})
                except Exception as e:
                    return jsonify({'status': 'error', 'message': str(e)}), 400
            else:
                return jsonify(self.config)
        
        @self.flask_app.route('/api/initialize', methods=['POST'])
        def initialize():
            return jsonify({
                'status': 'error', 
                'message': 'This is a minimal web interface. PsychoPy functionality is not available.'
            }), 400
        
        @self.flask_app.route('/api/calibrate', methods=['POST'])
        def calibrate():
            return jsonify({
                'status': 'error', 
                'message': 'This is a minimal web interface. PsychoPy functionality is not available.'
            }), 400
        
        @self.flask_app.route('/api/validate', methods=['POST'])
        def validate():
            return jsonify({
                'status': 'error', 
                'message': 'This is a minimal web interface. PsychoPy functionality is not available.'
            }), 400
        
        @self.flask_app.route('/api/experiment/start', methods=['POST'])
        def start_experiment():
            return jsonify({
                'status': 'error', 
                'message': 'This is a minimal web interface. PsychoPy functionality is not available.'
            }), 400
        
        @self.flask_app.route('/api/experiment/stop', methods=['POST'])
        def stop_experiment():
            return jsonify({
                'status': 'error', 
                'message': 'This is a minimal web interface. PsychoPy functionality is not available.'
            }), 400
        
        @self.flask_app.route('/api/gaze_data', methods=['GET'])
        def get_gaze_data():
            # Return simulated gaze data
            import random
            return jsonify({
                'status': 'success', 
                'data': {
                    'x': random.uniform(-1, 1),
                    'y': random.uniform(-1, 1),
                    'timestamp': time.time(),
                    'confidence': 0.95,
                    'valid': True,
                    'simulated': True
                }
            })
        
        @self.flask_app.route('/api/visualization/calibration', methods=['GET'])
        def get_calibration_visualization():
            if not VISUALIZATION_AVAILABLE:
                return jsonify({
                    'status': 'error', 
                    'message': 'Visualization not available'
                }), 400
                
            try:
                # Generate a simple visualization
                fig = plt.figure(figsize=(10, 8))
                
                # Plot some random points
                ax = fig.add_subplot(111)
                
                # Generate random target and gaze points
                import random
                target_points = [(random.uniform(-0.8, 0.8), random.uniform(-0.8, 0.8)) for _ in range(9)]
                gaze_points = [(x + random.uniform(-0.1, 0.1), y + random.uniform(-0.1, 0.1)) 
                              for x, y in target_points]
                
                # Extract x and y coordinates
                target_x = [p[0] for p in target_points]
                target_y = [p[1] for p in target_points]
                gaze_x = [p[0] for p in gaze_points]
                gaze_y = [p[1] for p in gaze_points]
                
                # Plot points
                ax.scatter(target_x, target_y, color='blue', label='Target', s=100)
                ax.scatter(gaze_x, gaze_y, color='red', alpha=0.7, label='Gaze', s=50)
                
                # Draw lines connecting corresponding points
                for i in range(len(target_x)):
                    ax.plot([target_x[i], gaze_x[i]], [target_y[i], gaze_y[i]], 'k-', alpha=0.3)
                
                ax.set_title('Simulated Calibration Results')
                ax.set_xlabel('X Coordinate')
                ax.set_ylabel('Y Coordinate')
                ax.legend()
                ax.grid(True, alpha=0.3)
                
                # Convert plot to image
                canvas = FigureCanvas(fig)
                img_io = io.BytesIO()
                canvas.print_png(img_io)
                img_io.seek(0)
                img_data = base64.b64encode(img_io.getvalue()).decode('utf-8')
                plt.close(fig)
                
                return jsonify({
                    'status': 'success', 
                    'image': f'data:image/png;base64,{img_data}',
                    'metrics': {
                        'average_error': 0.15,
                        'max_error': 0.25,
                        'quality': 'good'
                    }
                })
            except Exception as e:
                logger.error(f"Error generating visualization: {str(e)}")
                logger.error(traceback.format_exc())
                return jsonify({'status': 'error', 'message': str(e)}), 500
        
        @self.flask_app.route('/api/webcam_list', methods=['GET'])
        def get_webcam_list():
            if not OPENCV_AVAILABLE:
                return jsonify({'status': 'error', 'message': 'OpenCV not available'}), 400
                
            try:
                webcams = self._detect_webcams()
                return jsonify({'status': 'success', 'webcams': webcams})
            except Exception as e:
                return jsonify({'status': 'error', 'message': str(e)}), 500
    
    def _check_psychopy(self):
        """Check if PsychoPy is available."""
        try:
            import psychopy
            return True
        except ImportError:
            return False
    
    def _check_local_modules(self):
        """Check if local modules are available."""
        try:
            from PsychoPyInterface.Scripts.gaze_tracking import GazeTracker
            return True
        except ImportError:
            return False
    
    def _detect_webcams(self, max_cameras=10):
        """
        Detect available webcams.
        
        Parameters:
        -----------
        max_cameras : int
            Maximum number of cameras to check
            
        Returns:
        --------
        list
            List of dictionaries with webcam information
        """
        if not OPENCV_AVAILABLE:
            return []
            
        webcams = []
        
        for i in range(max_cameras):
            try:
                cap = cv2.VideoCapture(i)
                if cap.isOpened():
                    ret, frame = cap.read()
                    if ret:
                        width = cap.get(cv2.CAP_PROP_FRAME_WIDTH)
                        height = cap.get(cv2.CAP_PROP_FRAME_HEIGHT)
                        fps = cap.get(cv2.CAP_PROP_FPS)
                        
                        webcams.append({
                            'id': i,
                            'name': f'Camera {i}',
                            'resolution': f'{int(width)}x{int(height)}',
                            'fps': int(fps) if fps > 0 else 'Unknown'
                        })
                cap.release()
            except Exception as e:
                logger.debug(f"Error checking camera {i}: {e}")
        
        return webcams
    
    def run_web_interface(self):
        """Start the web interface."""
        if not FLASK_AVAILABLE or not self.flask_app:
            logger.error("Flask not available. Cannot start web interface.")
            return False
            
        try:
            host = self.config["web_interface"]["host"]
            port = self.config["web_interface"]["port"]
            debug = self.config["web_interface"]["debug"]
            open_browser = self.config["web_interface"]["open_browser"]
            
            # Check if port is available
            if not self._is_port_available(host, port):
                # Try to find an available port
                for p in range(port + 1, port + 100):
                    if self._is_port_available(host, p):
                        logger.warning(f"Port {port} is not available. Using port {p} instead.")
                        port = p
                        break
                else:
                    logger.error(f"Could not find an available port. Web interface will not start.")
                    return False
            
            # Open browser in a separate thread if requested
            if open_browser:
                threading.Timer(1.5, lambda: webbrowser.open(f"http://{host}:{port}")).start()
            
            # Start Flask app
            logger.info(f"Starting web interface at http://{host}:{port}")
            self.flask_app.run(host=host, port=port, debug=debug, use_reloader=False)
            
            return True
            
        except Exception as e:
            logger.error(f"Error starting web interface: {str(e)}")
            logger.error(traceback.format_exc())
            return False
    
    def _is_port_available(self, host, port):
        """Check if a port is available."""
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.bind((host, port))
            sock.close()
            return True
        except:
            return False

def load_config_file(config_path):
    """
    Load configuration from a JSON file.
    
    Parameters:
    -----------
    config_path : str
        Path to the configuration file
        
    Returns:
    --------
    dict
        Configuration dictionary or None if loading fails
    """
    try:
        with open(config_path, 'r') as f:
            return json.load(f)
    except Exception as e:
        logger.error(f"Error loading configuration file: {str(e)}")
        return None

def main():
    """Main entry point for the application."""
    # Parse command line arguments
    parser = argparse.ArgumentParser(description='Minimal PsychoPy GazeTracking Web Interface')
    parser.add_argument('--config', type=str, help='Path to configuration file')
    parser.add_argument('--host', type=str, help='Host for web interface')
    parser.add_argument('--port', type=int, help='Port for web interface')
    parser.add_argument('--no-browser', action='store_true', help='Do not open browser automatically')
    args = parser.parse_args()
    
    # Load configuration
    config = None
    if args.config:
        config = load_config_file(args.config)
    
    if config is None:
        config = DEFAULT_CONFIG.copy()
    
    # Override config with command line arguments
    if args.host:
        config["web_interface"]["host"] = args.host
    if args.port:
        config["web_interface"]["port"] = args.port
    if args.no_browser:
        config["web_interface"]["open_browser"] = False
    
    # Create and run application
    app = MinimalApp(config)
    
    try:
        # Run web interface
        app.run_web_interface()
    except KeyboardInterrupt:
        logger.info("Application terminated by user")

if __name__ == "__main__":
    main() 